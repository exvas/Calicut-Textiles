import frappe
from frappe import _

def execute(filters=None):
    # Fetch valid modes globally first
    valid_modes = get_valid_modes(filters)
    
    columns, data = get_columns(filters, valid_modes), get_data(filters, valid_modes)
    return columns, data

def get_valid_modes(filters):
    # Query to fetch dynamic modes of payment
    mode_of_payment_totals = frappe.db.sql("""
        SELECT sip.mode_of_payment, SUM(sip.amount) AS total
        FROM `tabSales Invoice Payment` sip
        LEFT JOIN `tabSales Invoice` si ON si.name = sip.parent
        WHERE si.is_return = 0 AND si.docstatus = 1
        GROUP BY sip.mode_of_payment
    """, as_dict=True)
    
    # Create list of valid modes with non-zero total
    valid_modes = [mop['mode_of_payment'] for mop in mode_of_payment_totals if mop['total'] > 0]
    return valid_modes

def get_columns(filters=None, valid_modes=None):
    columns = []

    # Define base columns
    if filters and filters.get("voucher_type") == "Payment Entry":
        # Columns for Payment Entry
        columns.extend([
            {
                "label": _("Receipt ID"),
                "fieldname": "receipt_id",
                "fieldtype": "Link",
                "options": "Payment Entry",
                "width": 150,
                "align": "center"
            },
            {
                "label": _("Customer Name"),
                "fieldname": "party_name",
                "fieldtype": "Data",
                "width": 150,
                "align": "center"
            },
            {
                "label": _("Paid Amount"),
                "fieldname": "paid_amount",
                "fieldtype": "Currency",
                "width": 150,
                "align": "center"
            },
        ])

        # Add dynamic columns for valid modes of payment (only for Payment Entry)
        for mode in valid_modes:
            columns.append({
                "label": _(mode),
                "fieldname": frappe.scrub(mode),
                "fieldtype": "Currency",
                "width": 150,
                "align": "center"
            })

    else:
        # Columns for Sales Invoice
        columns.extend([
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
            }
        ])

        # Add dynamic columns for valid modes of payment (only for Sales Invoice)
        for mode in valid_modes:
            columns.append({
                "label": _(mode),
                "fieldname": frappe.scrub(mode),
                "fieldtype": "Currency",
                "width": 150,
                "align": "center"
            })

        # Add the Voucher Type and Payment Reference ID columns for Sales Invoice, now at the end
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



def get_data(filters=None, valid_modes=None):
    data = []
    if filters and filters.get("voucher_type") == "Payment Entry":
        query = """
            SELECT 
                pe.name ,
                pe.party_name AS party_name,
                pe.paid_amount AS paid_amount,
                pe.mode_of_payment AS mode_of_payment,
                pe.posting_date AS date
            FROM
                `tabPayment Entry` pe
            LEFT JOIN
                `tabCustomer` c ON c.name = pe.party_name  -- Join with Customer table
            WHERE
                pe.docstatus = 1
                AND pe.payment_type = 'Receive'
                AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
        """

        item_list = frappe.db.sql(query, filters, as_dict=True)

        # Process the results for Payment Entry
        for item in item_list:
            row = {
                'receipt_id': item.name,
                'party_name': item.party_name,
                'paid_amount': item.paid_amount,
                'voucher_type': 'Payment Entry',
                'invoice_id': None,  # No invoice for Payment Entry
                'customer': None,  # No customer for Payment Entry
                'customername': item.customer_name,  # Customer name from the query
                'date': item.date,
                'discount': 0,
                'namount': 0
            }

            # Add dynamic mode of payment columns for Payment Entry
            for mode in valid_modes:
                row[frappe.scrub(mode)] = item.paid_amount if item.mode_of_payment == mode else 0

            data.append(row)

    else:
        # Query for Sales Invoice with dynamic mode of payment handling
        dynamic_mop_case_statements = ", ".join([
            f"SUM(CASE WHEN sip.mode_of_payment = '{mop}' "
            f"THEN COALESCE(sip.amount, 0) ELSE 0 END) AS `{frappe.scrub(mop)}`"
            for mop in valid_modes
        ])

        query = f"""
        SELECT 
            si.name AS invoice_id,
            si.customer AS customer,
            si.customer_name AS customername,
            pe.paid_amount AS paid_amount,
            si.posting_date AS date,
            si.discount_amount AS discount,
            si.grand_total AS namount,
            {dynamic_mop_case_statements},
            CASE
                WHEN si.is_pos = 1 THEN 'Sales Invoice'
                WHEN pe.name IS NOT NULL THEN 'Payment Entry'
                ELSE 'Sales Invoice'
            END AS voucher_type,
            pe.name AS payment_reference_id
        FROM
            `tabSales Invoice` si
        LEFT JOIN
            `tabSales Invoice Payment` sip ON sip.parent = si.name
        LEFT JOIN
            `tabPayment Entry Reference` per ON per.reference_name = si.name
        LEFT JOIN
            `tabPayment Entry` pe ON per.parent = pe.name
        WHERE
            si.is_return = 0 
            AND si.docstatus = 1
        GROUP BY
            si.name, si.customer, si.customer_name, si.posting_date, si.discount_amount, si.grand_total, pe.name, si.is_pos
        """

        # Add filters to the query
        if filters:
            if filters.get('customer'):
                query += " AND si.customer = %(customer)s"
            if filters.get('invoice_id'):
                query += " AND si.name = %(invoice_id)s"
            if filters.get('from_date'):
                query += " AND si.posting_date >= %(from_date)s"
            if filters.get('to_date'):
                query += " AND si.posting_date <= %(to_date)s"

        # Execute the query and process data
        item_list = frappe.db.sql(query, {
            'customer': filters.get('customer') if filters else None,
            'invoice_id': filters.get('invoice_id') if filters else None,
            'from_date': filters.get('from_date') if filters else None,
            'to_date': filters.get('to_date') if filters else None
        }, as_dict=True)

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
