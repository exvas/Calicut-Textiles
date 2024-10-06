# Copyright (c) 2024, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate



class EmployeePunchingData(Document):
	def validate(self):
		self.validate_employee()
		self.calculate_early()

	def on_submit(self):
		self.create_additional_salary_ot()
		self.create_additional_salary_early()


	def validate_employee(self):
		if self.employee_code:
			employee = frappe.db.get_value('Employee', {'attendance_device_id': self.employee_code}, 'name')
			if employee:
				self.employee = employee

	def calculate_early(self):
		early = self.late_coming_hours + self.early_going_hours
		self.late_early = early
		
	def create_additional_salary_ot(self):
		base_amount = frappe.db.get_value("Salary Structure Assignment", {"employee": self.employee}, "base", order_by="creation desc")

		if not base_amount:
			frappe.throw(f"No base amount found for employee {self.employee}")

		settings = frappe.get_doc("Calicut Textiles Settings")
		working_hour = frappe.db.get_value("HR Settings",None, "standard_working_hours")
		if working_hour:
			working_hour = float(working_hour)  
		else:
			frappe.throw("Unable to fetch standard working hours from HR Settings.")


		if self.ot_hours == 0:
			return

		if self.employee and self.ot_hours > 0:
			one_day = base_amount / 30
			one_hour = one_day / working_hour
			one_min = one_hour / 60
			ot_amount = self.ot_hours * one_min

			additional_salary = frappe.get_doc({
				"doctype": "Additional Salary",
				"employee": self.employee,
				"custom_is_overtime": 1,
				"salary_component": settings.ot_component,
				"custom_ot_min": self.ot_hours,
				"payroll_date": self.payroll_date,  
				"amount": ot_amount,
				"company": self.company,
				"overwrite_salary_structure_amount": 0  
			})

			additional_salary.save()
			additional_salary.submit()
		else:
			frappe.throw("No Employee or OT Hours found for this Punching Data")
	
	def create_additional_salary_early(self):
		base_amount = frappe.db.get_value("Salary Structure Assignment", {"employee": self.employee}, "base", order_by="creation desc")

		if not base_amount:
			frappe.throw(f"No base amount found for employee {self.employee}")
	
		settings = frappe.get_doc("Calicut Textiles Settings")
		working_hour = frappe.db.get_value("HR Settings",None, "standard_working_hours")
		if working_hour:
			working_hour = float(working_hour) 
		else:
			frappe.throw("Unable to fetch standard working hours from HR Settings.")

		if self.late_early == 0:
			return  

		if self.employee and self.late_early:
			one_day = base_amount/30
			one_hour =  one_day/working_hour
			one_min = one_hour/60
			early_amount = self.late_early * one_min

			
			additional_salary = frappe.get_doc({
				"doctype": "Additional Salary",
				"employee": self.employee,
				"custom_is_late_early":1,
				"salary_component": settings.early_component,
				"custom_late_early_min":self.late_early,
				"payroll_date": self.payroll_date,  
				"amount": early_amount,
				"company": self.company,
				"overwrite_salary_structure_amount": 0  
			})
			

			additional_salary.save()
			additional_salary.submit()
		else:
			frappe.throw("No Employee found for this Punching Data")

	
