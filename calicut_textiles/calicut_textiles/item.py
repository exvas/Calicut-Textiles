import frappe
from frappe import _

@frappe.whitelist()
def update_item_code(self, method):
    if self.item_group and self.brand and self.custom_item_short_name:
        categories = frappe.db.get_value("Item Group",self.item_group,'custom_code')
        brand = frappe.db.get_value("Brand",self.brand,'custom_code')
        self.item_code = str(categories)+str(brand)+str(self.custom_item_short_name)

# @frappe.whitelist()
# def update_barcode(self, method):
#     if self.item_code:
#         self.append("barcodes",{
#             "barcode":self.item_code
#         })



def update_batch_number_series(doc, method):

    batch_number_series = f"1.########"

    doc.batch_number_series = batch_number_series


def item_name_unique(doc, method):
    if doc.item_name:
        existing_item = frappe.db.exists("Item", {"item_name": doc.item_name, "name": ["!=", doc.name]})
        if existing_item:
            frappe.throw(_("An item with the name '{0}' already exists. Please choose a unique name.").format(doc.item_name))

