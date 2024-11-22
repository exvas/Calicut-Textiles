import frappe
from frappe import _
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
        '0': '+'
    }
    
    result = ''
    digits = str(sanforize)
    for digit in digits:
        if digit in mapping:
            result += mapping[digit]
    return result

def custom_date_code(doc, method):
    if isinstance(doc.posting_date, str):
        posting_date = datetime.strptime(doc.posting_date, '%Y-%m-%d')
    else:
        posting_date = doc.posting_date

    month_year = posting_date.strftime('%m%y')

    custom_code = convert_date_to_code(month_year)

    doc.custom_sanforize = custom_code


def update_employee_advance(doc, method):
    ea = frappe.get_doc("Employee Advance", doc.name)
    
    advance = ea.custom_bulk_employee_advance
        
    if advance:
        sp = frappe.get_doc("Bulk Employee Advance", advance)
        sp.employee_advance = 1
        sp.save()


def update_employee_additional(doc, method):
    ea = frappe.get_doc("Additional Salary", doc.name)
    
    advance = ea.custom_bulk_employee_advance
        
    if advance:
        sp = frappe.get_doc("Bulk Employee Advance", advance)
        sp.additional_salary = 1
        sp.save()