# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    columns = [
        # {
        #     "label": _("  Item Code"),
        #     "fieldname": "item_code",
        #     "fieldtype": "Data",
        #     "width": 150,
        # },
        {
            "label": _("Bill No"),
            "fieldname": "invoice_id",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 150,
        },
        {
            "label": _("Customer"),
            "fieldname": "customername",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 150,
        },
         {
            "label": _("Discount"),
            "fieldname": "discount",
            "fieldtype": "Currency",
            "width": 150,
        },
        
        {
            "label": _("Net Amount"),
            "fieldname": "namount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Mode of Payment"),
            "fieldname": "mop",
            "fieldtype": "LinK",
            "options": "Mode of Payment",
            "width": 150,
        },

         {
            "label": _("Amount"),
            "fieldname": "cashamount",
            "fieldtype": "Currency",
            "width": 150,
        },
        #  {
        #     "label": _("Card Amount"),
        #     "fieldname": "cardamount",
        #     "fieldtype": "Currency",
        #     "width": 150,
        # },
        #  {
        #     "label": _("Credit Amount"),
        #     "fieldname": "creditamount",
        #     "fieldtype": "Currency",
        #     "width": 150,
        # },
        #  {
        #     "label": _("Cheque"),
        #     "fieldname": "cheque",
        #     "fieldtype": "Currency",
        #     "width": 150,
        # },
        
    ]
    return columns

def get_data(filters=None):
    data = []
    query = """
        SELECT 
    `tabSales Invoice`.`name` AS `invoice_id`,
    `tabSales Invoice`.`customer_name`,
    `tabSales Invoice`.`posting_date`,
    `tabSales Invoice`.`discount_amount`,
    `tabSales Invoice`.`grand_total`,
    `tabSales Invoice Payment` .`mode_of_payment` ,

    `tabSales Invoice Payment` .`amount` 
FROM 
    `tabSales Invoice`

INNER JOIN 
    `tabSales Invoice Payment` 
    ON `tabSales Invoice Payment`.`parent` = `tabSales Invoice`.`name`

    """
  

    item_list = frappe.db.sql(query, filters, as_dict=True)

    for item in item_list:
        row = {
            'invoice_id': item.invoice_id,
            
            'customername':item.customer_name,
            'date': item.posting_date,
            'discount':item.discount_amount,
            'namount':item.grand_total,
            'mop':item.mode_of_payment,
           'cashamount': item.amount,
            # 'cardamount':item.,
            # 'creditamount':item.,
            # 'cheque':item.
            
            
        }
        data.append(row)

    return data
