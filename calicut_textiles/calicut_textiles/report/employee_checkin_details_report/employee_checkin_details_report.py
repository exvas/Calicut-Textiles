# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, format_time
from collections import defaultdict

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
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 150},
        {"label": "Time", "fieldname": "time", "fieldtype": "Time", "width": 150},
        {"label": "Status", "fieldname": "log_type", "fieldtype": "Data", "width": 150},
        {"label": "Late", "fieldname": "late", "fieldtype": "Data", "width": 150},
        {"label": "Early", "fieldname": "early", "fieldtype": "Data", "width": 150}

    ]

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
            ec.custom_late_early
        FROM `tabEmployee Checkin` ec
        LEFT JOIN `tabEmployee` emp ON ec.employee = emp.name
        WHERE {where_clause}
        ORDER BY ec.employee, ec.time ASC
    """, filters, as_dict=True)

    # Group check-ins by employee and date
    grouped = defaultdict(list)
    for row in checkin_data:
        key = (row.employee, getdate(row.time))
        grouped[key].append(row)

    result = []
    for (employee, date), entries in grouped.items():
        for i, row in enumerate(entries):
            is_first = (i == 0)
            is_last = (i == len(entries) - 1)

            result.append({
                "employee": row.employee,
                "employee_name": row.employee_name,
                "company": row.company,
                "shift": row.default_shift,
                "date": date,
                "time": format_time(row.time),
                "log_type": row.log_type or "IN",
                "late": row.custom_late_coming_minutes if is_first else "",
                "early": row.custom_late_early if is_last else ""
            })

    return result
