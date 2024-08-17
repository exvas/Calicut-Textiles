// Copyright (c) 2024, sammish and contributors
// For license information, please see license.txt


frappe.ui.form.on('Barcode Creator', {
    get_item: function(frm) {
        if (!frm.doc.item_group) {
            frappe.msgprint("Please select an item group.");
            return;
        }

        frappe.call({
            method: 'calicut_textiles.calicut_textiles.doctype.barcode_creator.barcode_creator.get_items',  // Ensure the path is correct
            args: {
                item_group: frm.doc.item_group
            },
            callback: function(response) {
                const items = response.message || [];

                // Clear existing items in the table
                frm.set_value('barcode_creator_item', []);

                // Append new items to the barcode_creator_item table
                items.forEach(item => {
                    frm.add_child('barcode_creator_item', {
                        item_code: item.item_code,
                        item_name: item.item_name,
                        item_barcode: item.barcode,  // Ensure this field exists and is correctly named
                        barcode: item.barcode
                    });
                });

                frm.refresh_field('barcode_creator_item');
            }
        });
    }
});


