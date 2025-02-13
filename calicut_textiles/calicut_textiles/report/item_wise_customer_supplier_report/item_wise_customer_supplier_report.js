// frappe.query_reports["Item Wise Customer Supplier Report"] = {
//     "filters": [
//         {
//             "fieldname": "from_date",
//             "label": __("From Date"),
//             "fieldtype": "Date",
//             "default": frappe.datetime.add_months(frappe.datetime.nowdate(), -1),
//             "reqd": 1
//         },
//         {
//             "fieldname": "to_date",
//             "label": __("To Date"),
//             "fieldtype": "Date",
//             "default": frappe.datetime.nowdate(),
//             "reqd": 1
//         },
//         {
//             "fieldname": "party_type",
//             "label": __("Party Type"),
//             "fieldtype": "Select",
//             "options": ["Customer", "Supplier"],
//             "default": "Customer",
//             "reqd": 1,
//             "on_change": function(query_report) {
//                 let party_filter = frappe.query_report.get_filter("party_name");
//                 if (party_filter) {
//                     let party_type = frappe.query_report.get_filter_value("party_type");
//                     party_filter.df.options = party_type === "Customer" ? "Customer" : "Supplier";
//                     party_filter.df.label = party_type === "Customer" ? "Customer Name" : "Supplier Name";
//                     party_filter.refresh();
//                 }
//             }
//         },
//         {
//             "fieldname": "party_name",
//             "label": __("Customer Name"),
//             "fieldtype": "Link",
//             "options": "Customer",
//             "reqd": 1
//         }
//     ]
// };


frappe.query_reports["Item Wise Customer Supplier Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.nowdate(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.nowdate(),
            "reqd": 1
        },
        {
            "fieldname": "party_type",
            "label": __("Party Type"),
            "fieldtype": "Select",
            "options": ["Customer", "Supplier"],
            "default": "Customer",
            "reqd": 1,
            "on_change": function(query_report) {
                let party_filter = frappe.query_report.get_filter("party_name");
                let supplier_filter = frappe.query_report.get_filter("supplier_name");
                let party_type = frappe.query_report.get_filter_value("party_type");

                if (party_filter && supplier_filter) {
                    if (party_type === "Customer") {
                        party_filter.df.options = "Customer";
                        party_filter.df.label = "Customer Name";
                        supplier_filter.df.hidden = false; // Show supplier filter
                    } else {
                        party_filter.df.options = "Supplier";
                        party_filter.df.label = "Supplier Name";
                        supplier_filter.df.hidden = true; // Hide supplier filter when party type is Supplier
                    }

                    party_filter.refresh();
                    supplier_filter.refresh();
                    query_report.refresh();
                }
            }
        },
        {
            "fieldname": "party_name",
            "label": __("Party Name"),
            "fieldtype": "Link",
            "options": "Customer",
            "reqd": 1
        },
        {
            "fieldname": "supplier_name",
            "label": __("Supplier Name"),
            "fieldtype": "Link",
            "options": "Supplier",
            "reqd": 0, // Not required
            "hidden": true // Hidden by default
        }
    ]
};
