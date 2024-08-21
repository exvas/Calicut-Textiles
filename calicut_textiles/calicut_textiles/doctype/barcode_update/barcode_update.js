// Copyright (c) 2024, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Barcode Update", {
	validate: function(frm) {
        frm.doc.barcode_update_item.forEach((doc) => {
            frappe.model.set_value(doc.doctype, doc.name, "custom_barcode_scan", doc.barcode);
        })
    }
});
