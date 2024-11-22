from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

import frappe
from frappe import _

class CustomPaymentEntry(PaymentEntry):
    def validate(self):
        self.setup_party_account_field()
        self.set_missing_values()
        self.set_liability_account()
        self.set_missing_ref_details(force=True)
        self.validate_payment_type()
        self.validate_party_details()
        self.set_exchange_rate()
        self.validate_mandatory()
        self.validate_reference_documents()  
        self.set_amounts()
        self.validate_amounts()
        self.apply_taxes()
        self.set_amounts_after_tax()
        self.clear_unallocated_reference_document_rows()
        self.validate_transaction_reference()
        self.set_title()
        self.set_remarks()
        self.validate_duplicate_entry()
        self.validate_payment_type_with_outstanding()
        self.validate_allocated_amount()
        self.validate_paid_invoices()
        self.ensure_supplier_is_not_blocked()
        self.set_tax_withholding()
        self.set_status()
        self.set_total_in_words()

    def validate_transaction_reference(self):
        pass
        