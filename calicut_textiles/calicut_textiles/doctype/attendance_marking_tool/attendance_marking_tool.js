// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance Marking Tool", {
    shift: function(frm) {
      if(frm.doc.shift){
        frm.add_custom_button(__("Get Employee"), function () {
            const shift = frm.doc.shift;

            if (!shift) {
                frappe.msgprint(__("Please select a Shift first."));
                return;
            }

            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Employee",
                    filters: {
                        default_shift: shift,
                        status: "Active"
                    },
                    fields: ["name", "employee_name"]
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        r.message.forEach(emp => {
                            frm.add_child("employee_details", {
                                employee: emp.name,
                                employee_name: emp.employee_name
                            });
                        });

                        frm.refresh_field("employee_details");
                    } else {
                        frappe.msgprint(__("No active employees found for this shift."));
                    }
                }
            });
        }).addClass("btn-primary");
      }
    },
    mark_attendance: function(frm) {
        const selected_rows = frm.fields_dict["employee_details"].grid.get_selected_children();

        if (selected_rows.length === 0) {
            frappe.msgprint(__('Please select at least one row from the employee list table.'));
            return;
        }

        if (!frm.doc.shift) {
            frappe.msgprint(__('Please select a Shift.'));
            return;
        }

        const d = new frappe.ui.Dialog({
            title: 'Mark Attendance',
            fields: [
                {
                    fieldname: 'status',
                    label: 'Status',
                    fieldtype: 'Select',
                    options: ['\n','Present', 'Absent', 'Half Day', 'Work From Home'].join('\n'),
                    reqd: 1
                },
                {
                  fieldname: 'shift',
                  label: 'Shift',
                  fieldtype: 'Data',
                  default: frm.doc.shift,
                  read_only: 1
                }
            ],
            primary_action_label: 'Mark',
            primary_action(values) {
                d.hide();

                selected_rows.forEach(child => {
                    frappe.model.set_value(child.doctype, child.name, "status", values.status);
                    frappe.model.set_value(child.doctype, child.name, "shift", frm.doc.shift);
                    console.log(`Marking Attendance: ${child.employee_name} -> ${values.status}`);
                });

                frm.refresh_field("employee_details");

                frappe.show_alert({
                    message: __('Status "{0}" applied to {1} selected entries.', [values.status, selected_rows.length]),
                    indicator: 'green'
                }, 3);
            }
        });

        d.show();
    }
});
