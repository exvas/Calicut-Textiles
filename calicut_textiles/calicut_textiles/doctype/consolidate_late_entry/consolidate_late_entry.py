# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime


class ConsolidateLateEntry(Document):
	pass


@frappe.whitelist()
def get_employee_late_entries(from_date, to_date):
    from_dt_str = from_date + " 00:00:00"
    to_dt_str = to_date + " 23:59:59"

    # Query to get last OUT checkin per employee per day with all details
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

    # Query to sum custom_late_early per employee for the date range
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

    # Map employee to total late early sum
    late_early_map = {d["employee"]: d["total_late_early"] or 0 for d in late_early_sums}

    results = []

    if last_out_checkins:
        for checkin in last_out_checkins:
            emp_id = checkin["employee"]

            salary_structures = frappe.db.get_all(
                "Salary Structure Assignment",
                filters={"employee": emp_id},
                fields=["employee", "base"]
            )
            if salary_structures:
                basic_salary = salary_structures[0].base or 0
            else:
                basic_salary = 0

            basic_salary_per_day = basic_salary / 30 if basic_salary else 0
            total_work_hours = checkin.get("custom_total_hours") or 0

            if total_work_hours > 0:
                per_minute_rate = round(basic_salary_per_day / (total_work_hours * 60), 4)
            else:
                per_minute_rate = 0

            # Sum of late early for this employee across the date range
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
