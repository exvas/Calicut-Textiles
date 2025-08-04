import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta, time
from frappe.utils import today, get_first_day, get_last_day, add_days, getdate, nowdate
from datetime import datetime, timedelta, time
from collections import defaultdict
import math
from frappe.utils import get_datetime



@frappe.whitelist()
def get_late_minutes_from_in_log(employee, date):
    """Fetch custom_late_coming_minutes from IN check-in on same date"""
    record = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "log_type": "IN",
            "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]
        },
        fields=["custom_late_coming_minutes"],
        order_by="time ASC",
        limit=1
    )
    return record[0] if record else {}


def as_time(timedelta_obj):
    # Convert timedelta to datetime.time object
    total_seconds = int(timedelta_obj.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return datetime.time(hour=hours, minute=minutes, second=seconds)

@frappe.whitelist()
def update_employee_checkin_fields(doc, method):
    """Auto alternate IN/OUT and calculate late/early metrics"""

    if not doc.employee or not doc.time:
        return

    time_obj = doc.time if isinstance(doc.time, datetime) else get_datetime(doc.time)

    same_day_logs = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "employee": doc.employee,
            "time": ["between", [
                time_obj.date().strftime('%Y-%m-%d') + " 00:00:00",
                time_obj.date().strftime('%Y-%m-%d') + " 23:59:59"
            ]],
            "docstatus": ["<", 2]
        },
        fields=["name", "time", "log_type"],
        order_by="time asc"
    )

    if same_day_logs:
        last_log = same_day_logs[-1]
        last_log_time = get_datetime(last_log["time"])
        time_diff_min = abs((time_obj - last_log_time).total_seconds()) / 60
        if time_diff_min < 5:
            doc.log_type = "IN"
        else:
            doc.log_type = "OUT" if last_log["log_type"] == "IN" else "IN"
    else:
        doc.log_type = "IN"

    default_shift = frappe.db.get_value("Employee", doc.employee, "default_shift")
    if not default_shift:
        return

    shift = frappe.get_doc("Shift Type", default_shift)
    if not shift.start_time or not shift.end_time:
        return

    start_time = as_time(shift.start_time)
    end_time = as_time(shift.end_time)

    shift_start = datetime.combine(time_obj.date(), start_time)
    shift_end = datetime.combine(time_obj.date(), end_time)

    if shift_end <= shift_start:
        shift_end += timedelta(days=1)

    total_seconds = (shift_end - shift_start).total_seconds()
    total_hours = total_seconds / 3600
    doc.custom_total_hours = round(total_hours, 2)

    grace_late = 10
    grace_early = 10

    if doc.log_type == 'IN':
        grace_limit = shift_start + timedelta(minutes=grace_late)
        if time_obj > grace_limit:
            diff_seconds = (time_obj - shift_start).total_seconds()
            diff_minutes = int(diff_seconds // 60)
            doc.custom_late_coming_minutes = diff_minutes
        else:
            doc.custom_late_coming_minutes = 0
        doc.custom_early_going_minutes = 0

    elif doc.log_type == 'OUT':
        grace_limit = shift_end - timedelta(minutes=grace_early)
        if time_obj < grace_limit:
            diff_seconds = (shift_end - time_obj).total_seconds()
            diff_minutes = math.ceil(diff_seconds / 60)
            doc.custom_early_going_minutes = diff_minutes
        else:
            doc.custom_early_going_minutes = 0

        in_checkin_late_coming = frappe.db.get_value(
            "Employee Checkin",
            {
                "employee": doc.employee,
                "log_type": "IN",
                "time": ["between", [
                    time_obj.date().strftime('%Y-%m-%d') + " 00:00:00",
                    time_obj.date().strftime('%Y-%m-%d') + " 23:59:59"
                ]],
                "docstatus": ["<", 2]
            },
            "custom_late_coming_minutes"
        ) or 0

        doc.custom_late_coming_minutes = in_checkin_late_coming or 0

    late = doc.custom_late_coming_minutes or 0
    early = doc.custom_early_going_minutes or 0
    doc.custom_late_early = float(late) + float(early)


def as_time(value):
    """Convert timedelta or string to datetime.time."""
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hour=hours, minute=minutes, second=seconds)
    elif isinstance(value, time):
        return value
    else:
        return datetime.strptime(value, "%H:%M:%S").time()


def to_time(value):
    """Convert timedelta to time if needed."""
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hour=hours, minute=minutes, second=seconds)
    return value


