# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document

class LateDayCheckinReset(Document):
    def on_submit(self):
        """Method to Update the checkin time """
        for checkin in self.checkin_details:
            if checkin.reset_time and checkin.employee_checkin:
                frappe.db.set_value("Employee Checkin", checkin.employee_checkin, {
                    "time": checkin.reset_time,
                })
                frappe.msgprint(f"Check-in updated for {checkin.employee_name}")

@frappe.whitelist()
def get_first_checkins_by_date(from_date, to_date):
    """Get first employee checkin for each employee per day within the date range."""

    if not from_date or not to_date:
        return []

    data = frappe.db.sql("""
        SELECT
            ec.name,
            ec.employee,
            ec.employee_name,
            ec.log_type,
            ec.time
        FROM `tabEmployee Checkin` ec
        INNER JOIN (
            SELECT employee, DATE(time) as checkin_date, MIN(time) AS min_time
            FROM `tabEmployee Checkin`
            WHERE DATE(time) BETWEEN %s AND %s
            GROUP BY employee, checkin_date
        ) AS first_checkin
        ON ec.employee = first_checkin.employee
        AND DATE(ec.time) = first_checkin.checkin_date
        AND ec.time = first_checkin.min_time
        WHERE ec.docstatus < 2
        ORDER BY ec.time ASC
    """, (from_date, to_date), as_dict=True)

    return data
