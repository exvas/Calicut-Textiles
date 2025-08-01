frappe.listview_settings['Employee Checkin'] = {
    onload(listview) {
        listview.page.add_inner_button('Recalculation', () => {
            const dialog = new frappe.ui.Dialog({
                title: 'Recalculate Late/Early',
                fields: [
                    {
                        label: 'From Date',
                        fieldname: 'from_date',
                        fieldtype: 'Date',
                        reqd: true
                    },
                    {
                        label: 'To Date',
                        fieldname: 'to_date',
                        fieldtype: 'Date',
                        reqd: true
                    }
                ],
                primary_action_label: 'Recalculate',
                primary_action(values) {
                    dialog.hide();
                    frappe.call({
                        method: 'calicut_textiles.calicut_textiles.doctype.calicut_textiles_settings.calicut_textiles_settings.reset_late_early',
                        args: {
                            from_date: values.from_date,
                            to_date: values.to_date
                        },
                        freeze: true,
                        freeze_message: "Recalculating late/early entries...",
                        callback(r) {
                            if (r.message) {
                                frappe.msgprint(__('Late/Early entries recalculated successfully.'));
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
