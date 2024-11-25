# Copyright (c) 2024, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
from frappe import _


class BulkEmployeeAdvance(Document):
    def on_cancel(self):
        self.update_advance()
        self.update_additional()

    def validate(self):
        bank_account = frappe.db.get_value("Mode of Payment", self.mode_of_payment, "type")
        if bank_account == "Bank":
             if not self.reference_no:
                 frappe.throw(_("Reference No and Reference Date is mandatory for Bank transaction"))

    def update_advance(self):
        if self.employee_advance:
            self.db_set('employee_advance', 0)
    
    def update_additional(self):
        if self.additional_salary:
            self.db_set('additional_salary', 0)


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
        employee_advance.custom_bulk_employee_advance = row.parent

        employee_advance.save()
        frappe.db.commit()
        employee_advance.submit()
        created_advances.append(employee_advance.name)

        paid_to = frappe.get_doc("Mode of Payment", bulk_advance.mode_of_payment)
        paid_to_account = None

        if paid_to.accounts:
            for account in paid_to.accounts:
                if account.company == bulk_advance.company:  
                    paid_to_account = account.default_account
                    break

        if not paid_to_account:
            frappe.throw(_("No default account set for the selected mode of payment and company."))
        company_account = frappe.db.get_value(
            "Company", {"name": bulk_advance.company}, "default_employee_advance_account"
        )
        if not company_account:
            frappe.throw(_("Default employee advance account not found for the company."))
        payment_entry = frappe.new_doc("Payment Entry")
        payment_entry.payment_type = "Pay"
        payment_entry.posting_date = bulk_advance.posting_date
        payment_entry.mode_of_payment = bulk_advance.mode_of_payment
        payment_entry.party_type = "Employee"
        payment_entry.party = row.employee
        payment_entry.paid_amount = row.advance_amount
        payment_entry.received_amount = row.advance_amount
        payment_entry.paid_to = company_account
        payment_entry.paid_from = paid_to_account
        payment_entry.target_exchange_rate = bulk_advance.exchange_rate
        payment_entry.source_exchange_rate = bulk_advance.exchange_rate
        payment_entry.reference_no = bulk_advance.reference_no
        payment_entry.reference_date = bulk_advance.reference_date
        payment_entry.company = bulk_advance.company
        payment_entry.append(
            "references",
            {
                "reference_doctype": "Employee Advance",
                "reference_name": employee_advance.name,
                "allocated_amount": row.advance_amount,
            },
        )

        payment_entry.insert(ignore_permissions=True)
        payment_entry.submit()
        created_payment_entries.append(payment_entry.name)

    return {
        "created_advances": created_advances,
        "created_payment_entries": created_payment_entries,
    }



@frappe.whitelist()
def create_bulk_additional_salary(doc_name):
    bulk = frappe.get_doc("Bulk Employee Advance", doc_name)
    
    advances = frappe.get_all(
        "Employee Advance",
        filters={'custom_bulk_employee_advance': bulk.name},
        fields=["name", "employee"]
    )
    
    if not advances:
        frappe.throw(_("No Employee Advances found linked to Bulk Employee Advance: {0}").format(doc_name))
    
    advance_map = {advance["employee"]: advance for advance in advances}
    
    created_advances = []
    
    for row in bulk.employee_details:
            if row.employee not in advance_map:
                frappe.msgprint(_("No Employee Advance found for employee: {0}").format(row.employee),alert=True)
                
            employee_advance = frappe.new_doc("Additional Salary")
            employee_advance.employee = row.employee
            employee_advance.payroll_date = bulk.payroll_date
            employee_advance.salary_component = bulk.salary_component
            employee_advance.company = bulk.company
            employee_advance.amount = row.advance_amount
            
            linked_advance = advance_map[row.employee]
            employee_advance.ref_doctype = "Employee Advance"
            employee_advance.ref_docname = linked_advance["name"]
            employee_advance.custom_bulk_employee_advance = row.parent 
            
            employee_advance.save()
            employee_advance.submit()
            
            created_advances.append(employee_advance.name)
        
    return created_advances


        
    

    