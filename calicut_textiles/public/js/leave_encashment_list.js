frappe.listview_settings['Leave Encashment'] = {
  onload(listview) {
    listview.page.add_inner_button('Create Encashment', () => {
      const dialog = new frappe.ui.Dialog({
        title: 'Create Leave Encashment',
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
            method: "calicut_textiles.calicut_textiles.events.encashment.create_monthly_leave_encashment",
            args: {
              payroll_date: values.payroll_date
            },
            callback(r) {
              if (r.message) {
                frappe.msgprint(__('Leave Encashment Created Successfully.'));
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
