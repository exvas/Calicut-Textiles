// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["Collection Report"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width":150,
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width":150,
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width":150,
		},
		{
			"fieldname": "invoice_id",
			"label": __("Invoice-Id"),
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width":150,
		},
		
		
		

	]
};
