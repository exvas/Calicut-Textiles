frappe.ui.form.on('Item', {
    has_batch_no: function(frm) {
        if (frm.doc.has_batch_no) {
            frm.set_value('create_new_batch', 1);
        } else {
            frm.set_value('create_new_batch', 0);
        }
    },
    after_save: function(frm) {
        frm.set_df_property('custom_item_short_name', 'hidden', 1);
    },
    validate: function(frm) {
        let value = frm.doc.custom_sanforize;
        if (value && (value < 10 || value > 99)) {
            frappe.msgprint(__('Please enter a two-digit number SANFORIZE+'));
            frappe.validated = false;
        }
    }
});