@frappe.whitelist()
def process_monthly_overtime_additional_salary():
    """Creates Additional Salary for Overtime only once per month per employee."""
    settings = frappe.get_single("Calicut Textiles Settings")
    if settings.ot_salary:
        today_date = today()
        first_day = get_first_day(today_date)
        last_day = get_last_day(today_date)

        processing_last_day = getdate(today_date) if getdate(today_date) < last_day else last_day

        settings = frappe.get_single("Calicut Textiles Settings")
        threshold = settings.threshold_overtime_minutes or 0

        employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name", "company", "holiday_list"])

        for emp in employees:
            if frappe.db.exists("Additional Salary", {
                "employee": emp.name,
                "salary_component": "Over Time",
                "payroll_date": last_day
            }):
                continue

            total_overtime_minutes = 0

            shift_type_name = frappe.get_value("Employee", emp.name, "default_shift")
            if not shift_type_name:
                continue

            shift_type = frappe.get_doc("Shift Type", shift_type_name)
            shift_start = to_time(shift_type.start_time)
            shift_end = to_time(shift_type.end_time)

            # Compute total working hours per day
            dummy_date = datetime.today().date()
            shift_start_dt = datetime.combine(dummy_date, shift_start)
            shift_end_dt = datetime.combine(dummy_date, shift_end)
            if shift_end_dt <= shift_start_dt:
                shift_end_dt += timedelta(days=1)

            total_working_hours = (shift_end_dt - shift_start_dt).total_seconds() / 3600

            # Handle edge case if shift is wrongly configured
            if total_working_hours <= 0:
                continue


            checkins = frappe.get_all("Employee Checkin", filters={
                "employee": emp.name,
                "time": ["between", [f"{first_day} 00:00:00", f"{processing_last_day} 23:59:59"]]
            }, order_by="time asc", fields=["time"])

            checkins_by_day = defaultdict(list)
            for row in checkins:
                checkins_by_day[row.time.date()].append(row.time)

            for checkin_date, times in checkins_by_day.items():
                filtered_checkins = []
                last_time = None
                for current_time in times:
                    if not last_time or (current_time - last_time).total_seconds() > 300:
                        filtered_checkins.append(current_time)
                        last_time = current_time

                if len(filtered_checkins) >= 2:
                    in_time = filtered_checkins[0]
                    out_time = filtered_checkins[-1]

                    shift_start_dt = datetime.combine(checkin_date, shift_start)
                    shift_end_dt = datetime.combine(checkin_date, shift_end)
                    if shift_end_dt <= shift_start_dt:
                        shift_end_dt += timedelta(days=1)

                    if emp.holiday_list == "CT Holidays" and checkin_date.weekday() == 6:
                        overtime_minutes = (out_time - in_time).total_seconds() / 60
                        total_overtime_minutes += overtime_minutes
                        continue

                    normal_end_dt = shift_end_dt + timedelta(minutes=threshold)

                    if out_time <= normal_end_dt:
                        overtime_evening = 0
                    else:
                        overtime_evening = threshold + (out_time - normal_end_dt).total_seconds() / 60

                    normal_start_dt = shift_start_dt - timedelta(minutes=threshold)

                    if in_time >= normal_start_dt:
                        overtime_morning = 0
                    else:
                        overtime_morning = threshold + (normal_start_dt - in_time).total_seconds() / 60

                    total_overtime_minutes += overtime_morning + overtime_evening

            if total_overtime_minutes > 0:
                base = frappe.get_value("Salary Structure Assignment", {"employee": emp.name}, "base")
                if not base:
                    continue

                total_days = (datetime.strptime(str(last_day), "%Y-%m-%d") - datetime.strptime(str(first_day), "%Y-%m-%d")).days + 1
                per_minute_rate = base / (total_days * total_working_hours * 60)
                overtime_amount = round(per_minute_rate * total_overtime_minutes, 2)

                existing_additional_salary = frappe.get_all("Additional Salary", filters={
                    "employee": emp.name,
                    "salary_component": "Over Time",
                    "payroll_date": last_day
                }, limit=1)

                if existing_additional_salary:
                    additional_salary = frappe.get_doc("Additional Salary", existing_additional_salary[0].name)
                    additional_salary.amount += overtime_amount
                    additional_salary.save()
                else:
                    additional_salary = frappe.new_doc("Additional Salary")
                    additional_salary.employee = emp.name
                    additional_salary.company = emp.company
                    additional_salary.payroll_date = last_day
                    additional_salary.amount = overtime_amount
                    additional_salary.salary_component = "Over Time"
                    additional_salary.overwrite_salary_structure_amount = 1
                    additional_salary.submit()


