import frappe
from frappe import _
from erpnext.stock.utils import _update_item_info
from frappe.utils import *

from typing import Dict, Optional

BarcodeScanResult = Dict[str, Optional[str]]

@frappe.whitelist()
def scan_barcode(search_value: str) -> BarcodeScanResult:
	def set_cache(data: BarcodeScanResult):
		frappe.cache().set_value(f"erpnext:barcode_scan:{search_value}", data, expires_in_sec=120)

	def get_cache() -> BarcodeScanResult | None:
		if data := frappe.cache().get_value(f"erpnext:barcode_scan:{search_value}"):
			return data

	if scan_data := get_cache():
		return scan_data

	# search barcode no
	barcode_data = frappe.db.get_value(
		"Item Barcode",
		{"barcode": search_value},
		["barcode", "parent as item_code", "uom"],
		as_dict=True,
	)
	if barcode_data:
		_update_item_info(barcode_data)
		set_cache(barcode_data)
		return barcode_data

	# search serial no
	serial_no_data = frappe.db.get_value(
		"Serial No",
		search_value,
		["name as serial_no", "item_code", "batch_no"],
		as_dict=True,
	)
	if serial_no_data:
		_update_item_info(serial_no_data)
		set_cache(serial_no_data)
		return serial_no_data

	# search batch no
	batch_no_data = frappe.db.get_value(
		"Batch",
		search_value,
		["name as batch_no", "item as item_code", "batch_qty as qty"],
		as_dict=True,
	)
	print(batch_no_data)
	if batch_no_data:
		if frappe.get_cached_value("Item", batch_no_data.item_code, "has_serial_no"):
			frappe.throw(
				_(
					"Batch No {0} is linked with Item {1} which has serial no. Please scan serial no instead."
				).format(search_value, batch_no_data.item_code)
			)
			
        
		_update_item_info(batch_no_data)
		set_cache(batch_no_data)
		return batch_no_data

	return {}


# def validate_sales_person(doc,method):
# 	if not doc.custom_sales_person:
# 		frappe.throw(_("Please select a sales person"))


@frappe.whitelist()
def set_user_and_customer_and_branch(user):
    settings = frappe.get_single("Calicut Textiles Settings")

    user_series = [
        doc.series for doc in settings.set_user_series if doc.user == user
    ]

    user_tax = [
        doc.sales_taxes_template for doc in settings.set_user_series if doc.user == user
    ]

    user_branch = [
        doc.branch for doc in settings.set_user_series if doc.user == user
    ]

    # user_price = [
    #     doc.price_list for doc in settings.set_user_series if doc.user == user
    # ]

    default_price = None
    for doc in settings.set_user_series:
        if doc.user == user:
            default_price = doc.price_list
            break

    return {
        "user_series": user_series if user_series else [],
        "default_tax": user_tax[0] if user_tax else None,
        "default_branch": user_branch[0] if user_branch else None,
        "default_price": default_price
    }

def validate_fields(doc,method):
    if not doc.customer_address:
        frappe.throw(_("Please select a customer address"))
    
            
