// Copyright (c) 2024, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Employee Advance", {
    setup : function(frm) {
        frm.ignore_doctypes_on_cancel_all = ["Payment Entry"];
    },
    onload(frm){
        frm.get_field('employee_details').grid.cannot_add_rows = true;
    },
	
    refresh: function(frm) {
        frm.set_query("salary_component", function () {
            return {
                filters: {
                    "type": "Deduction"
                }
            };
        });
        if (frm.doc.docstatus == 1 && frm.doc.employee_advance != 1) {
            frm.add_custom_button(__('Employee Advance'), function() {
                frappe.call({
                    method: "calicut_textiles.calicut_textiles.doctype.bulk_employee_advance.bulk_employee_advance.create_employee_advances",
                    freeze: true, 
                    freeze_message: __('Creating Employee Advance and Payment Entry...'),
                    args: { doc_name: frm.doc.name },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Employee Advances created successfully.'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to create Employee Advances. Please try again.'));
                        }
                    }
                });
            }, __('Create'));
        }
        if (frm.doc.docstatus == 1 && frm.doc.employee_advance == 1 && frm.doc.additional_salary != 1) {
            frm.add_custom_button(__('Additional Salary'), function() {
                frappe.call({
                    method: "calicut_textiles.calicut_textiles.doctype.bulk_employee_advance.bulk_employee_advance.create_bulk_additional_salary",
                    freeze: true, 
                    freeze_message: __('Creating Additional Salary...'),
                    args: { doc_name: frm.doc.name },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Employee Additional Salary created successfully.'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to create Additional Salary Please try again.'));
                        }
                    }
                });
            }, __('Create'));
        }
    },
    posting_date: function (frm) {
        table_update(frm)
    },
    company: function (frm) {
        table_update(frm)
    },
});
function table_update(frm) {
    if (frm.doc.company && frm.doc.posting_date) {
        frm.call({
            method: 'get_employees',
            freeze: true, 
            freeze_message: __('Fetching employee details...'), 
            args: {company: frm.doc.company},
            callback: function (r) {console.log(r)
                if (r.message) {
                    frm.clear_table('employee_details'); 
                    r.message.forEach(emp => {
                        let row = frm.add_child('employee_details');
                        row.employee = emp.name;
                        row.designation = emp.designation;
                        row.employee_name = emp.employee_name;
                    });
                    frm.refresh_field('employee_details'); 
                } else {
                    frappe.msgprint(__('No employees found for the selected company.'));
                }
            }
        });
    }
}

