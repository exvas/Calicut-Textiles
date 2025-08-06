import frappe
from frappe.utils import getdate, format_time
from collections import defaultdict
from datetime import datetime, timedelta, time


def str_to_minutes(time_str):
    if not time_str:
        return 0
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

def minutes_to_str(minutes):
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h:02}:{m:02}"


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    final_data = []

    last_key = None

    for row in data:
        # Keep totals row untouched
        if row.get("employee") == "Total":
            final_data.append(row)
            continue

        current_key = (row["employee"], row["date"])

        if current_key == last_key:
            row["employee"] = ""
            row["employee_name"] = ""
            row["company"] = ""
            row["shift"] = ""
            row["total_hours"] = ""
            row["date"] = ""
        else:
            last_key = current_key

        final_data.append(row)

    return columns, final_data


def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
        {"label": "Shift", "fieldname": "shift", "fieldtype": "Link", "options": "Shift Type", "width": 150},
        {"label": "Total Hours", "fieldname": "total_hours", "fieldtype": "Data", "width": 150},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 150},
        {"label": "Time", "fieldname": "time", "fieldtype": "Time", "width": 150},
        {"label": "Status", "fieldname": "log_type", "fieldtype": "Data", "width": 150},
        {"label": "Late", "fieldname": "late", "fieldtype": "Data", "width": 150},
        {"label": "Early", "fieldname": "early", "fieldtype": "Data", "width": 150},
        {"label": "Over Time", "fieldname": "over_time", "fieldtype": "Data", "width": 150},
        {"label": "Total Working Hours", "fieldname": "total_working_hours", "fieldtype": "Data", "width": 150},
        {"label": "Total Break Time", "fieldname": "total_break_time", "fieldtype": "Data", "width": 150}
    ]


def to_time(value):
    """Convert timedelta to time if needed."""
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hour=hours, minute=minutes, second=seconds)
    return value


