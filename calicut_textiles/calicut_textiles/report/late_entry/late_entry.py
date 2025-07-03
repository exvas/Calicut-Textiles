# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Late", "fieldname": "late", "fieldtype": "Int", "width": 120},
        {"label": "Early", "fieldname": "early", "fieldtype": "Int", "width": 120},
        {"label": "Late Early", "fieldname": "late_early", "fieldtype": "Int", "width": 130},
        {"label": "Shift Type", "fieldname": "shift_type", "fieldtype": "Data", "width": 120},
        {"label": "Shift Hours", "fieldname": "total_hours", "fieldtype": "Float", "width": 150},
        {"label": "Total Hours Cutting", "fieldname": "late_early", "fieldtype": "Float", "width": 150},
        {"label": "Total Amount Cutting", "fieldname": "deduction", "fieldtype": "Currency", "width": 150},
        {"label": "Salary (CTC)", "fieldname": "ctc", "fieldtype": "Currency", "width": 120},
        {"label": "Minute Salary", "fieldname": "minute_salary", "fieldtype": "Currency", "width": 140},
    ]

def get_data(filters):
    company = filters.get("company")

    checkins = frappe.db.sql("""
        SELECT
            ec.employee_name,
            ec.custom_late_coming_minutes as late,
            ec.custom_early_going_minutes as early,
            ec.custom_late_early as late_early,
            ec.shift as shift_type,
            ec.custom_total_hours as total_hours,
            e.ctc,
            ROUND((((e.ctc / 30) / NULLIF(ec.custom_total_hours, 0)) / 60), 2) as minute_salary,
            ROUND(((((e.ctc / 30) / NULLIF(ec.custom_total_hours, 0)) / 60) * IFNULL(ec.custom_late_early, 0)), 2) as deduction
        FROM
            `tabEmployee Checkin` ec
        LEFT JOIN `tabEmployee` e ON e.name = ec.employee
        WHERE
            ec.log_type = 'OUT'
            AND e.company = %s
        ORDER BY
            ec.employee_name ASC
    """, (company,), as_dict=True)

    return checkins


