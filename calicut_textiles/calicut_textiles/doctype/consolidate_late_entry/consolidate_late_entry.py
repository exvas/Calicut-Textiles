# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from datetime import datetime


class ConsolidateLateEntry(Document):
	pass


@frappe.whitelist()
def get_employee_late_entries(from_date, to_date):
    from_dt_str = from_date + " 00:00:00"
    to_dt_str = to_date + " 23:59:59"

    # Query to get last OUT checkin per employee per day
    last_out_query = """
    SELECT
        ec.name,
        ec.employee,
        ec.employee_name,
        ec.log_type,
        ec.shift,
        ec.custom_total_hours,
        ec.time
    FROM
        `tabEmployee Checkin` ec
    INNER JOIN (
        SELECT
            employee,
            DATE(time) as checkin_date,
            MAX(time) as last_out_time
        FROM
            `tabEmployee Checkin`
        WHERE
            log_type = 'OUT'
            AND time BETWEEN %(from_dt)s AND %(to_dt)s
        GROUP BY
            employee, checkin_date
    ) AS last_out ON ec.employee = last_out.employee
        AND DATE(ec.time) = last_out.checkin_date
        AND ec.time = last_out.last_out_time
    WHERE ec.log_type = 'OUT'
    """

    last_out_checkins = frappe.db.sql(last_out_query, {"from_dt": from_dt_str, "to_dt": to_dt_str}, as_dict=True)

    # Sum of custom_late_early for full date range
    late_early_sum_query = """
    SELECT
        employee,
        SUM(custom_late_early) as total_late_early
    FROM
        `tabEmployee Checkin`
    WHERE
        log_type = 'OUT'
        AND time BETWEEN %(from_dt)s AND %(to_dt)s
    GROUP BY employee
    """
    late_early_sums = frappe.db.sql(late_early_sum_query, {"from_dt": from_dt_str, "to_dt": to_dt_str}, as_dict=True)
    late_early_map = {d["employee"]: d["total_late_early"] or 0 for d in late_early_sums}

    #  Keep only the latest OUT checkin for each employee
    latest_checkin_map = {}
    for checkin in last_out_checkins:
        emp_id = checkin["employee"]
        if (emp_id not in latest_checkin_map) or (checkin["time"] > latest_checkin_map[emp_id]["time"]):
            latest_checkin_map[emp_id] = checkin

    results = []
    for emp_id, checkin in latest_checkin_map.items():
        salary_structures = frappe.db.get_all(
            "Salary Structure Assignment",
            filters={"employee": emp_id},
            fields=["employee", "base"]
        )
        basic_salary = salary_structures[0].base if salary_structures else 0
        basic_salary_per_day = basic_salary / 30 if basic_salary else 0
        total_work_hours = checkin.get("custom_total_hours") or 0

        if total_work_hours > 0:
            per_minute_rate = round(basic_salary_per_day / (total_work_hours * 60), 4)
        else:
            per_minute_rate = 0

        consolidate_hour_cutting = late_early_map.get(emp_id, 0)
        consolidate_amt_cutting = round(per_minute_rate * consolidate_hour_cutting, 2)

        results.append({
            "employee": checkin["employee"],
            "employee_name": checkin["employee_name"],
            "shift_type": checkin["shift"],
            "total_working_hours": total_work_hours,
            "basic_salary": basic_salary,
            "min_salary": per_minute_rate,
            "consolidat_hour_cutting": consolidate_hour_cutting,
            "consolidate_amt_cutting": consolidate_amt_cutting
        })

    return results



@frappe.whitelist()
def create_late_early_additional_salary(doc):
    if isinstance(doc, str):
        doc = frappe.get_doc("Consolidate Late Entry", doc)

    if doc.additional_salary_created:
        frappe.throw("Additional Salary Already Created")

    for late_entry in doc.late_entry_details:
        relieving_date = frappe.db.get_value("Employee", late_entry.employee, "relieving_date")

        if relieving_date and relieving_date < doc.payroll_date:
            frappe.throw(
                "Payroll Date {0} is after the Relieving Date {1} for Employee {2}".format(
                    doc.payroll_date, relieving_date, late_entry.employee
                )
            )

        additional_salary = frappe.new_doc("Additional Salary")
        additional_salary.employee = late_entry.employee
        additional_salary.employee_name = late_entry.employee_name
        additional_salary.payroll_date = doc.payroll_date
        additional_salary.salary_component = doc.componenet
        additional_salary.amount = late_entry.consolidate_amt_cutting
        additional_salary.custom_late_early_min = late_entry.consolidat_hour_cutting
        additional_salary.custom_consolidated_late_entry = doc.name
        additional_salary.overwrite_salary_structure_amount = True
        additional_salary.custom_is_late_early = True
        additional_salary.submit()

    doc.additional_salary_created = True
    doc.save()
