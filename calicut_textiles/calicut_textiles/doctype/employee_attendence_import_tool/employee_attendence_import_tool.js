// Copyright (c) 2024, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Attendence Import Tool", {

        refresh: function(frm) {
            if (frm.doc.status == "Pending" || frm.doc.status == "Failed") {
            frm.add_custom_button(__('Import Data'), function() {
                if (!frm.doc.file) {
                    frappe.msgprint(__("Please upload a file"));
                    return;
                }
                if (!frm.doc.payroll_date) {
                    frappe.msgprint(__('Please select a payroll date.'));
                    return;
                }
                
                frappe.call({
                    method: "calicut_textiles.calicut_textiles.doctype.employee_attendence_import_tool.employee_attendence_import_tool.import_attendance_data",
                    args: {
                        file_name: frm.doc.file,
                        docname:  frm.doc.name,
                        payroll_date: frm.doc.payroll_date

                    },
                    callback: function(response) {
                        if (!response.exc) {
                            frappe.msgprint(__("Employee Attendance Data imported successfully!"));
                            frm.reload_doc();
                        }
                    },
                    freeze: true,
                    freeze_message: __("Importing data, please wait..."),
                });
            });
        }
        }
    
    });
    
    
    

