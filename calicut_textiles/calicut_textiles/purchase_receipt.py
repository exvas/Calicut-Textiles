import frappe
from datetime import datetime

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
        '0': 'T'
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
