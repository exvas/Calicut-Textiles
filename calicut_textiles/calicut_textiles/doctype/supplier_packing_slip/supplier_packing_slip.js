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
    var item = frappe.get_doc(cdt, cdn);

    // validations
    if (item.qty > item.po_actual_qty) {
        frappe.msgprint(__('Quantity is more than in Actual Qty'));
        return;
    }

    if (item.qty <= 0) {
        frappe.msgprint(__('Quantity is zero, cannot add a new row.'));
        return;
    }

    // calculate remaining qty
    let remaining_qty = flt(item.po_actual_qty) - flt(item.qty);

    // update current row first
    frappe.model.set_value(cdt, cdn, 'po_remaining_qty', remaining_qty);

    // -------- create new row (CORRECT WAY) ----------
    let child = frappe.model.add_child(
        frm.doc,
        "Supplier Packing Slip Item",          // Child Doctype name
        "supplier_packing_slip_item"           // Table fieldname
    );

    // populate new row
    child.item_code = item.item_code;
    child.qty = 0;
    child.uom = item.uom;
    child.po_ref = item.po_ref;
    child.po_actual_qty = remaining_qty;
    child.purchase_order_item = item.purchase_order_item;
    child.lot_no = item.lot_no;

    // refresh grid
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
