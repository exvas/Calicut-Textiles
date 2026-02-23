// Copyright (c) 2024, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Supplier Packing Slip", {
    setup : function(frm) {
        frm.ignore_doctypes_on_cancel_all = ["Serial and Batch Bundle"];
    },
    onload(frm){
        frm.get_field('supplier_packing_slip_item').grid.cannot_add_rows = true;
    },
	refresh(frm) {
        if (frm.doc.docstatus == 1 && frm.doc.purchase_receipt != 1) {
            frm.add_custom_button(__('Purchase Receipt'), function() {
                frappe.call({
                    method: "calicut_textiles.calicut_textiles.doctype.supplier_packing_slip.supplier_packing_slip.make_purchase_receipt",
                    args: {
                        packing_slip: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: "Purchase Receipt is Created",
                                indicator: 'green'
                            }, 5);
                            frappe.set_route('Form', 'Purchase Receipt', r.message);
                        }
                    }
                });
            }, __('Create'));
        }

	},
});
frappe.ui.form.on('Supplier Packing Slip Item', {
    add: function(frm, cdt, cdn) {

        let row = frappe.get_doc(cdt, cdn);

        if (flt(row.qty) <= 0) {
            frappe.msgprint(__('Quantity must be greater than zero.'));
            return;
        }

        if (flt(row.qty) > flt(row.po_actual_qty)) {
            frappe.msgprint(__('Quantity is more than Actual Qty.'));
            return;
        }

        let remaining_qty = flt(row.po_actual_qty) - flt(row.qty);

        frappe.model.set_value(cdt, cdn, 'po_remaining_qty', remaining_qty);

        if (remaining_qty <= 0) {
            frm.refresh_field('supplier_packing_slip_item');
            return;
        }

        let table = frm.doc.supplier_packing_slip_item;
        let current_index = table.findIndex(d => d.name === row.name);

        // create row (adds at last)
        let new_row = frm.add_child('supplier_packing_slip_item');

        // populate values
        new_row.item_code = row.item_code;
        new_row.qty = 0;
        new_row.uom = row.uom;
        new_row.po_ref = row.po_ref;
        new_row.po_actual_qty = remaining_qty;
        new_row.po_remaining_qty = remaining_qty;
        new_row.purchase_order_item = row.purchase_order_item;
        new_row.lot_no = row.lot_no;

        // remove from last position
        table.splice(table.length - 1, 1);

        // insert after current row
        table.splice(current_index + 1, 0, new_row);

        // reindex
        table.forEach((d, i) => d.idx = i + 1);

        frm.refresh_field('supplier_packing_slip_item');
    },

    qty: function(frm, cdt, cdn) {
        set_remaining_qty(frm, cdt, cdn);
    },

    pcs: function(frm, cdt, cdn) {
        update_net_qty(frm, cdt, cdn);
    },

    custom_qty: function(frm, cdt, cdn) {
        update_net_qty(frm, cdt, cdn);
    },
});

function set_remaining_qty(frm, cdt, cdn) {
    var child = locals[cdt][cdn];
    var po_remaining_qty = child.po_actual_qty - child.qty;
    frappe.model.set_value(child.doctype, child.name, 'po_remaining_qty', po_remaining_qty);
}

function update_net_qty(frm, cdt, cdn) {
    let current_row = locals[cdt][cdn];
    let new_qty = current_row.pcs * current_row.custom_qty;
    frappe.model.set_value(current_row.doctype, current_row.name, 'qty', new_qty);

    // Delay to ensure 'qty' value is updated before recalculating remaining quantities
    setTimeout(() => {
        update_remaining_quantities(frm);
    }, 100);
}

function update_remaining_quantities(frm) {
    let rows = frm.doc.supplier_packing_slip_item;
    let po_actual_qty_map = {};
    let used_qty_map = {};

    // Step 1: Prepare map of original po_actual_qty for each PO Item
    rows.forEach(row => {
        if (!po_actual_qty_map[row.purchase_order_item]) {
            po_actual_qty_map[row.purchase_order_item] = row.po_actual_qty;
        }
    });

    // Step 2: Recalculate and update po_remaining_qty for all rows
    rows.forEach((row, idx) => {
        let po_item = row.purchase_order_item;

        if (!used_qty_map[po_item]) {
            used_qty_map[po_item] = 0;
        }

        // Remaining qty before this row
        let remaining_qty = po_actual_qty_map[po_item] - used_qty_map[po_item];

        // Update this row's po_actual_qty (in case it needs correction)
        frappe.model.set_value(row.doctype, row.name, 'po_actual_qty', remaining_qty);

        // Calculate po_remaining_qty after using this row's qty
        let row_qty = row.qty || 0;
        let po_remaining_qty = remaining_qty - row_qty;
        frappe.model.set_value(row.doctype, row.name, 'po_remaining_qty', po_remaining_qty);

        // Update used qty for next rows
        used_qty_map[po_item] += row_qty;
    });
}
