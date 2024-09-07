frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
    if (frm.doc.docstatus == 1) {
        frm.add_custom_button(__('Supplier Packing Slip'), function() {
            frappe.call({
                method: "calicut_textiles.calicut_textiles.events.purchase_order.make_supplier_packing_slip",
                args: {
                    purchase_order: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: "Supplier Packing Slip is Created",
                            indicator: 'green'
                        }, 5);
                        frappe.set_route('Form', 'Supplier Packing Slip', r.message);
                    }
                }
            });
        }, __('Create'));
    }
}

})