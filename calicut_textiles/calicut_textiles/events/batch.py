import frappe
from frappe.model.document import Document
from frappe import _


def update_qty(doc, method):
    if doc.voucher_type == 'Purchase Receipt':
        for batch_entry in doc.entries:
            if batch_entry.batch_no: 
                pr_items = frappe.get_all(
                    'Purchase Receipt Item',
                    filters={'item_code': doc.item_code, 'qty': batch_entry.qty, 'parent': doc.voucher_no},
                    fields=['name', 'custom_net_qty']
                )
                
                for pr_item in pr_items:
                        print("fcgvhjkl",pr_item)
                        frappe.db.set_value('Batch', batch_entry.batch_no, 'custom_qty', pr_item['custom_net_qty'])
      