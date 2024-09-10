import frappe
from frappe.model.document import Document
from frappe import _

def update_batch_in_purchase_receipt(doc, method):
    pr_items = frappe.get_all('Purchase Receipt Item', filters={'item_code': doc.item,'parent': doc.reference_name}, fields=['name'])

    for pr_item in pr_items:
        frappe.db.set_value('Purchase Receipt Item', pr_item['name'], 'custom_batch', doc.name)
    
    frappe.db.commit()