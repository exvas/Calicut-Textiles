import frappe

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
    print(doc)

    sanforize_value = doc.posting_date
    an_value = convert_date_to_code(sanforize_value)

    custom_date_code = f"{an_value}"
    
    doc.custom_date_code = custom_date_code
