// Copyright (c) 2024, sammish and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Rack Update", {
// 	refresh(frm) {
//         console.log("ffffffffffffffffffffffffffffffffffffffff")

// 	},
// });
// your_app/your_app/doctype/rack_update/rack_update.js

// frappe.ui.form.on('Rack Update', {
//     refresh(frm) {

//         // Add custom button
//         frm.add_custom_button(__('Get Items'), function() {
//             if (!frm.doc.item_group) {
//                 frappe.msgprint(__('Please select an Item Group'));
//                 return;
//             }

//             // Call the server-side method to fetch items
//             frappe.call({
//                 method: 'calicut_textiles.calicut_textiles.doctype.rack_update.rack_update.get_items',
                
//                 args: {
//                     item_group: frm.doc.item_group
//                 },
//                 callback: function(r) {
//                     if (r.message) {
//                         // Clear the child table
//                         frm.clear_table('rack_item');

//                         // Add fetched items to the child table
//                         r.message.forEach(item => {
//                             let row = frm.add_child('rack_item');
//                             row.item_code = item.item_code;
//                             row.item_name = item.item_name;
//                             row.uom = item.stock_uom;
//                             row.rack = item.custom_rak_location;
//                         });

//                         // Refresh the table
//                         frm.refresh_field('rack_item');
//                     }
//                 }
//             });
//         });
//     }
// });

// frappe.ui.form.on('Rack Update', {
//     refresh(frm) {

//         // Add custom button
//         frm.add_custom_button(__('Get Items'), function() {
//             if (!frm.doc.item_group) {
//                 frappe.msgprint(__('Please select an Item Group'));
//                 return;
//             }

//             if (!frm.doc.warehouse) {
//                 frappe.msgprint(__('Please select a Warehouse'));
//                 return;
//             }

//             // Call the server-side method to fetch items
//             frappe.call({
//                 method: 'calicut_textiles.calicut_textiles.doctype.rack_update.rack_update.get_items',
//                 args: {
//                     item_group: frm.doc.item_group,
//                     warehouse: frm.doc.warehouse
//                 },
//                 callback: function(r) {
//                     if (r.message) {
//                         // Clear the child table
//                         frm.clear_table('rack_item');

//                         // Add fetched items to the child table
//                         r.message.forEach(item => {
//                             let row = frm.add_child('rack_item');
//                             row.item_code = item.item_code;
//                             row.item_name = item.item_name;
//                             row.uom = item.stock_uom;
//                             row.rack = item.custom_rak_location;
//                             row.available_qty = item.actual_qty; // Add the available quantity
//                         });

//                         // Refresh the table
//                         frm.refresh_field('rack_item');
//                     }
//                 }
//             });
//         });
//     }
// });
frappe.ui.form.on('Rack Update', {
    refresh(frm) {
        if (frm.doc.docstatus !== 1) {
            // Add custom button
            frm.add_custom_button(__('Get Items'), function() {
                if (!frm.doc.item_group) {
                    frappe.msgprint(__('Please select an Item Group'));
                    return;
                }

                if (!frm.doc.warehouse) {
                    frappe.msgprint(__('Please select a Warehouse'));
                    return;
                }

                // Call the server-side method to fetch items
                frappe.call({
                    method: 'calicut_textiles.calicut_textiles.doctype.rack_update.rack_update.get_items',
                    args: {
                        item_group: frm.doc.item_group,
                        warehouse: frm.doc.warehouse
                    },
                    callback: function(r) {
                        if (r.message) {
                            // Clear the child table
                            frm.clear_table('rack_item');

                            // Add fetched items to the child table
                            r.message.forEach(item => {
                                let row = frm.add_child('rack_item');
                                row.item_code = item.item_code;
                                row.item_name = item.item_name;
                                row.uom = item.stock_uom;
                                row.rack = item.custom_rak_location;
                                row.available_qty = item.actual_qty; // Add the available quantity
                            });

                            // Refresh the table
                            frm.refresh_field('rack_item');
                        }
                    }
                });
            });
        }
    },
    before_submit(frm) {
        frappe.call({
            method: 'calicut_textiles.calicut_textiles.doctype.rack_update.rack_update.update_item_rack_locations',
            args: {
                items: frm.doc.rack_item
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__(r.message));
                }
            }
        });
    }
});
