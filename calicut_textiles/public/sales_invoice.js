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
    custom_sales_person: function (frm) {
        validate_employee_selection(frm);
    },
    custom_checked_by: function (frm) {
        validate_employee_selection(frm);
    }
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