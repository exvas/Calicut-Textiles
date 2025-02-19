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

        if (item.qty > item.po_actual_qty) {
            frappe.msgprint(__('Quantity is more than in Actual Qty'));
            return; 
        }

        if (item.qty <= 0) {
            frappe.msgprint(__('Quantity is zero, cannot add a new row.'));
            return; 
        }
        
        item.po_remaining_qty = item.po_actual_qty - item.qty;
        // if (item.po_remaining_qty <= 0) {
        //     frappe.msgprint(__('All qty are used, no more rows can be added.'));
        //     return; 
        // }

        let row_index = frm.doc.supplier_packing_slip_item.findIndex(row => row.name === item.name);

        let new_row = frm.fields_dict.supplier_packing_slip_item.grid.add_new_row(row_index +2);

        
        new_row.item_code = item.item_code;
        new_row.qty = 0
        new_row.uom = item.uom;
        new_row.po_ref = item.po_ref;
        new_row.po_actual_qty = item.po_remaining_qty;
        new_row.purchase_order_item = item.purchase_order_item;
        new_row.lot_no = item.lot_no;
    
        frm.refresh_field('supplier_packing_slip_item');
        frappe.model.set_value(cdt, cdn, 'po_remaining_qty', item.po_remaining_qty);
        
    },
    qty: function(frm, cdt, cdn) {
        set_remaining_qty(frm, cdt, cdn)
    },
    pcs: function(frm, cdt, cdn) {
        update_net_qty(frm, cdt, cdn)
    },
    custom_qty: function(frm, cdt, cdn) {
        update_net_qty(frm, cdt, cdn)
    },
})
function set_remaining_qty(frm,cdt,cdn){
    var child = locals[cdt][cdn]
    var po_remaining_qty = 0;
    po_remaining_qty = child.po_actual_qty - child.qty
    frappe.model.set_value(child.doctype, child.name, 'po_remaining_qty', po_remaining_qty);
}

function update_net_qty(frm,cdt,cdn){
    var child = locals[cdt][cdn]
    var qty = 0;
    qty = child.pcs * child.custom_qty
    frappe.model.set_value(child.doctype, child.name, 'qty', qty);
}