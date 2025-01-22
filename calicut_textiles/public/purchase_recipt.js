frappe.ui.form.on('Purchase Receipt', {
    onload: function(frm) {
        frm.barcode_scanner = new erpnext.utils.BarcodeScanner({
            frm: frm,
            scan_field_name: 'custom_type_barcode', 
            items_table_name: 'items', 
            barcode_field: 'barcode', 
            serial_no_field: 'serial_no', 
            batch_no_field: 'batch_no', 
            uom_field: 'uom', 
            qty_field: 'qty', 
            prompt_qty: true,
            scan_api: "erpnext.stock.utils.scan_barcode" 
        });
    },
    custom_type_barcode: function(frm) {
        frm.barcode_scanner.process_scan().catch(() => {
            frappe.msgprint(__('Unable to process barcode'));
        });
    },
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
        frm.add_custom_button(__('Create Item Prices'), function() {
            frappe.call({
                method: "calicut_textiles.calicut_textiles.purchase_receipt.create_item_price",
                args: {
                    items: JSON.stringify(frm.doc.items)
                },
                callback: function(r) {console.log(r)
                    if (r.message) {
                        frappe.msgprint(__('Item Price updated successfully.'));
                    }
                }
            });
        }, __("Create"));
    },
    before_submit: function(frm) {
        if (!frm.doc.custom_gc_no) {
            frappe.throw(__('LR No is mandatory before submitting the Purchase Receipt.'));
        }
    },
    custom_apply: function(frm) {
        if (!frm.doc.custom_selling_percentage_ && !frm.doc.custom_retail_percentage_) {
            frappe.msgprint(__('Please enter at least one percentage value before applying.'));
            return;
        }
    
        frm.doc.items.forEach(row => {
            if (frm.doc.custom_selling_percentage_ !== undefined) {
                frappe.model.set_value(row.doctype, row.name, 'custom_selling_percentage', frm.doc.custom_selling_percentage_);
            }
            if (frm.doc.custom_retail_percentage_ !== undefined) {
                frappe.model.set_value(row.doctype, row.name, 'custom_retail_percentage_', frm.doc.custom_retail_percentage_);
            }
        });
        frappe.msgprint(__('Percentage applied successfully.'));
    
        frm.refresh_field('items');
    },
    custom_clear: function(frm) {
        frm.set_value("custom_selling_percentage_","")
        frm.set_value("custom_retail_percentage_","")
    
        frm.doc.items.forEach(row => {
                frappe.model.set_value(row.doctype, row.name, 'custom_selling_percentage', " ");
          
                frappe.model.set_value(row.doctype, row.name, 'custom_retail_percentage_', " ");
                
                frappe.model.set_value(row.doctype, row.name, 'custom_selling_rate', " ");
          
                frappe.model.set_value(row.doctype, row.name, 'custom_retail_rate', " ");
            
        });
        frappe.msgprint(__('Percentage Cleared'));
    
        frm.refresh_field('items');
    },

});

frappe.ui.form.on("Purchase Receipt Item", {
    custom_pcs: function(frm, cdt, cdn) {
        update_qty(frm, cdt, cdn)
    },
    custom_net_qty: function(frm, cdt, cdn) {
        update_qty(frm, cdt, cdn)
    },
    custom_selling_percentage: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.rate && row.custom_selling_percentage) {
            frappe.model.set_value(cdt, cdn, 'custom_selling_rate', 
                row.rate + (row.rate * row.custom_selling_percentage / 100));
        }
    },
    custom_retail_percentage_: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.rate && row.custom_retail_percentage_) {
            frappe.model.set_value(cdt, cdn, 'custom_retail_rate', 
                row.rate + (row.rate * row.custom_retail_percentage_ / 100));
        }
    },
    custom_selling_rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.rate && row.custom_selling_rate) {
            frappe.model.set_value(cdt, cdn, 'custom_selling_percentage', 
                ((row.custom_selling_rate - row.rate) / row.rate) * 100);
        }
    },
    custom_retail_rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.rate && row.custom_retail_rate) {
            frappe.model.set_value(cdt, cdn, 'custom_retail_percentage_', 
                ((row.custom_retail_rate - row.rate) / row.rate) * 100);
        }
    }


});

function update_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
        row.qty = row.custom_pcs * row.custom_net_qty
        frm.refresh_field("items");
}