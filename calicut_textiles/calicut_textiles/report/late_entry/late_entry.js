// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["Late Entry"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "100px",
			reqd: 1,
		},
	]
};
