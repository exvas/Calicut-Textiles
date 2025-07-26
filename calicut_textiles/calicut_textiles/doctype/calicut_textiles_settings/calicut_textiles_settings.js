// Copyright (c) 2024, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Calicut Textiles Settings", {
	refresh : function(frm) {
    frm.add_custom_button(__("Reset Late Early"), function () {
      frappe.call({
        method : "calicut_textiles.calicut_textiles.doctype.calicut_textiles_settings.calicut_textiles_settings.reset_late_early",
        callback: function(r){
          if(r.message){
            frappe.msgprint(__("Late/Early entries recalculated successfully."));
          }
        }
      });
    }).addClass("btn-primary");
	},
});
