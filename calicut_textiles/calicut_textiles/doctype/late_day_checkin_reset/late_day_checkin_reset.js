// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Late Day Checkin Reset", {
	refresh: function(frm) {
		if (frm.is_new()) {
			frm.add_custom_button(__("Get Checkin Details"), function() {
				const today = frappe.datetime.get_today();

				frappe.call({
					method: "frappe.client.get_list",
					args: {
						doctype: "Employee Checkin",
						filters: {
							log_type: "IN",
							time: ["between", [today + " 00:00:00", today + " 23:59:59"]]
						},
						fields: ["name", "employee", "employee_name", "log_type", "time"]
					},
					callback: function(r) {
						if (r.message && r.message.length > 0) {
							$.each(r.message, function(i, emp) {
								let child = frm.add_child("checkin_details");
								child.employee_checkin = emp.name;
								child.employee = emp.employee;
								child.employee_name = emp.employee_name;
								child.log_type = emp.log_type;
								child.time = emp.time;
							});

							frm.refresh_field("checkin_details");

							frappe.show_alert({
								message: __("{0} check-in records added", [r.message.length]),
								indicator: 'green'
							}, 3);
						} else {
							frappe.msgprint(__("No employee check-ins found for today."));
						}
					}
				});
			}).addClass("btn-primary");
		}
		if (frm.doc.docstatus === 1) {
			frm.set_df_property("reset_checkin", "hidden", 1);
		} else {
			frm.set_df_property("reset_checkin", "hidden", 0);
		}
	},
	reset_checkin: function(frm) {
		const selected_rows = frm.fields_dict["checkin_details"].grid.get_selected_children();

		if (selected_rows.length === 0) {
			frappe.msgprint(__('Please select at least one row from the child table.'));
			return;
		}
		
		const d = new frappe.ui.Dialog({
			title: 'Reset Check-in Time for Selected',
			fields: [
				{
					fieldname: 'reset_datetime',
					label: 'Reset Datetime',
					fieldtype: 'Datetime',
					reqd: 1
				},
				{
					fieldname: 'reason',
					label: 'Reason',
					fieldtype: 'Small Text',
					reqd: 1
				}
			],
			primary_action_label: 'Reset',
			primary_action(values) {
				d.hide();

				selected_rows.forEach(child => {
					child.reset_time = values.reset_datetime;
					child.reason = values.reason;
					console.log(`Reset for ${child.employee_name}`);
				});

				frm.refresh_field("checkin_details");

				frappe.show_alert({
					message: __('Reset applied to {0} selected entries.', [selected_rows.length]),
					indicator: 'green'
				}, 3);
			}
		});
		d.show();
	}
});
