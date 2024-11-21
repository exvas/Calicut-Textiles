# Copyright (c) 2024, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class BulkEmployeeAdvance(Document):
	pass



@frappe.whitelist()
def create_employee_advances(doc_name):
    bulk_advance = frappe.get_doc("Bulk Employee Advance", doc_name)

    if not bulk_advance.employee_details:
        frappe.throw("No employees listed in the Employee Details table.")

    created_advances = []
    created_payment_entries = []

    for row in bulk_advance.employee_details:
        employee_advance = frappe.new_doc("Employee Advance")
        employee_advance.employee = row.employee
        employee_advance.posting_date = bulk_advance.posting_date
        employee_advance.mode_of_payment = bulk_advance.mode_of_payment
        employee_advance.company = bulk_advance.company
        employee_advance.advance_amount = row.advance_amount
        employee_advance.purpose = bulk_advance.purpose
        employee_advance.repay_unclaimed_amount_from_salary = 1
        employee_advance.currency = bulk_advance.currency
        employee_advance.exchange_rate = bulk_advance.exchange_rate

        employee_advance.insert(ignore_permissions=True)
        employee_advance.submit()
        created_advances.append(employee_advance.name)

        paid_to = frappe.get_doc("Mode of Payment", bulk_advance.mode_of_payment)
        paid_to_account = paid_to.accounts[0].default_account if paid_to.accounts else None
        if not paid_to_account:
            frappe.throw("No default account set for the selected mode of payment.")
        
        payment_entry = frappe.new_doc("Payment Entry")
        payment_entry.payment_type = 'Pay'
        payment_entry.posting_date = bulk_advance.posting_date
        payment_entry.mode_of_payment = bulk_advance.mode_of_payment
        payment_entry.party_type = 'Employee'
        payment_entry.party = row.employee
        payment_entry.paid_amount = row.advance_amount
        payment_entry.received_amount = row.advance_amount
        payment_entry.paid_to = paid_to_account
        payment_entry.paid_from = paid_to_account
        payment_entry.target_exchange_rate = 1
        payment_entry.source_exchange_rate = 1
        payment_entry.append("references", {
            "reference_doctype": "Employee Advance",
            "reference_name": employee_advance.name,
            "allocated_amount": row.advance_amount
        })

        payment_entry.insert(ignore_permissions=True)
        payment_entry.submit()
        created_payment_entries.append(payment_entry.name)

    return {
        "created_advances": created_advances,
        "created_payment_entries": created_payment_entries,
    }
