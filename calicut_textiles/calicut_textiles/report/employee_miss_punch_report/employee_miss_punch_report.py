# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from collections import defaultdict
from datetime import date

def execute(filters=None):
    if filters is None:
        filters = {}

    today_str = date.today().strftime("%Y-%m-%d")
    from_date = filters.get("from_date") or today_str
    to_date = filters.get("to_date") or today_str

    columns = get_columns()
    data = []

    checkins = frappe.get_all(
        "Employee Checkin",
        fields=["employee", "time", "log_type"],
        filters=[
            ["time", ">=", f"{from_date} 00:00:00"],
            ["time", "<=", f"{to_date} 23:59:59"]
        ],
        order_by="employee, time asc"
    )

    employee_cache = {}
    records = defaultdict(lambda: {
        "first_in": None,
        "last_out": None,
        "employee_name": None,
        "company": None,
        "shift": None
    })

    for checkin in checkins:
        emp = checkin.employee
        checkin_date = checkin.time.date()
        log_type = checkin.log_type.upper() if checkin.log_type else ""

        if emp not in employee_cache:
            emp_doc = frappe.get_doc("Employee", emp)
            employee_cache[emp] = {
                "employee_name": emp_doc.employee_name,
                "company": emp_doc.company,
                "shift": emp_doc.default_shift
            }

        rec = records[(emp, checkin_date)]
        rec["employee_name"] = employee_cache[emp]["employee_name"]
        rec["company"] = employee_cache[emp]["company"]
        rec["shift"] = employee_cache[emp]["shift"]

        if log_type == "IN":
            if rec["first_in"] is None or checkin.time < rec["first_in"]:
                rec["first_in"] = checkin.time
        elif log_type == "OUT":
            if rec["last_out"] is None or checkin.time > rec["last_out"]:
                rec["last_out"] = checkin.time

    for (emp, checkin_date), val in sorted(records.items()):
        first_in = val["first_in"]
        last_out = val["last_out"]

        status = "Present" if first_in and last_out else "Miss Punch"

        if first_in:
            data.append({
                "employee": emp,
                "employee_name": val["employee_name"],
                "company": val["company"],
                "shift": val["shift"],
                "date": checkin_date,
                "time": first_in.strftime("%H:%M:%S"),
                "log_type": "IN",
                "status": status
            })

        if last_out:
            data.append({
                "employee": emp,
                "employee_name": val["employee_name"],
                "company": val["company"],
                "shift": val["shift"],
                "date": checkin_date,
                "time": last_out.strftime("%H:%M:%S"),
                "log_type": "OUT",
                "status": status
            })

    final_data = []
    last_key = None

    for row in data:
        current_key = (row["employee"], row["date"])
        if current_key == last_key:
            row["employee"] = ""
            row["employee_name"] = ""
            row["company"] = ""
            row["shift"] = ""
            row["status"] = ""
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
        {"label": "Log Type", "fieldname": "log_type", "fieldtype": "Data", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 150},
    ]
