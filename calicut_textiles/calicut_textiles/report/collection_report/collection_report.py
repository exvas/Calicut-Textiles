# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {
            "label": _("Bill No"),
            "fieldname": "invoice_id",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 150,
            "align": "center"
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150,
            "hidden": 1,
            "align": "center"
        },
        {
            "label": _("Customer"),
            "fieldname": "customername",
            "fieldtype": "Data",
            "width": 150,
            "align": "center"
        },
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 150,
            "align": "center"
        },
        {
            "label": _("Discount"),
            "fieldname": "discount",
            "fieldtype": "Currency",
            "width": 150,
            "align": "center"
        },
        {
            "label": _("Net Amount"),
            "fieldname": "namount",
            "fieldtype": "Currency",
            "width": 150,
            "align": "center"
        },
        {
            "label": _("Mode of Payment"),
            "fieldname": "mop",
            "fieldtype": "Link",
            "options": "Mode of Payment",
            "width": 150,
            "align": "center"
        },
        {
            "label": _("Amount"),
            "fieldname": "cashamount",
            "fieldtype": "Currency",
            "width": 150,
            "align": "center"
        },
        {
            "label": _("References"),
            "fieldname": "payment_entry_id",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 150,
            "align": "center"
        }
    ]
    return columns


def get_data(filters=None):
    data = []
    query = """
            SELECT 
            si.name AS invoice_id,
            si.customer AS customer,
            si.customer_name AS customername,
            si.posting_date AS date,
            si.discount_amount AS discount,
            si.grand_total AS namount,
            COALESCE(sip.mode_of_payment, pe.mode_of_payment) AS mop,
            COALESCE(sip.amount, pe.paid_amount) AS cashamount,
            -- Display the Payment Entry ID (pe.name is the Payment ID)
            pe.name AS payment_entry_id  
            FROM 
                `tabSales Invoice` si
            LEFT JOIN 
                `tabSales Invoice Payment` sip ON sip.parent = si.name
            LEFT JOIN 
                `tabPayment Entry Reference` per ON per.reference_name = si.name
            LEFT JOIN 
                `tabPayment Entry` pe ON per.parent = pe.name  
            WHERE 
                si.is_return = 0;




    """

    # Apply filters if provided
    if filters:
        if filters.get('customer'):
            query += " AND si.customer = %(customer)s"
        if filters.get('invoice_id'):
            query += " AND si.name = %(invoice_id)s"
        if filters.get('mode_of_payment'):
            query += " AND COALESCE(sip.mode_of_payment, pe.mode_of_payment) = %(mode_of_payment)s"

    # Execute the query with the filters
    item_list = frappe.db.sql(query, {
        'customer': filters.get('customer') if filters else None,
        'invoice_id': filters.get('invoice_id') if filters else None,
        'mode_of_payment': filters.get('mode_of_payment') if filters else None
    }, as_dict=True)

    # Prepare the data
    for item in item_list:
        row = {
            'invoice_id': item.invoice_id,
            'customer': item.customer,
            'customername': item.customername,
            'date': item.date,
            'discount': item.discount,
            'namount': item.namount,
            'mop': item.mop,
            'cashamount': item.cashamount,
            'payment_entry_id':item.payment_entry_id
        }
        data.append(row)

    return data
