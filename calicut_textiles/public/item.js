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
    }
});

