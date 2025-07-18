# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate



class AttendanceMarkingTool(Document):
	def on_submit(self):
		self.create_attendence_for_employee()

	def create_attendence_for_employee(self):
		"""Method to Create Attendance"""
		if not self.employee_details:
			frappe.throw("No employee details found.")

		for employee in self.employee_details:
			if not frappe.db.exists("Attendance", {"employee": employee.employee,"attendance_date": self.date}):
				employee_doc = frappe.get_doc("Employee", employee.employee)

				if employee.status and employee.shift:

					attendance = frappe.new_doc("Attendance")
					attendance.employee = employee.employee
					attendance.employee_name = employee.employee_name
					attendance.status = employee.status
					attendance.attendance_date = self.date
					attendance.company = employee_doc.company
					attendance.department = employee_doc.department
					attendance.shift = employee.shift or self.shift
					attendance.insert()
					attendance.submit()
