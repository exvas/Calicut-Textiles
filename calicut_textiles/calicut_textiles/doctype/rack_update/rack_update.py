# Copyright (c) 2024, sammish and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RackUpdate(Document):
	pass

# your_app/your_app/doctype/rack_update/rack_update.py

# import frappe

# @frappe.whitelist()
# def get_items(item_group):
#     items = frappe.get_all('Item', filters={'item_group': item_group}, fields=['item_code','item_name','stock_uom','custom_rak_location'])
#     return items

# import frappe

# @frappe.whitelist()
# def get_items(item_group, warehouse):
#     items = frappe.get_all('Item', filters={'item_group': item_group}, fields=['item_code','item_name','stock_uom','custom_rak_location'])
    
#     for item in items:
#         bin_entries = frappe.get_all("Bin",
#                                      filters={
#                                          "item_code": item['item_code'],
#                                          "warehouse": warehouse
#                                      },
#                                      fields=["actual_qty"],
#                                      limit=1)
#         if bin_entries:
#             item['actual_qty'] = bin_entries[0].actual_qty
#         else:
#             item['actual_qty'] = 0
    
#     return items
import frappe

@frappe.whitelist()
def get_items(item_group, warehouse):
    items = frappe.get_all('Item', filters={'item_group': item_group}, fields=['item_code', 'item_name', 'stock_uom', 'custom_rak_location'])
    
    for item in items:
        bin_entries = frappe.get_all("Bin",
                                     filters={
                                         "item_code": item['item_code'],
                                         "warehouse": warehouse
                                     },
                                     fields=["actual_qty"],
                                     limit=1)
        if bin_entries:
            item['actual_qty'] = bin_entries[0].actual_qty
        else:
            item['actual_qty'] = 0
    
    return items

@frappe.whitelist()
def update_item_rack_locations(items):
    items = frappe.parse_json(items)
    updates_made = False  # Track whether any updates were made
    
    try:
        for item in items:
            if item.get('item_code') and item.get('rack'):
                # Get the current custom_rak_location for the item
                current_rack = frappe.db.get_value('Item', item['item_code'], 'custom_rak_location')
                if current_rack != item['rack']:
                    frappe.db.set_value('Item', item['item_code'], 'custom_rak_location', item['rack'])
                    updates_made = True
        
        if updates_made:
            frappe.db.commit()
            return "Rack locations updated successfully."
        else:
            return None  # No updates were made

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Rack Update Error")
        return f"Failed to update rack locations: {str(e)}"
