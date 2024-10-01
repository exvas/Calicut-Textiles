frappe.ui.form.on('Salary Slip', {
    validate: function (frm) {
        calculate_deducted_gross(frm)
    }

})


frappe.ui.form.on('Salary Details', {
    late_early: function(frm, cdt, cdn) {
        calculate_deducted_gross(frm);
    }
});

function calculate_deducted_gross(frm) {
    let total_deducted_amount = 0;

    frappe.db.get_value("Salary Structure Assignment", {"employee": frm.doc.employee}, "base")
        .then(r => {
            if (r.message) {
                let base_amount = flt(r.message.base);  // Get the base amount

                // Calculate the total deductions
                $.each(frm.doc.deductions || [], function(i, row) {
                    if (row.custom_is_late_early) {
                        total_deducted_amount += flt(row.amount);
                    }
                });

                // Subtract the total deducted amount from the base amount
                let final_amount = base_amount - total_deducted_amount;

                // Update the custom field with the deducted gross value
                frm.set_value('custom_deducted_gross', final_amount);
            }
        });
}