@frappe.whitelist()
def create_overtime_additional_salary(payroll_date):
    """Creates Additional Salary for Overtime only once per month per employee."""
    encashment_date = getdate(payroll_date)
    first_day = get_first_day(encashment_date)
    last_day = get_last_day(encashment_date)
    processing_last_day = last_day
    current_date = encashment_date


    settings = frappe.get_single("Calicut Textiles Settings")
    threshold = settings.threshold_overtime_minutes or 0

    employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name", "company", "holiday_list"])

    for emp in employees:
        if frappe.db.exists("Additional Salary", {
            "employee": emp.name,
            "salary_component": "Over Time",
            "payroll_date": last_day
        }):
            continue

        total_overtime_minutes = 0

        shift_type_name = frappe.get_value("Employee", emp.name, "default_shift")
        if not shift_type_name:
            continue

        shift_type = frappe.get_doc("Shift Type", shift_type_name)
        shift_start = to_time(shift_type.start_time)
        shift_end = to_time(shift_type.end_time)

        # Compute total working hours per day
        dummy_date = datetime.today().date()
        shift_start_dt = datetime.combine(dummy_date, shift_start)
        shift_end_dt = datetime.combine(dummy_date, shift_end)
        if shift_end_dt <= shift_start_dt:
            shift_end_dt += timedelta(days=1)

        total_working_hours = (shift_end_dt - shift_start_dt).total_seconds() / 3600

        # Handle edge case if shift is wrongly configured
        if total_working_hours <= 0:
            continue


        checkins = frappe.get_all("Employee Checkin", filters={
            "employee": emp.name,
            "time": ["between", [f"{first_day} 00:00:00", f"{processing_last_day} 23:59:59"]]
        }, order_by="time asc", fields=["time"])

        checkins_by_day = defaultdict(list)
        for row in checkins:
            checkins_by_day[row.time.date()].append(row.time)

        for checkin_date, times in checkins_by_day.items():
            filtered_checkins = []
            last_time = None
            for current_time in times:
                if not last_time or (current_time - last_time).total_seconds() > 300:
                    filtered_checkins.append(current_time)
                    last_time = current_time

            if len(filtered_checkins) >= 2:
                in_time = filtered_checkins[0]
                out_time = filtered_checkins[-1]

                shift_start_dt = datetime.combine(checkin_date, shift_start)
                shift_end_dt = datetime.combine(checkin_date, shift_end)
                if shift_end_dt <= shift_start_dt:
                    shift_end_dt += timedelta(days=1)

                if emp.holiday_list == "CT Holidays" and checkin_date.weekday() == 6:
                    overtime_minutes = (out_time - in_time).total_seconds() / 60
                    total_overtime_minutes += overtime_minutes
                    continue

                normal_end_dt = shift_end_dt + timedelta(minutes=threshold)

                if out_time <= normal_end_dt:
                    overtime_evening = 0
                else:
                    overtime_evening = threshold + (out_time - normal_end_dt).total_seconds() / 60

                normal_start_dt = shift_start_dt - timedelta(minutes=threshold)

                if in_time >= normal_start_dt:
                    overtime_morning = 0
                else:
                    overtime_morning = threshold + (normal_start_dt - in_time).total_seconds() / 60

                total_overtime_minutes += overtime_morning + overtime_evening

        if total_overtime_minutes > 0:
            base = frappe.get_value("Salary Structure Assignment", {"employee": emp.name}, "base")
            if not base:
                continue

            total_days = (datetime.strptime(str(last_day), "%Y-%m-%d") - datetime.strptime(str(first_day), "%Y-%m-%d")).days + 1
            per_minute_rate = base / (total_days * total_working_hours * 60)
            overtime_amount = round(per_minute_rate * total_overtime_minutes, 2)

            existing_additional_salary = frappe.get_all("Additional Salary", filters={
                "employee": emp.name,
                "salary_component": "Over Time",
                "payroll_date": last_day
            }, limit=1)

            if existing_additional_salary:
                additional_salary = frappe.get_doc("Additional Salary", existing_additional_salary[0].name)
                additional_salary.amount += overtime_amount
                additional_salary.save()
            else:
                additional_salary = frappe.new_doc("Additional Salary")
                additional_salary.employee = emp.name
                additional_salary.company = emp.company
                additional_salary.payroll_date = current_date
                additional_salary.amount = overtime_amount
                additional_salary.salary_component = "Over Time"
                additional_salary.overwrite_salary_structure_amount = 1
                additional_salary.submit()


def timedelta_to_time(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return time(hours, minutes, seconds)
