import frappe
from frappe.model.document import Document
from frappe import _

def update_batch_in_purchase_receipt(doc, method):
    if doc.voucher_type == 'Purchase Receipt':
        for batch_entry in doc.entries:
            if batch_entry.batch_no: 
                pr_items = frappe.get_all(
                    'Purchase Receipt Item',
                    filters={'item_code': doc.item_code, 'qty': batch_entry.qty, 'parent': doc.voucher_no},
                    fields=['name', 'custom_batch']
                )
                
                updated_items = []
                
                for pr_item in pr_items:
                    if pr_item.get('custom_batch') != batch_entry.batch_no:
                        frappe.db.set_value('Purchase Receipt Item', pr_item['name'], 'custom_batch', batch_entry.batch_no)
                        updated_items.append({'name': pr_item['name'], 'custom_batch': batch_entry.batch_no})
                frappe.db.commit()
      

def update_qty(doc, method):
    for batch_entry in doc.entries:
        if batch_entry.batch_no: 
            pr_items = frappe.get_all(
                'Purchase Receipt Item',
                filters={'item_code': doc.item_code, 'qty': batch_entry.qty, 'parent': doc.voucher_no},
                fields=['name', 'custom_sp_qty']
            )
            
            for pr_item in pr_items:
                    print("fcgvhjkl",pr_item)
                    frappe.db.set_value('Batch', batch_entry.batch_no, 'custom_qty', pr_item['custom_sp_qty'])
    frappe.db.commit()
      