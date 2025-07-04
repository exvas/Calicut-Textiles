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
	from frappe.utils import getdate, nowdate

	company = filters.get("company")
	target_date = filters.get("date") or nowdate()

	# Step 1: Try to fetch OUT check-ins first
	out_checkins = frappe.db.sql("""
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
			e.company = %s
			AND ec.log_type = 'OUT'
			AND DATE(ec.time) = %s
	""", (company, target_date), as_dict=True)

	# Get list of employees who already have OUT entries
	employees_with_out = [row["employee_name"] for row in out_checkins]

	# Step 2: Get IN check-ins only for employees without OUT
	if employees_with_out:
		in_checkins = frappe.db.sql("""
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
				e.company = %s
				AND ec.log_type = 'IN'
				AND DATE(ec.time) = %s
				AND ec.employee_name NOT IN %s
		""", (company, target_date, tuple(employees_with_out)), as_dict=True)
	else:
		in_checkins = frappe.db.sql("""
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
				e.company = %s
				AND ec.log_type = 'IN'
				AND DATE(ec.time) = %s
		""", (company, target_date), as_dict=True)

	return out_checkins + in_checkins



