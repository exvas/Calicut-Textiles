import frappe
from datetime import datetime
from frappe import _

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


