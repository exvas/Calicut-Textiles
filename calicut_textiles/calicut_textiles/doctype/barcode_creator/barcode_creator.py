# Copyright (c) 2024, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BarcodeCreator(Document):
	def validate(self):
		for item in self.barcode_creator_item:
			if not item.item_barcode:
				frappe.throw("Barcode is Required")
@frappe.whitelist()
def get_items(item_group):
    if not item_group:
        frappe.throw("Please select an item group")

    # Fetch items based on the item group
    items = frappe.get_all("Item", filters={"item_group": item_group}, fields=["item_code", "item_name"])

    result = []

    for item in items:
        # Get barcodes for each item
        barcodes = frappe.get_all("Item Barcode", filters={"parent": item.item_code}, fields=["barcode"])

        if not barcodes:
            # If no barcodes found, append with an empty barcode
            result.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "barcode": ""
            })
        else:
            # Add each barcode to the result list
            for barcode in barcodes:
                result.append({
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "barcode": barcode.barcode
                })

    return result







