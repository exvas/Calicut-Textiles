import frappe

@frappe.whitelist()
def update_item_code(self, method):
    if self.custom_categories and self.brand and self.custom_item_short_name:
        categories = frappe.db.get_value("Categories",self.custom_categories,'code_id')
        brand = frappe.db.get_value("Brand",self.brand,'custom_code')
        self.item_code = str(categories)+str(brand)+str(self.custom_item_short_name)

@frappe.whitelist()
def update_barcode(self, method):
    if self.item_code:
        self.append("barcodes",{
            "barcode":self.item_code
        })

def convert_sanforize_to_code(sanforize):
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

def update_batch_number_series(doc, method):
    item_code = doc.item_code
    
    current_month = frappe.utils.now_datetime().strftime("%m")

    sanforize_value = doc.custom_sanforize
    an_value = convert_sanforize_to_code(sanforize_value)

    batch_number_series = f"{item_code}-{current_month}-{an_value}-.###"
    print(batch_number_series)

    doc.batch_number_series = batch_number_series




