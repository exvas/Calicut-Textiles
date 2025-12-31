frappe.ui.form.on("Payroll Entry", {
    refresh(frm) {
        if (frm.doc.docstatus === 0&&!frm.is_new())  {
            frm.add_custom_button("Process Attendance & OT", () => {
                if (!frm.doc.employees || frm.doc.employees.length === 0) {
                    frappe.msgprint("No employees found in this Payroll Entry.");
                    return;
                }

                frappe.call({
                    method: "calicut_textiles.public.python.payroll_entry.enqueue_payroll_processing",
                    args: {
                        payroll_entry: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Processing employees from Payroll Entry..."
                });
            });
        }
    }
});
