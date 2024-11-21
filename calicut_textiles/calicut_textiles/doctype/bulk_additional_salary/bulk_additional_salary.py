# Copyright (c) 2024, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BulkAdditionalSalary(Document):
	pass


@frappe.whitelist()
def create_additional_salary(doc_name):
    advance = frappe.get_doc("Bulk Additional Salary", doc_name)

    if not advance.employee_advance_details:
        frappe.throw("No employee advances listed for this posting date.")

    created_advances = []
  
    for row in advance.employee_advance_details:
        employee_advance = frappe.new_doc("Additional Salary")
        employee_advance.employee = row.employee
        employee_advance.payroll_date = advance.payroll_date
        employee_advance.salary_component = advance.salary_component
        employee_advance.company = advance.company
        employee_advance.amount = row.advance_amount
        employee_advance.ref_doctype = "Employee Advance"
        employee_advance.ref_docname = row.employee_advance

        employee_advance.insert()
        employee_advance.submit()
        created_advances.append(employee_advance.name)
    return created_advances