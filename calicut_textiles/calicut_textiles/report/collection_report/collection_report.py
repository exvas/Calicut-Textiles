import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data

def get_columns(filters=None):
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
            "align": "center"
        },
        {
            "label": _("Customer Name"),
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
    ]

    # Fetch and dynamically add columns for modes of payment
    mode_of_payment_list = frappe.db.sql("""
        SELECT DISTINCT mode_of_payment
        FROM (
            SELECT mode_of_payment FROM `tabSales Invoice Payment`
            UNION
            SELECT mode_of_payment FROM `tabPayment Entry`
        ) AS modes
    """, as_dict=True)

    # Fetch totals for each mode of payment to exclude those with total 0
    mode_of_payment_totals = frappe.db.sql("""
        SELECT sip.mode_of_payment, SUM(sip.amount) AS total
        FROM `tabSales Invoice Payment` sip
        LEFT JOIN `tabSales Invoice` si ON si.name = sip.parent
        WHERE si.is_return = 0 AND si.docstatus = 1
        GROUP BY sip.mode_of_payment
    """, as_dict=True)

    # Filter out modes of payment where total is 0
    valid_modes = [mop['mode_of_payment'] for mop in mode_of_payment_totals if mop['total'] > 0]

    for mop in valid_modes:
        columns.append({
            "label": _(mop),
            "fieldname": frappe.scrub(mop),
            "fieldtype": "Currency",
            "width": 150,
            "align": "center"
        })

    # Add columns for Voucher Type and Payment Reference ID
    columns.append({
        "label": _("Voucher Type"),
        "fieldname": "voucher_type",
        "fieldtype": "Data",
        "width": 150,
        "align": "center"
    })
    columns.append({
        "label": _("Payment Reference ID"),
        "fieldname": "payment_reference_id",
        "fieldtype": "Link",
        "options": "Payment Entry",  # Corrected to Payment Entry
        "width": 150,
        "align": "center"
    })

    return columns

def get_data(filters=None):
    mode_of_payment_totals = frappe.db.sql("""
        SELECT sip.mode_of_payment, SUM(sip.amount) AS total
        FROM `tabSales Invoice Payment` sip
        LEFT JOIN `tabSales Invoice` si ON si.name = sip.parent
        WHERE si.is_return = 0 AND si.docstatus = 1
        GROUP BY sip.mode_of_payment
    """, as_dict=True)

    # Filter out modes of payment where total is 0
    valid_modes = [mop['mode_of_payment'] for mop in mode_of_payment_totals if mop['total'] > 0]

    dynamic_mop_case_statements = ", ".join([
        f"SUM(CASE WHEN sip.mode_of_payment = '{mop}' "
        f"THEN COALESCE(sip.amount, 0) ELSE 0 END) AS `{frappe.scrub(mop)}`"
        for mop in valid_modes
    ])

    # SQL Query to fetch data
    query = f"""
    SELECT 
        si.name AS invoice_id,
        si.customer AS customer,
        si.customer_name AS customername,
        si.posting_date AS date,
        si.discount_amount AS discount,
        si.grand_total AS namount,
        {dynamic_mop_case_statements},
        CASE
            WHEN si.is_pos = 1 THEN 'Sales Invoice'
            WHEN pe.name IS NOT NULL THEN 'Payment Entry'
            ELSE 'Sales Invoice'
        END AS voucher_type,
        pe.name AS payment_reference_id  -- Corrected to get payment_reference_id from Payment Entry (pe.name)
    FROM
        `tabSales Invoice` si
    LEFT JOIN
        `tabSales Invoice Payment` sip ON sip.parent = si.name
    LEFT JOIN
        `tabPayment Entry Reference` per ON per.reference_name = si.name
    LEFT JOIN
        `tabPayment Entry` pe ON per.parent = pe.name
    WHERE
       si.posting_date BETWEEN %(from_date)s AND %(to_date)s
       AND si.is_return = 0 
       AND si.docstatus = 1
    """

    # Add filters dynamically
    if filters:
        if filters.get('customer'):
            query += " AND si.customer = %(customer)s"
        
        if filters.get('invoice_id'):
            query += " AND si.name = %(invoice_id)s"

    query += " GROUP BY si.name, si.customer, si.customer_name, si.posting_date, si.discount_amount, si.grand_total, pe.name, si.is_pos"

    # Execute the query
    item_list = frappe.db.sql(query, {
        'customer': filters.get('customer'),
        'invoice_id': filters.get('invoice_id'),
        'from_date': filters.get('from_date'),
        'to_date': filters.get('to_date')
    }, as_dict=True)

    data = []
    for item in item_list:
        row = {
            'invoice_id': item.invoice_id,
            'customer': item.customer,
            'customername': item.customername,
            'date': item.date,
            'discount': item.discount,
            'namount': item.namount
        }

        # Add dynamic mode of payment values only for valid modes
        for mop in valid_modes:
            mop_fieldname = frappe.scrub(mop)
            row[mop_fieldname] = item.get(mop_fieldname, 0)

        # Add Voucher Type and Payment Reference ID (from Payment Entry)
        row['voucher_type'] = item.get('voucher_type', None)
        row['payment_reference_id'] = item.get('payment_reference_id', None)

        data.append(row)

    return data
