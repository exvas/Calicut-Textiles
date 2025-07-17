import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta, time
from frappe.utils import today, get_first_day, get_last_day, add_days, getdate, nowdate
from datetime import datetime, timedelta, time
from collections import defaultdict
from frappe.utils.data import get_time



@frappe.whitelist()
def get_late_minutes_from_in_log(employee, date):
    """Fetch custom_late_coming_minutes from IN check-in on same date"""
    record = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]
        },
        fields=["custom_late_coming_minutes"],
        order_by="time ASC",
        limit=1
    )
    return record[0] if record else {}



@frappe.whitelist()
def get_first_and_last_checkins(employee, date):
    """Fetch first, last, and all check-ins of the day for an employee"""
    records = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]
        },
        fields=["name", "time", "custom_late_coming_minutes", "custom_early_going_minutes"],
        order_by="time ASC"
    )

    if not records:
        return {}

    return {
        "first": records[0],
        "last": records[-1] if len(records) > 1 else None,
        "all": records  # return full list for time comparison
    }


@frappe.whitelist()
def update_employee_checkin_fields(doc, method):
    """Calculate Late Entry and Early Going based on first and last check-ins of the day"""
    if not doc.employee or not doc.time:
        return

    # Fetch all check-ins for the day, sorted by time
    checkins = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "employee": doc.employee,
            "time": ["between", [doc.time.date().strftime('%Y-%m-%d') + " 00:00:00",
                                 doc.time.date().strftime('%Y-%m-%d') + " 23:59:59"]],
            "docstatus": ["<", 2]
        },
        fields=["name", "time", "custom_late_coming_minutes", "custom_early_going_minutes"],
        order_by="time ASC"
    )

    if not checkins:
        return

    current_time = doc.time
    first = checkins[0]
    last = checkins[-1]

    # Skip duplicate check-ins within 5 minutes of first or last
    if first["name"] != doc.name and abs((current_time - first["time"]).total_seconds()) <= 300:
        # Duplicate of IN
        return
    if last["name"] != doc.name and abs((current_time - last["time"]).total_seconds()) <= 300:
        # Duplicate of OUT
        return

    # Load default shift
    default_shift = frappe.db.get_value("Employee", doc.employee, "default_shift")
    if not default_shift:
        return

    shift = frappe.get_doc("Shift Type", default_shift)
    if not shift.start_time or not shift.end_time:
        return

    start_time = get_time(shift.start_time)
    end_time = get_time(shift.end_time)


    shift_start = datetime.combine(current_time.date(), start_time)
    shift_end = datetime.combine(current_time.date(), end_time)
    if shift_end <= shift_start:
        shift_end += timedelta(days=1)

    # Total shift hours
    total_hours = (shift_end - shift_start).seconds / 3600
    doc.custom_total_hours = round(total_hours, 2)

    # Determine if this is first or last check-in
    is_first = (first["name"] == doc.name)
    is_last = (last["name"] == doc.name)

    if is_first:
        # Late coming logic
        diff_minutes = int((current_time - shift_start).total_seconds() / 60)
        doc.custom_late_coming_minutes = diff_minutes if diff_minutes > 10 else 0

    if is_last:
        # Early going logic
        diff_minutes = int((shift_end - current_time).total_seconds() / 60)
        doc.custom_early_going_minutes = diff_minutes if diff_minutes > 20 else 0

        # Add total late+early
        late = first.get("custom_late_coming_minutes") or 0
        early = doc.custom_early_going_minutes or 0
        doc.custom_late_coming_minutes = late
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

    today_date = today()
    first_day = get_first_day(today_date)
    last_day = get_last_day(today_date)

    processing_last_day = getdate(today_date) if getdate(today_date) < last_day else last_day

    settings = frappe.get_single("Calicut Textiles Settings")
    threshold = settings.threshold_overtime_minutes or 0

    employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name", "company"])

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
                worked_minutes = (out_time - in_time).total_seconds() / 60

                shift_start_dt = datetime.combine(checkin_date, shift_start)
                shift_end_dt = datetime.combine(checkin_date, shift_end)
                if shift_end_dt <= shift_start_dt:
                    shift_end_dt += timedelta(days=1)

                shift_minutes = (shift_end_dt - shift_start_dt).total_seconds() / 60
                extra = worked_minutes - shift_minutes

                if extra > threshold:
                    overtime_today = extra - threshold
                    total_overtime_minutes += overtime_today

        if total_overtime_minutes > 0:
            base = frappe.get_value("Salary Structure Assignment", {"employee": emp.name}, "base")
            if not base:
                continue

            total_days = (datetime.strptime(str(last_day), "%Y-%m-%d") - datetime.strptime(str(first_day), "%Y-%m-%d")).days + 1
            per_minute_rate = base / (total_days * 8 * 60)
            overtime_amount = round(per_minute_rate * total_overtime_minutes, 2)

            additional_salary = frappe.new_doc("Additional Salary")
            additional_salary.employee = emp.name
            additional_salary.company = emp.company
            additional_salary.payroll_date = last_day
            additional_salary.amount = overtime_amount
            additional_salary.salary_component = "Over Time"
            additional_salary.overwrite_salary_structure_amount = 1
            additional_salary.submit()
