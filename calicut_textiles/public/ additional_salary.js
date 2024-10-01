// frappe.ui.form.on('Additional Salary', {
//     custom_late_early_min: function(frm){
//         base = frappe.db.get_value("Salary Structure Assignment", {"employee": self.employee}, "base", order_by="creation desc")
//         frm.doc.amount = frm.doc.custom_late_early_min * base

//     }
// });