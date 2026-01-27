// Copyright (c) 2026, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daliy Cash Entry", {
	refresh:function(frm) {
        if (frm.doc.paid_type && frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Payment Entry"),function () {
                frappe.call({
                    method:"calicut_textiles.calicut_textiles.doctype.daliy_cash_entry.daliy_cash_entry.create_payment_entry",
                    args:{daliy_cash_entry:frm.doc.name},
                    callback:function (r) {
                        var doc = frappe.model.sync(r.message);
                        frappe.set_route("Form", doc[0].doctype, doc[0].name);
                    }
                })
            },__("Create"));
        }
        if(frm.doc.docstatus === 1){
            frm.add_custom_button(__("Journal Entry"),function () {
                frappe.call({
                    method:"calicut_textiles.calicut_textiles.doctype.daliy_cash_entry.daliy_cash_entry.create_journal_entry",
                    args:{daliy_cash_entry:frm.doc.name},
                    callback:function (r) {
                        var doc = frappe.model.sync(r.message);
                        frappe.set_route("Form", doc[0].doctype, doc[0].name);
                    }
                })
            },__("Create"));
        }
    },
});
