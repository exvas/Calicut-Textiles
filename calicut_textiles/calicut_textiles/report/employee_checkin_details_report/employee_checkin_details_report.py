# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, format_time
from collections import defaultdict
from datetime import datetime, timedelta, time


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    final_data = []

    last_key = None

    for row in data:
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

    for (employee, date), entries in grouped.items():
        first_in_time = None
        last_out_time = None
        total_break_seconds = 0
        shift_type_name = frappe.get_value("Employee", employee, "default_shift")
        if shift_type_name:
            shift_type = frappe.get_doc("Shift Type", shift_type_name)
            shift_start = to_time(shift_type.start_time)
            shift_end = to_time(shift_type.end_time)

        for idx, entry in enumerate(entries):
            log_type = (entry.log_type or '').upper()

            if not first_in_time and log_type == "IN":
                first_in_time = entry.time
            if log_type == "OUT":
                last_out_time = entry.time

            if log_type == "OUT" and idx + 1 < len(entries):
                next_entry = entries[idx + 1]
                next_log_type = (next_entry.log_type or '').upper()
                if next_log_type == "IN":
                    time_diff = next_entry.time - entry.time
                    total_break_seconds += time_diff.total_seconds()

        total_working_hours = ""
        if first_in_time and last_out_time and last_out_time > first_in_time:
            working_duration = last_out_time - first_in_time
            h, remainder = divmod(working_duration.total_seconds(), 3600)
            m, _ = divmod(remainder, 60)
            total_working_hours = "{:02}:{:02}".format(int(h), int(m))

        total_break_time = ""
        if total_break_seconds > 0:
            h, remainder = divmod(total_break_seconds, 3600)
            m, _ = divmod(remainder, 60)
            total_break_time = "{:02}:{:02}".format(int(h), int(m))

        overtime = ""
        if last_out_time and shift_end:

            shift_end_datetime = datetime.combine(date, shift_end)

            if shift_end < datetime.combine(date, datetime.min.time()).time():
                shift_end_datetime += timedelta(days=1)

            if last_out_time > shift_end_datetime:
                overtime_duration = last_out_time - shift_end_datetime
                overtime_seconds = overtime_duration.total_seconds()

                if overtime_seconds > 0:
                    h, remainder = divmod(overtime_seconds, 3600)
                    m, _ = divmod(remainder, 60)
                    overtime = "{:02}:{:02}".format(int(h), int(m))

        for i, row in enumerate(entries):
            is_first = i == 0
            is_last = i == len(entries) - 1

            result.append({
                "employee": row.employee,
                "employee_name": row.employee_name,
                "company": row.company,
                "shift": row.default_shift,
                "total_hours": row.custom_total_hours,
                "date": date,
                "time": format_time(row.time),
                "log_type": row.log_type or "IN",
                "late": row.custom_late_coming_minutes if is_first else "",
                "early": row.custom_early_going_minutes if is_last else "",
                "over_time": overtime if is_last else "",
                "total_working_hours": total_working_hours if is_last else "",
                "total_break_time": total_break_time if is_last else ""
            })

    return result
