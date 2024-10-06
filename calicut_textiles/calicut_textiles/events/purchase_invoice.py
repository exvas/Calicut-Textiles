import frappe


def create_purchase_invoices(doc, method):
    item = frappe.get_doc("Calicut Textiles Settings")

    if not doc.transporter:
        return
    
    if not item.transporter_item:
        frappe.throw("Transporter Item is not set in Calicut Textiles Settings")
        
    invoice_1 = frappe.new_doc("Purchase Invoice")
    invoice_1.supplier = doc.transporter
    invoice_1.posting_date = doc.lr_date
    invoice_1.bill_no = doc.bill_no
    invoice_1.append("items", {
        "item_code": item.transporter_item,
        "qty": 1,
        "rate": doc.custom_total_lr_rate
    })
    invoice_1.submit()

    if not doc.custom_handling_charger:
        return

    
    if not item.handling_charge_item:
        frappe.throw("Handling Charge Item is not set in Calicut Textiles Settings")

    invoice_2 = frappe.new_doc("Purchase Invoice")
    invoice_2.supplier = doc.custom_handling_charger
    invoice_2.posting_date = doc.custom_handling_charge_date
    invoice_1.bill_no = doc.bill_no
    invoice_2.append("items", {
        "item_code": item.handling_charge_item,
        "qty": 1,
        "rate": doc.custom_handling_charge_rate
    })
    invoice_2.submit()



