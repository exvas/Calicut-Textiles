frappe.listview_settings['Additional Salary'] = {
  onload(listview) {
    listview.page.add_inner_button('Create OT Salary', () => {
      const dialog = new frappe.ui.Dialog({
        title: 'Create Additional Salary',
        fields: [
          {
              label: 'Payroll Date',
              fieldname: 'payroll_date',
              fieldtype: 'Date',
              reqd: true
          }
        ],
        primary_action_label: 'Create',
        primary_action(values) {
          dialog.hide();
          frappe.call({
            method: "calicut_textiles.calicut_textiles.events.employee_checkin.create_overtime_additional_salary",
            args: {
              payroll_date: values.payroll_date
            },
            callback(r) {
              if (r.message) {
                frappe.msgprint(__('Additional Salary Created Successfully.'));
                listview.refresh();
              }
            }
          });
        }
      });
      dialog.show();
    });
  }
};
