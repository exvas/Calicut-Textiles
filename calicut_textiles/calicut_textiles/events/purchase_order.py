import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import comma_and, cstr, flt, getdate, nowdate, cint

@frappe.whitelist()
def make_supplier_packing_slip(purchase_order):

    order = frappe.get_doc("Purchase Order", purchase_order)
  
    
    sp = frappe.get_doc({
        'doctype': 'Supplier Packing Slip',
        'posting_date': order.transaction_date,
        'company': order.company,
        'supplier': order.supplier,
        'purchase_order': order.name
    })


    for item in order.items:
        sp_item = sp.append("supplier_packing_slip_item", {})
        sp_item.item_code = item.item_code
        sp_item.po_ref = item.parent
        sp_item.purchase_order_item = item.name
        sp_item.uom = item.uom
        sp_item.po_actual_qty = item.qty
        sp_item.po_remaining_qty = item.qty


    sp.insert(ignore_permissions=True)

    return sp.name