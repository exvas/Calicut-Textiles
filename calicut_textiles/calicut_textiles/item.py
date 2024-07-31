import frappe

@frappe.whitelist()
def update_item_code(self, method):
    if self.custom_division and self.custom_categories and self.brand and self.custom_item_short_name:
        division = frappe.db.get_value("Division",self.custom_division,'code_id')
        categories = frappe.db.get_value("Categories",self.custom_categories,'code_id')
        brand = frappe.db.get_value("Brand",self.brand,'custom_code')
        print(str(division)+str(categories)+str(brand))
        self.item_code = str(division)+str(categories)+str(brand)+str(self.custom_item_short_name)

@frappe.whitelist()
def update_barcode(self, method):
    if self.item_code:
        self.append("barcodes",{
            "barcode":self.item_code
        })