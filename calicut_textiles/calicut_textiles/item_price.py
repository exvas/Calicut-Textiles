import frappe

def convert_rate_to_code(sanforize):
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
def update_custom_rate_code(doc, method):
    item_code = doc.item_code


    sanforize_value = doc.price_list_rate
    an_value = convert_rate_to_code(sanforize_value)

    custom_rate_code = f"{an_value}"
    print(custom_rate_code)

    doc.custom_rate_code = custom_rate_code