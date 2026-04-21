frappe.query_reports["Stock Balance Detailed"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: "2025-05-18",
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.nowdate(),
        },
        {
            fieldname: "item_code",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item",
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
        },
        {
            fieldname: "warehouse",
            label: __("Warehouse"),
            fieldtype: "Link",
            options: "Warehouse",
        },
        {
            fieldname: "batch_no",
            label: __("Batch"),
            fieldtype: "Link",
            options: "Batch",
        },
        {
            fieldname: "ageing",
            label: __("Ageing"),
            fieldtype: "Select",
            options: ["", "0-30", "31-60", "61-90", "90+"].join("\n"),
        },
        {
            fieldname: "supplier",
            label: __("Supplier"),
            fieldtype: "Link",
            options: "Supplier",
        },
        {
            fieldname: "supplier_group",
            label: __("Supplier Group"),
            fieldtype: "Link",
            options: "Supplier Group",
        },
        {
            fieldname: "show_batch",
            label: __("Show Batch"),
            fieldtype: "Check",
            default: 1,
        },
    ],
};
