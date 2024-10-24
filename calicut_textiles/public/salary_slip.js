frappe.ui.form.on('Salary Slip', {
    employee: function(frm) {
        if(frm.doc.employee && frm.doc.start_date) {
            frm.trigger("deducted_gross");  
        }
    },

    start_date: function(frm) {
        if(frm.doc.employee && frm.doc.start_date) {
            frm.trigger("deducted_gross");  
        }
    },

    end_date: function(frm) {
        if(frm.doc.employee && frm.doc.start_date) {
            frm.trigger("deducted_gross");  
        }
    },


    deducted_gross: function(frm) {
            frappe.call({
                method: "calicut_textiles.calicut_textiles.events.salary_slip.calculate_deducted_gross",
                args: {
                    employee: frm.doc.employee,
                    start_date: frm.doc.start_date  
                },
                callback: function(r) {
                    if(r.message) {
                        let deducted_gross = r.message;
                        frm.set_value('custom_deducted_gross', deducted_gross);
                        frm.set_value('custom_deducted_per_day', deducted_gross / frm.doc.payment_days);
                        frm.set_value('custom_deducted_basic', deducted_gross * 62.5 / 100);
                        frm.set_value('custom_deducted_da', deducted_gross * 40 / 100);
                    }
                }
            });
    
    }
});
