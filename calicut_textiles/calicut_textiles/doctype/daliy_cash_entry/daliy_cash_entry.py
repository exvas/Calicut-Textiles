# Copyright (c) 2026, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DaliyCashEntry(Document):
	def on_cancel(self):
		if self.payment_entry:
			pe = frappe.get_doc("Payment Entry", self.payment_entry)
			if pe.docstatus == 1:
				pe.cancel()
			frappe.db.set_value(self.doctype, self.name, "payment_entry", None)
			frappe.db.commit()
			# pe.delete()
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.cancel()
			frappe.db.set_value(self.doctype, self.name, "journal_entry", None)
			frappe.db.commit()
			# je.delete()

@frappe.whitelist()
def create_payment_entry(daliy_cash_entry):
	doc = frappe.get_doc("Daliy Cash Entry", daliy_cash_entry)
	company = frappe.db.get_single_value("Global Defaults", "default_company")
	if doc.paid_type:
		payment_entry = frappe.get_doc({
			"doctype": "Payment Entry",
			"payment_type": "Pay",
			"mode_of_payment": "Cash",
			"company": company,
			"paid_from": frappe.db.get_value("Company", company, "default_cash_account"),
			"party_type": doc.paid_type,
			"party": doc.paid_to,
			"received_amount":doc.amount,
			"paid_amount": doc.amount,
			"source_exchange_rate": 1,
			"target_exchange_rate": 1,
			"cost_center": doc.cost_center if doc.cost_center else frappe.db.get_value("Company", company, "cost_center"),
			"remarks": doc.note
		})
		payment_entry.insert()
		frappe.db.set_value(doc.doctype, doc.name, "payment_entry", payment_entry.name)
		frappe.db.commit()
		return payment_entry

@frappe.whitelist()
def create_journal_entry(daliy_cash_entry):
	doc = frappe.get_doc("Daliy Cash Entry", daliy_cash_entry)
	company = frappe.db.get_single_value("Global Defaults", "default_company")
	journal_entry = frappe.get_doc({
		"doctype": "Journal Entry",
		"company": company,
		"posting_date": doc.posting_date,
		"user_remark": f"Paid To :{doc.paid_name}, Note:{doc.note}",
		"accounts": [
			{
				"account": frappe.db.get_value("Company", company, "default_cash_account"),
				"debit_in_account_currency": doc.amount,
				"debit": doc.amount,
				"cost_center": doc.cost_center if doc.cost_center else frappe.db.get_value("Company", company, "cost_center"),
			},
			{
				"account": frappe.db.get_value("Company", company, "default_expense_account"),
				"credit_in_account_currency": doc.amount,
				"credit": doc.amount,
				"cost_center": doc.cost_center if doc.cost_center else frappe.db.get_value("Company", company, "cost_center"),
			}
		]
	})
	journal_entry.insert()
	frappe.db.set_value(doc.doctype, doc.name, "journal_entry", journal_entry.name)
	frappe.db.commit()
	return journal_entry


@frappe.whitelist()
def delete_linked_daliy_cash_entry(payment_entry, method):
	dce_name = frappe.db.get_value("Daliy Cash Entry", {"payment_entry": payment_entry.name})
	if dce_name:
		dce = frappe.get_doc("Daliy Cash Entry", dce_name)
		frappe.db.set_value(dce.doctype, dce.name, "payment_entry", None)
		frappe.db.commit()
		if dce.docstatus == 1:
			dce.cancel()
			
@frappe.whitelist()
def delete_linked_journal_daliy_cash_entry(journal_entry, method):
	dce_name = frappe.db.get_value("Daliy Cash Entry", {"journal_entry": journal_entry.name})
	if dce_name:
		dce = frappe.get_doc("Daliy Cash Entry", dce_name)
		frappe.db.set_value(dce.doctype, dce.name, "journal_entry", None)
		frappe.db.commit()
		if dce.docstatus == 1:
			dce.cancel()