import frappe
from frappe import _

def validate_encashment_amount(doc, method):
    if not doc.base:
        frappe.throw(_("Base amount is required"))
    doc.custom_leave_encashment_amount_per_day = doc.base/30