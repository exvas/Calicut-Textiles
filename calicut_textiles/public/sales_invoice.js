frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        frm.barcode_scanner = new erpnext.utils.BarcodeScanner({
            frm: frm,
            scan_field_name: 'custom_type_barcode', 
            items_table_name: 'items', 
            barcode_field: 'barcode', 
            serial_no_field: 'serial_no', 
            batch_no_field: 'batch_no', 
            uom_field: 'uom', 
            qty_field: 'custom_net_qty', 
            prompt_qty: true,
            scan_api: "erpnext.stock.utils.scan_barcode" 
        });
        
        frm.get_field('custom_references').grid.cannot_add_rows = true;
    },
    refresh: function(frm){
        if (frm.doc.customer) {
        frappe.call({
            method: 'calicut_textiles.calicut_textiles.events.sales_invoice.set_user_and_customer_and_branch',
            args: {
                user: frappe.session.user
            },
            callback: function (r) {
                if (r.message) {
                    if (r.message.user_series && r.message.user_series.length > 0) {
                        var namingSeries = Array.isArray(r.message.user_series) ? r.message.user_series[0] : r.message.user_series;
                        frm.set_value('naming_series', namingSeries);
                    }
                    if (r.message.default_tax) {
                        frm.set_value('taxes_and_charges', r.message.default_tax);
                    }
                    if (r.message.default_branch) {
                        frm.set_value('custom_branch', r.message.default_branch);
                    }
                    if (r.message.default_price) {
                        frm.set_value('selling_price_list', r.message.default_price);
                    }
                }
            }
        });
    }
    },
    custom_type_barcode: function(frm) {
        frm.barcode_scanner.process_scan().catch(() => {
            frappe.msgprint(__('Unable to process barcode'));
        });
    },
    custom_sales_person: function (frm) {
        validate_employee_selection(frm);
    },
    custom_checked_by: function (frm) {
        validate_employee_selection(frm);
    },
    scan_barcode: function (frm) {
        var barcode = frm.doc.scan_barcode;
        var custom_references = true
        if(frm.doc.custom_references){
            for (var i = 0; i < frm.doc.custom_references.length; i++) {
                    if (frm.doc.custom_references[i].references === barcode) {
                        custom_references = false;
                    }
                }
        }
        if(custom_references){
            var custom_references = frm.doc.custom_references || [];
            frm.add_child('custom_references',{
                'references':barcode,
                'timestamp':frappe.datetime.now_datetime()
            })
            frm.refresh_field('custom_references');
    }
}
});
frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        get_total(frm, cdt, cdn)
    },
    custom_net_qty: function(frm, cdt, cdn) {
        get_net_qty(frm, cdt, cdn)
        get_total(frm, cdt, cdn)
    },
    custom_pcs: function(frm, cdt, cdn) {
        get_net_qty(frm, cdt, cdn)
        get_total(frm, cdt, cdn)
    },
    rate: function(frm, cdt, cdn) {
        get_total(frm, cdt, cdn)
    },
    amount: function(frm, cdt, cdn) {
        get_total(frm, cdt, cdn);
    },
    
});

function validate_employee_selection(frm) {
    if (frm.doc.custom_sales_person && frm.doc.custom_checked_by && frm.doc.custom_sales_person === frm.doc.custom_checked_by) {
        frappe.msgprint({
            title: __('Validation Error'),
            message: __('The Sales Person and Checked By fields cannot have the same employee.'),
            indicator: 'red'
        });
        frm.set_value('custom_checked_by', '');
    }
}

function get_net_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let qty = 0;

    qty = row.custom_net_qty * row.custom_pcs

    frappe.model.set_value(cdt, cdn, "qty", qty);
    
}

function get_total(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.item_tax_template) {
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Item Tax Template",
                name: row.item_tax_template,
            },
            callback: function (r) {
                if (r.message) {
                    let tax_template = r.message;
                    let gst_rate = tax_template.gst_rate || 0;
                    let total = 0;
                    let rate = 0

                    rate = row.rate *  row.qty
                    console.log("rate",rate)

                    total = rate + (rate * gst_rate / 100);
                    console.log("total",total)

                    frappe.model.set_value(cdt, cdn, "custom_total", total);
                } else {
                    frappe.model.set_value(cdt, cdn, "custom_total", total);
                }
            },
        });
    } 
}
