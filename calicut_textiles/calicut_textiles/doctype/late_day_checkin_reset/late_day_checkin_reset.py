# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
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
