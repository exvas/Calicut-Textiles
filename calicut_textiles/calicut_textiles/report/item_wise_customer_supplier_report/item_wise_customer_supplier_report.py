import frappe

def execute(filters=None):
    if not filters:
        filters = {}
    


    # DEBUG: Print filters to check if they are correctly passed
    frappe.logger().info(f"Received filters: {filters}")

    # Validate that required filters exist
    required_filters = ["from_date", "to_date", "party_type", "party_name"]
    for field in required_filters:
        if field not in filters or not filters[field]:
            frappe.throw(f"Missing required filter: {field}")

    columns = get_columns(filters)  # Pass filters to get_columns()
    data = get_data(filters)

    return columns, data

def get_columns(filters):
    columns = [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 200},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 200},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        # {"label": "Quantity", "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": "Rate", "fieldname": "rate", "fieldtype": "Currency", "width": 200},
    ]

    if filters.get("party_type") == "Customer":
        columns.insert(1, {"label": "Sales Invoice ID", "fieldname": "invoice_id", "fieldtype": "Link", "options": "Sales Invoice", "width": 200})
        columns.append({"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 200})
        columns.append({"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width": 200})
    
    elif filters.get("party_type") == "Supplier":
        columns.insert(1, {"label": "Purchase Invoice ID", "fieldname": "invoice_id", "fieldtype": "Link", "options": "Purchase Invoice", "width": 200})
        columns.append({"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width":200})
        # columns.append({"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 150})

    return columns


def get_data(filters):
    data = []

    if filters.get("party_type") == "Customer":
        # Fetch unique items sold to the customer
        sales_query = """
            SELECT
				si.posting_date, si.name AS invoice_id, si_item.item_code, si_item.item_name,
				'Customer' AS party_type, si.customer AS party_name, 
				c.customer_name AS customer_name, 
				s.supplier_name AS supplier_name,  -- Add supplier_name for customer condition
				pi.supplier AS related_party_name,
				SUM(si_item.qty) AS qty, AVG(si_item.rate) AS rate
			FROM `tabSales Invoice Item` si_item
			JOIN `tabSales Invoice` si ON si_item.parent = si.name
			LEFT JOIN `tabCustomer` c ON si.customer = c.name
			LEFT JOIN `tabPurchase Invoice Item` pi_item ON si_item.item_code = pi_item.item_code
			LEFT JOIN `tabPurchase Invoice` pi ON pi_item.parent = pi.name
			LEFT JOIN `tabSupplier` s ON pi.supplier = s.name  -- Join with tabSupplier to get supplier_name
			WHERE si.docstatus = 1 
				AND si.customer = %(party_name)s
				AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			GROUP BY si_item.item_code  -- Ensures only one row per item
		"""

        data += frappe.db.sql(sales_query, filters, as_dict=True)

    elif filters.get("party_type") == "Supplier":
        # Fetch unique items purchased from the supplier
        purchase_query = """
             SELECT
				pi.posting_date, pi.name AS invoice_id, pi_item.item_code, pi_item.item_name,
				'Supplier' AS party_type, pi.supplier AS party_name, 
				s.supplier_name AS supplier_name,  -- Ensure supplier_name is selected
				si.customer AS related_party_name, 
				SUM(pi_item.qty) AS qty, AVG(pi_item.rate) AS rate
			FROM `tabPurchase Invoice Item` pi_item
			JOIN `tabPurchase Invoice` pi ON pi_item.parent = pi.name
			LEFT JOIN `tabSupplier` s ON pi.supplier = s.name  -- Join with tabSupplier to get supplier_name
			LEFT JOIN `tabSales Invoice Item` si_item ON pi_item.item_code = si_item.item_code
			LEFT JOIN `tabSales Invoice` si ON si_item.parent = si.name
			WHERE pi.docstatus = 1 
				AND pi.supplier = %(party_name)s
				AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
			GROUP BY pi_item.item_code  -- Ensures only one row per item
		"""

        data += frappe.db.sql(purchase_query, filters, as_dict=True)

    return data
