# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ConsolidateLateEntry(Document):
	pass

@frappe.whitelist()
def get_employee_late_entries(from_date, to_date):
    results = frappe.db.sql("""
        SELECT
            ec.employee as employee,
            ec.employee_name,
            ec.shift as shift_type,
            ec.custom_total_hours as total_hours,
            e.ctc as salary,
            ROUND((((e.ctc / 30) / NULLIF(ec.custom_total_hours, 0)) / 60), 2) as min_salary,
			ec.custom_late_early as consolidat_hour_cutting,
			(ROUND((((e.ctc / 30) / NULLIF(ec.custom_total_hours, 0)) / 60), 2) * ec.custom_late_early) as consolidate_amt_cutting
        FROM
            `tabEmployee Checkin` ec
        LEFT JOIN `tabEmployee` e ON e.name = ec.employee
        WHERE
            ec.log_type = 'OUT'
            AND ec.time BETWEEN %s AND %s
        GROUP BY ec.employee
    """, (from_date, to_date), as_dict=True)

    return results
# 