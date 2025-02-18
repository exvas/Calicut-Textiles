import frappe
from datetime import datetime
from frappe import _
import os, re, json

def convert_date_to_code(sanforize):
    mapping = {
        '1': 'S',
        '2': 'A',
        '3': 'N',
        '4': 'F',
        '5': 'O',
        '6': 'R',
        '7': 'I',
        '8': 'Z',
        '9': 'E',
        '0': '+'
    }
    
    result = ''
    digits = str(sanforize)
    for digit in digits:
        if digit in mapping:
            result += mapping[digit]
    return result

@frappe.whitelist()
def custom_date_code(doc, method):
    posting_date = datetime.strptime(doc.posting_date, '%Y-%m-%d')

    month_year = posting_date.strftime('%m%y')

    custom_code = convert_date_to_code(month_year)

    doc.custom_date_code = custom_code


def update_supplier_packing_slip(doc, method):
    pr = frappe.get_doc("Purchase Receipt", doc.name)
    for item in pr.items:
        supplier_packing_slip = item.custom_supplier_packing_slip
        
        if supplier_packing_slip:
            sp = frappe.get_doc("Supplier Packing Slip", supplier_packing_slip)
            sp.purchase_receipt = 1
            sp.save()


@frappe.whitelist()
def create_landed_cost_voucher(pr):
    purchase_receipt = frappe.get_doc("Purchase Receipt", pr)
    clt_settings = frappe.get_single("Calicut Textiles Settings")

 
    lcv = frappe.new_doc("Landed Cost Voucher")
    

    lcv.company = purchase_receipt.company
    lcv.posting_date = purchase_receipt.posting_date

    lcv.append("purchase_receipts", {
        "receipt_document_type": "Purchase Receipt",
        "receipt_document": purchase_receipt.name,
        "posting_date": purchase_receipt.posting_date,
        "supplier": purchase_receipt.supplier,
        "grand_total": purchase_receipt.grand_total
    })

    for tax in clt_settings.taxes:
        if tax.transport_charge and purchase_receipt.custom_total_lr_rate:
            lcv.append("taxes", {
                "expense_account": tax.expense_account,
                "description": tax.description,  
                "amount": purchase_receipt.custom_total_lr_rate
            })
        elif tax.handling_charge and purchase_receipt.custom_handling_charge_rate:
            lcv.append("taxes", {
                "expense_account": tax.expense_account,
                "description": tax.description,  
                "amount": purchase_receipt.custom_handling_charge_rate
            })

    lcv.save()
    lcv.submit()
    purchase_receipt.custom_landed_cost = 1  
    purchase_receipt.save()  

    return lcv.name



@frappe.whitelist()
def create_item_price(items):
    
    items = json.loads(items)

    price_list_mrp = frappe.db.get_value("Calicut Textiles Settings", None, "price_listmrp")
    retail_price_list = frappe.db.get_value("Calicut Textiles Settings", None, "retail_price")

    if not price_list_mrp or not retail_price_list:
        frappe.throw("Price lists are not configured in Calicut Textiles Settings.")

    for item in items:
        batch_no = frappe.db.get_value(
            "Serial and Batch Entry",
            {"parent": item.get("serial_and_batch_bundle")},
            "batch_no"
        )

        selling_rate = item.get("custom_selling_rate")
        retail_rate = item.get("custom_retail_rate")

        if not selling_rate and not retail_rate:
            continue

        if selling_rate:
            item_price = frappe.get_all(
                "Item Price",
                filters={
                    "item_code": item.get("item_code"),
                    "price_list": price_list_mrp,
                    "batch_no": batch_no
                },
                fields=["name"]
            )

            if item_price:
                item_price_doc = frappe.get_doc("Item Price", item_price[0].name)
                item_price_doc.price_list_rate = selling_rate
                item_price_doc.save()
            else:
                frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item.get("item_code"),
                    "uom": item.get("uom"),
                    "price_list": price_list_mrp,
                    "price_list_rate": selling_rate,
                    "batch_no": batch_no,
                    "custom_purchase_receipt_": item.get("parent")
                }).insert()

        if retail_rate:
            item_price = frappe.get_all(
                "Item Price",
                filters={
                    "item_code": item.get("item_code"),
                    "price_list": retail_price_list,
                    "batch_no": batch_no,
                },
                fields=["name"]
            )

            if item_price:
                item_price_doc = frappe.get_doc("Item Price", item_price[0].name)
                item_price_doc.price_list_rate = retail_rate
                item_price_doc.save()
            else:
                frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item.get("item_code"),
                    "uom": item.get("uom"),
                    "price_list": retail_price_list,
                    "price_list_rate": retail_rate,
                    "batch_no": batch_no,
                    "custom_purchase_receipt_": item.get("parent")
                }).insert()

    frappe.db.commit()
    return "Item prices updated successfully."

def delete_item_prices(doc, method):
    item_prices = frappe.get_all(
        "Item Price",
        filters={"custom_purchase_receipt_": doc.name},fields=["name"])

    for item_price in item_prices:
            item_price_doc = frappe.get_doc("Item Price", item_price.name)
            item_price_doc.delete()
        
def validate_supplier_no(doc,method):
    if not doc.bill_no:
        frappe.throw("Supplier Invoice No Required")