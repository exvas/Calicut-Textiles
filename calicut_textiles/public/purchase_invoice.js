frappe.ui.form.on('Purchase Invoice', {
});

frappe.ui.form.on("Purchase Invoice Item", {
    custom_pcs: function(frm, cdt, cdn) {
        update_qty(frm, cdt, cdn)
    },
    custom_net_qty: function(frm, cdt, cdn) {
        update_qty(frm, cdt, cdn)
    },
});

function update_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
        row.qty = row.custom_pcs * row.custom_net_qty
        frm.refresh_field("items");
}
