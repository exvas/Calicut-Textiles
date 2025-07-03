// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Consolidate Late Entry", {
    get_employee: function(frm) {
        if (!frm.doc.from_date || !frm.doc.to_date) {
            frappe.msgprint("Please select From Date and To Date.");
            return;
        }

        frappe.call({
            method: "calicut_textiles.calicut_textiles.doctype.consolidate_late_entry.consolidate_late_entry.get_employee_late_entries",
            args: {
                from_date: frm.doc.from_date,
                to_date: frm.doc.to_date
            },
            callback: function(r) {
                if (r.message) {
                    frm.clear_table("late_entry_details");
                    r.message.forEach(function(row) {
                        let child = frm.add_child("late_entry_details", row);
                    });
                    frm.refresh_field("late_entry_details");
                }
            }
        });
    }
});
