frappe.ui.form.on('Purchase Receipt', {
    before_save: function(frm) {
        frm.doc.items.forEach((doc) => {
            frappe.model.set_value(doc.doctype, doc.name, "custom_barcode_scan", doc.barcode);
        })
    },
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.docstatus ==1 && !frm.doc.custom_landed_cost){
            frm.add_custom_button(__('Landed Cost Voucher'), function() {
                frappe.call({
                    method: "calicut_textiles.calicut_textiles.purchase_receipt.create_landed_cost_voucher",
                    args: {
                        pr: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__('Landed Cost Voucher {0} created successfully', [r.message]));
                        }
                    }
                });
            },__('Create')); 
        }
    }

});