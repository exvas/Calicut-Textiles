frappe.ui.form.on("Consolidate Late Entry", {
    get_employee: function(frm) {
        if (!frm.doc.from_date || !frm.doc.to_date) {
            frappe.msgprint("Please select From Date and To Date.");
            return;
        }

        frappe.call({
            method: "calicut_textiles.calicut_textiles.doctype.consolidate_late_entry.consolidate_late_entry.get_employee_late_entries",
            args: {
                from_date: frm.doc.from_date,
                to_date: frm.doc.to_date
            },
            callback: function(r) {
                if (r.message) {
                    frm.clear_table("late_entry_details");
                    r.message.forEach(function(row) {
                        let child = frm.add_child("late_entry_details");
                        child.employee = row.employee;
                        child.employee_name = row.employee_name;
                        child.shift_type = row.shift_type;
                        child.total_hours = row.total_working_hours;
                        child.salary = row.basic_salary;
                        child.min_salary = row.min_salary;
                        child.consolidat_hour_cutting = row.consolidat_hour_cutting;
                        child.consolidate_amt_cutting = row.consolidate_amt_cutting;
                    });
                    frm.refresh_field("late_entry_details");
                }
            }
        });
    },
    refresh: function(frm) {
      if (!frm.is_new()) {
          frm.fields.forEach(field => {
              if (field.df && field.df.fieldname) {
                  frm.set_df_property(field.df.fieldname, 'read_only', 1);
              }
          });

          frm.disable_save();

          if (!frm.doc.additional_salary_created) {
              frm.add_custom_button(__('Create Additional Salary'), function() {
                  frappe.call({
                      method: "calicut_textiles.calicut_textiles.doctype.consolidate_late_entry.consolidate_late_entry.create_late_early_additional_salary",
                      args: {
                          doc: frm.doc.name
                      },
                      freeze: true,
                      freeze_message: "Creating Additional Salary...",
                      callback: function(r) {
                          if (!r.exc) {
                              frappe.msgprint(__('Additional Salary created successfully'));
                              frm.reload_doc();
                          }
                      }
                  });
              }, __('Create'));
          }
      }
  }

});
