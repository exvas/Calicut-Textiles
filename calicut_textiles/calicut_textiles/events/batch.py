import frappe
from frappe.model.document import Document
from frappe import _

def update_batch_in_purchase_receipt(doc, method):
    for code in doc.entries:
        pr_items = frappe.get_all('Purchase Receipt Item', filters={'item_code': doc.item_code,'serial_and_batch_bundle': doc.name}, fields=['name'])

        for pr_item in pr_items:
            frappe.db.set_value('Purchase Receipt Item', pr_item['name'], 'custom_batch', code.batch_no)
    
    frappe.db.commit()