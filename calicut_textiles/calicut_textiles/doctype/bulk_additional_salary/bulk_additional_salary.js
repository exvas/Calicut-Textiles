// Copyright (c) 2024, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Additional Salary", {
    onload(frm){
        frm.get_field('employee_advance_details').grid.cannot_add_rows = true;
    },
	refresh(frm) {
        frm.set_query("salary_component", function () {
            return {
                filters: {
                    "type": "Deduction"
                }
            };
        });
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__('Create Additional Salary'), function() {
                frappe.call({
                    method: "calicut_textiles.calicut_textiles.doctype.bulk_additional_salary.bulk_additional_salary.create_additional_salary",
                    args: { doc_name: frm.doc.name },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Additional Salary created successfully.'));
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to create Additional Salary . Please try again.'));
                        }
                    }
                });
            });
        }

	},
    posting_date: function (frm) {
        if (frm.doc.company && frm.doc.posting_date) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Employee Advance',
                    filters: {
                        company: frm.doc.company,
                        posting_date: frm.doc.posting_date
                    },
                    fields: ['name','advance_amount', 'employee', 'employee_name']
                },
                callback: function (r) {
                    if (r.message) {
                        frm.clear_table('employee_advance_details'); 
                        r.message.forEach(emp => {
                            let row = frm.add_child('employee_advance_details');
                            row.employee = emp.employee;
                            row.employee_name = emp.employee_name;
                            row.employee_advance = emp.name;
                            row.advance_amount = emp.advance_amount;
                        });
                        frm.refresh_field('employee_advance_details'); 
                    } else {
                        frappe.msgprint(__('No employees Advances found for the selected company.'));
                    }
                }
            });
        }
    },
});