def get_data(filters):
    conditions = []

    if filters.get("from_date"):
        filters["from_datetime"] = f"{filters['from_date']} 00:00:00"
        conditions.append("ec.time >= %(from_datetime)s")

    if filters.get("to_date"):
        filters["to_datetime"] = f"{filters['to_date']} 23:59:59"
        conditions.append("ec.time <= %(to_datetime)s")

    if filters.get("company"):
        conditions.append("emp.company = %(company)s")

    if filters.get("employee"):
        conditions.append("ec.employee = %(employee)s")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    checkin_data = frappe.db.sql(f"""
        SELECT
            ec.employee,
            emp.employee_name,
            emp.company,
            ec.time,
            ec.log_type,
            emp.default_shift,
            ec.custom_late_coming_minutes,
            ec.custom_early_going_minutes,
            ec.custom_late_early,
            ec.custom_total_hours
        FROM `tabEmployee Checkin` ec
        LEFT JOIN `tabEmployee` emp ON ec.employee = emp.name
        WHERE {where_clause}
        ORDER BY ec.employee, ec.time ASC
    """, filters, as_dict=True)

    grouped = defaultdict(list)
    for row in checkin_data:
        key = (row.employee, getdate(row.time))
        grouped[key].append(row)

    result = []

    settings = frappe.get_single("Calicut Textiles Settings")
    threshold = settings.threshold_overtime_minutes or 0

    # Totals accumulators
    total_late = 0
    total_early = 0
    total_overtime_minutes = 0
    total_working_minutes = 0
    total_break_minutes = 0

    for (employee, date), entries in grouped.items():
        checkin_times = [entry.time for entry in entries]
        checkin_times.sort()

        filtered_checkins = []
        last_time = None
        for current_time in checkin_times:
            if not last_time or (current_time - last_time).total_seconds() > 300:
                filtered_checkins.append(current_time)
                last_time = current_time

        if len(filtered_checkins) < 2:
            continue

        in_time = filtered_checkins[0]
        out_time = filtered_checkins[-1]

        shift_type_name = frappe.get_value("Employee", employee, "default_shift")
        if not shift_type_name:
            continue

        shift_type = frappe.get_doc("Shift Type", shift_type_name)
        shift_start = to_time(shift_type.start_time)
        shift_end = to_time(shift_type.end_time)

        shift_start_dt = datetime.combine(date, shift_start)
        shift_end_dt = datetime.combine(date, shift_end)
        if shift_end_dt <= shift_start_dt:
            shift_end_dt += timedelta(days=1)

        normal_end_dt = shift_end_dt + timedelta(minutes=threshold)
        normal_start_dt = shift_start_dt - timedelta(minutes=threshold)

        holiday_list = frappe.get_value("Employee", employee, "holiday_list") or ""

        if holiday_list == "CT Holidays" and date.weekday() == 6:
            total_overtime_minutes_day = (out_time - in_time).total_seconds() / 60
        else:

            # Morning Overtime
            if in_time < normal_start_dt:
                overtime_morning = threshold + (normal_start_dt - in_time).total_seconds() / 60
            else:
                overtime_morning = 0

            # Evening Overtime
            if out_time > normal_end_dt:
                overtime_evening = threshold + (out_time - normal_end_dt).total_seconds() / 60
            else:
                overtime_evening = 0

            total_overtime_minutes_day = overtime_morning + overtime_evening

        overtime = ""
        if total_overtime_minutes_day > 0:
            h = int(total_overtime_minutes_day // 60)
            m = int(total_overtime_minutes_day % 60)
            overtime = "{:02}:{:02}".format(h, m)

        # --- Calculate total break time and working hours as in original logic ---
        total_break_seconds = 0
        for idx, entry in enumerate(entries):
            log_type = (entry.log_type or '').upper()
            if log_type == "OUT" and idx + 1 < len(entries):
                next_entry = entries[idx + 1]
                next_log_type = (next_entry.log_type or '').upper()
                if next_log_type == "IN":
                    time_diff = next_entry.time - entry.time
                    total_break_seconds += time_diff.total_seconds()

        total_working_hours = ""
        if in_time and out_time and out_time > in_time:
            working_duration = out_time - in_time
            h, remainder = divmod(working_duration.total_seconds(), 3600)
            m, _ = divmod(remainder, 60)
            total_working_hours = "{:02}:{:02}".format(int(h), int(m))

        total_break_time = ""
        if total_break_seconds > 0:
            h, remainder = divmod(total_break_seconds, 3600)
            m, _ = divmod(remainder, 60)
            total_break_time = "{:02}:{:02}".format(int(h), int(m))

        for i, row in enumerate(entries):
            is_first = i == 0
            is_last = i == len(entries) - 1

            is_ct_sunday = holiday_list == "CT Holidays" and date.weekday() == 6

            late_val = row.custom_late_coming_minutes if is_first and not is_ct_sunday and row.custom_late_coming_minutes else 0
            early_val = row.custom_early_going_minutes if is_last and not is_ct_sunday and row.custom_early_going_minutes else 0

            # Accumulate totals
            total_late += late_val
            total_early += early_val
            if is_last:
                total_overtime_minutes += str_to_minutes(overtime) if overtime else 0
                total_working_minutes += str_to_minutes(total_working_hours) if total_working_hours else 0
                total_break_minutes += str_to_minutes(total_break_time) if total_break_time else 0

            result.append({
                "employee": row.employee,
                "employee_name": row.employee_name,
                "company": row.company,
                "shift": row.default_shift,
                "total_hours": row.custom_total_hours,
                "date": date,
                "time": format_time(row.time),
                "log_type": row.log_type or "IN",
                "late": row.custom_late_coming_minutes if is_first and not is_ct_sunday else "",
                "early": row.custom_early_going_minutes if is_last and not is_ct_sunday else "",
                "over_time": overtime if is_last else "",
                "total_working_hours": total_working_hours if is_last else "",
                "total_break_time": total_break_time if is_last else ""
            })

    # Append a total summary row at the end
    result.append({
        "employee": "",
        "employee_name": "",
        "company": "",
        "shift": "",
        "total_hours": "",
        "date": "",
        "time": "",
        "log_type": "<b>Total</b>",
        "late": f"<b>{total_late}</b>" if total_late else "",
        "early": f"<b>{total_early}</b>" if total_early else "",
        "over_time": f"<b>{minutes_to_str(total_overtime_minutes)}</b>" if total_overtime_minutes > 0 else "",
        "total_working_hours": f"<b>{minutes_to_str(total_working_minutes)}</b>" if total_working_minutes > 0 else "",
        "total_break_time": f"<b>{minutes_to_str(total_break_minutes)}</b>" if total_break_minutes > 0 else ""
    })

    return result
