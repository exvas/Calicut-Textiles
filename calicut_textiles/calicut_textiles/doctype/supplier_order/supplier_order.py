# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document

class SupplierOrder(Document):
    def on_submit(self):
        
        create_purchase_order_from_supplier_order(self)


def create_purchase_order_from_supplier_order(supplier_order):
    po = frappe.new_doc("Purchase Order")
    po.supplier = supplier_order.supplier
    po.custom_sales_person = supplier_order.sales_person
    po.schedule_date = supplier_order.order_date or frappe.utils.nowdate()
    po.set_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
    po.supplier_order_id = supplier_order.name

    for product in supplier_order.products:
        po.append("items", {
            "item_code": product.item,
            "custom_net_qty": product.quantity,
            "qty":product.net_qty,
            "custom_pcs":product.pcs,
            "uom": product.uom or "Nos",
            "rate": product.rate,
            "schedule_date": product.required_by or frappe.utils.nowdate(),
            "warehouse": po.set_warehouse
        })

    po.insert(ignore_permissions=True)
    po.save()

    # Force update and reload
    frappe.db.set_value("Supplier Order", supplier_order.name, "status", "Submitted")
    frappe.db.commit()
    supplier_order.reload()

    frappe.msgprint(f"✅ Purchase Order <b>{po.name}</b> created from Supplier Order <b>{supplier_order.name}</b>")
