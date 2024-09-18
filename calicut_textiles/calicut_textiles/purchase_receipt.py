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