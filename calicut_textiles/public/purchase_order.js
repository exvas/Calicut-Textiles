frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
    if (frm.doc.docstatus == 1 && frm.doc.status != "To Bill") {
        frm.add_custom_button(__('Supplier Packing Slip'), function() {
            frappe.call({
                method: "calicut_textiles.calicut_textiles.events.purchase_order.make_supplier_packing_slip",
                args: {
                    purchase_order: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: "Supplier Packing Slip is Created",
                            indicator: 'green'
                        }, 5);
                        frappe.set_route('Form', 'Supplier Packing Slip', r.message);
                    }
                }
            });
        }, __('Create'));
    }
    if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Send via WhatsApp'), function() {
            show_whatsapp_options_dialog(frm);
        }, __('Create'));

        // Add button to view saved PDF files
        frm.add_custom_button(__('View Saved PDFs'), function() {
            show_saved_files_dialog(frm);
        }, __('Create'));

        // Style the buttons after they're created
        setTimeout(function() {
            $('.btn-default[data-label*="WhatsApp"]').addClass('btn-whatsapp').removeClass('btn-default');
        }, 100);
    }
},
supplier : function(frm){
  if (frm.doc.supplier) {
      get_supplier_mobile(frm.doc.supplier);
  }
},
onload: function(frm) {
  if (!$('#whatsapp-custom-css').length) {
      $('head').append('<style id="whatsapp-custom-css">' +
          '.btn-success[data-label*="WhatsApp"], .btn-whatsapp {' +
              'background: #25D366 !important;' +
              'border-color: #25D366 !important;' +
              'color: white !important;' +
              'font-weight: 500;' +
          '}' +
          '.btn-success[data-label*="WhatsApp"]:hover, .btn-whatsapp:hover {' +
              'background: #128C7E !important;' +
              'border-color: #128C7E !important;' +
              'transform: translateY(-1px);' +
              'box-shadow: 0 4px 8px rgba(37, 211, 102, 0.3);' +
          '}' +
          '.whatsapp-preview {' +
              'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;' +
              'line-height: 1.4;' +
              'background: #f0f0f0;' +
              'padding: 15px;' +
              'border-radius: 8px;' +
              'margin: 10px 0;' +
              'border-left: 4px solid #25D366;' +
          '}' +
          '.whatsapp-dialog .modal-dialog {' +
              'max-width: 700px;' +
          '}' +
          '.mobile-input-group {' +
              'position: relative;' +
              'margin-bottom: 15px;' +
          '}' +
          '.mobile-input-group input {' +
              'padding-left: 45px;' +
          '}' +
          '.mobile-prefix {' +
              'position: absolute;' +
              'left: 10px;' +
              'top: 50%;' +
              'transform: translateY(-50%);' +
              'color: #666;' +
              'font-weight: 500;' +
          '}' +
          '.whatsapp-icon {' +
              'display: inline-block;' +
              'width: 16px;' +
              'height: 16px;' +
              'margin-right: 8px;' +
              'vertical-align: text-bottom;' +
          '}' +
          '.pdf-files-list {' +
              'background: #f8f9fa;' +
              'padding: 10px;' +
              'border-radius: 5px;' +
              'margin-top: 10px;' +
              'border: 1px solid #dee2e6;' +
          '}' +
          '.file-item {' +
              'display: flex;' +
              'justify-content: space-between;' +
              'align-items: center;' +
              'padding: 5px 0;' +
              'border-bottom: 1px solid #dee2e6;' +
          '}' +
          '.file-item:last-child {' +
              'border-bottom: none;' +
          '}' +
          '.file-actions {' +
              'display: flex;' +
              'gap: 8px;' +
          '}' +
          '.format-info {' +
              'background: #f8f9fa;' +
              'padding: 8px 12px;' +
              'border-radius: 4px;' +
              'margin-top: 5px;' +
              'font-size: 12px;' +
              'color: #666;' +
          '}' +
          '.btn-resend {' +
              'background: #25D366 !important;' +
              'border-color: #25D366 !important;' +
              'color: white !important;' +
              'font-size: 12px;' +
          '}' +
          '.btn-resend:hover {' +
              'background: #128C7E !important;' +
              'border-color: #128C7E !important;' +
          '}' +
          '.resend-dialog .modal {' +
              'z-index: 1060 !important;' +
          '}' +
          '.resend-dialog .modal-backdrop {' +
              'z-index: 1055 !important;' +
          '}' +
      '</style>');
  }
}

});


function show_whatsapp_options_dialog(frm) {
    // First, get available options and current settings
    get_print_formats_letterheads_and_settings(function(print_formats, letterheads, current_print_format, current_letterhead) {
        // Create options dialog
        var dialog_title = '<svg class="whatsapp-icon" viewBox="0 0 24 24" fill="#25D366">' +
            '<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893A11.821 11.821 0 0020.863 3.486"/>' +
            '</svg>' +
            'Choose WhatsApp Option';

        var dialog = new frappe.ui.Dialog({
            title: dialog_title,
            fields: [
                {
                    label: 'Supplier Mobile Number',
                    fieldname: 'mobile_number',
                    fieldtype: 'Data',
                    reqd: 1,
                    description: 'Enter mobile number with country code (e.g., +91 xxxxxxxxxx)'
                },
                {
                    label: 'Print Format',
                    fieldname: 'print_format',
                    fieldtype: 'Select',
                    options: print_formats,
                    default: current_print_format,
                    description: 'Select print format for the PDF purchase order'
                },
                {
                    label: 'Letterhead',
                    fieldname: 'letterhead',
                    fieldtype: 'Select',
                    options: letterheads,
                    default: current_letterhead,
                    description: 'Select letterhead for the PDF purchase order'
                },
                {
                    label: 'WhatsApp Option',
                    fieldname: 'whatsapp_option',
                    fieldtype: 'Select',
                    options: ['PDF with Download Link', 'PDF for Manual Attachment'],
                    default: 'PDF with Download Link',
                    description: 'Choose how to send the PDF'
                },
                {
                    label: 'Preview',
                    fieldname: 'message_preview',
                    fieldtype: 'HTML',
                    options: '<div class="whatsapp-preview">Loading preview...</div>'
                }
            ],
            primary_action_label: 'Generate WhatsApp Link',
            primary_action: function(values) {
                if (values.whatsapp_option === 'PDF for Manual Attachment') {
                    send_whatsapp_with_attachment(frm, values.mobile_number, values.print_format, values.letterhead, dialog);
                } else {
                    send_whatsapp_invoice(frm, values.mobile_number, values.print_format, values.letterhead, dialog);
                }
            },
            secondary_action_label: 'Get Supplier Mobile',
            secondary_action: function() {
                get_supplier_mobile(frm.doc.supplier, dialog);
            }
        });

        // Custom styling for mobile input
        dialog.$wrapper.addClass('whatsapp-dialog');

        // Add styling and event handlers
        setTimeout(function() {
            var mobileField = dialog.get_field('mobile_number');
            var printFormatField = dialog.get_field('print_format');
            var letterheadField = dialog.get_field('letterhead');
            var optionField = dialog.get_field('whatsapp_option');

            if (mobileField) {
                mobileField.$input.wrap('<div class="mobile-input-group"></div>');
                mobileField.$input.parent().prepend('<span class="mobile-prefix">📱</span>');

                // Update preview when mobile number changes
                mobileField.$input.on('input', function() {
                    update_message_preview_enhanced(frm, dialog);
                });
            }

            if (printFormatField) {
                // Add print format info below the field
                printFormatField.$wrapper.append('<div class="format-info">' +
                    '📝 This print format will be used to generate the PDF purchase order. Default is set from Whatsapp Settings.' +
                    '</div>');

                printFormatField.$input.on('change', function() {
                    update_message_preview_enhanced(frm, dialog);
                });
            }

            if (letterheadField) {
                // Add letterhead info below the field
                letterheadField.$wrapper.append('<div class="format-info">' +
                    '💡 This letterhead will be used in the generated PDF purchase order. Default is set from Whatsapp Settings.' +
                    '</div>');

                letterheadField.$input.on('change', function() {
                    update_message_preview_enhanced(frm, dialog);
                });
            }

            if (optionField) {
                optionField.$input.on('change', function() {
                    update_message_preview_enhanced(frm, dialog);
                });
            }
        }, 100);

        dialog.show();

        // Load supplier mobile if available
        if (frm.doc.supplier) {
            get_supplier_mobile(frm.doc.supplier, dialog);
        }

        // Initial preview
        setTimeout(function() {
            update_message_preview_enhanced(frm, dialog);
        }, 200);
    });
}

function get_print_formats_letterheads_and_settings(callback) {
    // Get available print formats
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Print Format',
            filters: {
                'doc_type': 'Purchase Order'
            },
            fields: ['name'],
            order_by: 'name'
        },
        callback: function(pf_response) {
            var print_formats = ['Standard'];  // Start with Standard option
            if (pf_response.message) {
                print_formats = print_formats.concat(pf_response.message.map(function(pf) { return pf.name; }));
            }

            // Get available letterheads
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Letter Head',
                    fields: ['name'],
                    order_by: 'name'
                },
                callback: function(lh_response) {
                    var letterheads = [''];  // Start with empty option
                    if (lh_response.message) {
                        letterheads = letterheads.concat(lh_response.message.map(function(lh) { return lh.name; }));
                    }

                    // Get current settings from Whatsapp Settings
                    frappe.call({
                        method: 'calicut_textiles.calicut_textiles.events.purchase_order.get_whatsapp_settings',
                        callback: function(settings_response) {
                            var current_print_format = 'Standard';
                            var current_letterhead = '';
                            if (settings_response.message && settings_response.message.success) {
                                current_print_format = settings_response.message.print_format || 'Standard';
                                current_letterhead = settings_response.message.letterhead || '';
                            }
                            callback(print_formats, letterheads, current_print_format, current_letterhead);
                        }
                    });
                }
            });
        }
    });
}

function show_saved_files_dialog(frm) {
    // Show dialog with saved PDF files
    frappe.call({
        method: 'calicut_textiles.calicut_textiles.events.purchase_order.get_saved_invoice_files',
        args: {
            docname: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                var files = r.message.files;
                var files_html = '';

                if (files.length > 0) {
                    files_html = '<div class="pdf-files-list">';
                    files_html += '<h6>📄 Saved PDF Files:</h6>';

                    files.forEach(function(file) {
                        files_html += '<div class="file-item">' +
                            '<div>' +
                                '<strong>' + file.file_name + '</strong><br>' +
                                '<small class="text-muted">Created: ' + frappe.datetime.str_to_user(file.creation) + '</small>' +
                            '</div>' +
                            '<div class="file-actions">' +
                                '<a href="' + file.file_url + '" target="_blank" class="btn btn-sm btn-primary">' +
                                    '📥 Download' +
                                '</a>' +
                                '<button class="btn btn-sm btn-resend" ' +
                                        'data-file-id="' + file.name + '" ' +
                                        'data-file-name="' + file.file_name + '" ' +
                                        'data-file-url="' + file.file_url + '">' +
                                    '📱 Resend' +
                                '</button>' +
                            '</div>' +
                        '</div>';
                    });

                    files_html += '</div>';
                } else {
                    files_html = '<p class="text-muted">No saved PDF files found for this purchase order.</p>';
                }

                var files_dialog = frappe.msgprint({
                    title: 'Purchase Order PDFs',
                    message: files_html,
                    wide: true
                });

                // Add event handler for resend buttons after the dialog is shown
                setTimeout(function() {
                    $('.btn-resend').off('click').on('click', function() {
                        var fileId = $(this).data('file-id');
                        var fileName = $(this).data('file-name');
                        var fileUrl = $(this).data('file-url');

                        // Don't close the dialog, just open resend on top
                        resend_saved_pdf(fileId, fileName, fileUrl);
                    });
                }, 100);
            }
        }
    });
}

// Make resend function globally accessible
window.resend_saved_pdf = function(file_id, file_name, file_url) {
    // Show resend dialog for saved PDF
    var resend_dialog = new frappe.ui.Dialog({
        title: '📱 Resend PDF: ' + file_name,
        fields: [
            {
                label: 'Supplier Mobile Number',
                fieldname: 'mobile_number',
                fieldtype: 'Data',
                reqd: 1,
                description: 'Enter mobile number with country code (e.g., +91 xxxxxxxxxx)'
            },
            {
                label: 'WhatsApp Option',
                fieldname: 'whatsapp_option',
                fieldtype: 'Select',
                options: ['PDF with Download Link', 'PDF for Manual Attachment'],
                default: 'PDF with Download Link',
                description: 'Choose how to send the PDF'
            },
            {
                label: 'Preview',
                fieldname: 'message_preview',
                fieldtype: 'HTML',
                options: '<div class="whatsapp-preview">Loading preview...</div>'
            }
        ],
        primary_action_label: 'Send WhatsApp',
        primary_action: function(values) {
            send_existing_pdf_via_whatsapp(cur_frm, values.mobile_number, values.whatsapp_option, file_name, file_url, resend_dialog);
        }
    });

    resend_dialog.show();

    // Force the resend dialog to appear on top with much higher z-index
    setTimeout(function() {
        // Get the highest z-index currently on page
        var maxZ = Math.max.apply(null,
            $('*').map(function() {
                return parseInt($(this).css('z-index')) || 0;
            }).get()
        );

        // Set resend dialog z-index much higher
        var newZIndex = Math.max(maxZ + 100, 9999);

        resend_dialog.$wrapper.css({
            'z-index': newZIndex,
            'position': 'relative'
        });

        resend_dialog.$wrapper.find('.modal').css({
            'z-index': newZIndex + 1,
            'position': 'fixed'
        });

        // Handle backdrop - make it appear between base dialog and resend dialog
        var $backdrop = $('.modal-backdrop').last();
        if ($backdrop.length) {
            $backdrop.css('z-index', newZIndex - 1);
        }

        // Ensure the dialog is visible and on top
        resend_dialog.$wrapper.show();
    }, 100);

    // Add event handlers for resend dialog
    setTimeout(function() {
        var mobileField = resend_dialog.get_field('mobile_number');
        var optionField = resend_dialog.get_field('whatsapp_option');

        if (mobileField) {
            mobileField.$input.wrap('<div class="mobile-input-group"></div>');
            mobileField.$input.parent().prepend('<span class="mobile-prefix">📱</span>');

            mobileField.$input.on('input', function() {
                update_resend_preview(cur_frm, resend_dialog, file_name);
            });
        }

        if (optionField) {
            optionField.$input.on('change', function() {
                update_resend_preview(cur_frm, resend_dialog, file_name);
            });
        }
    }, 150);

    // Load supplier mobile if available
    if (cur_frm.doc.supplier) {
        get_supplier_mobile(cur_frm.doc.supplier, resend_dialog);
    }

    // Initial preview
    setTimeout(function() {
        update_resend_preview(cur_frm, resend_dialog, file_name);
    }, 200);
};

function resend_saved_pdf(file_id, file_name, file_url) {
    // Call the global function
    window.resend_saved_pdf(file_id, file_name, file_url);
}

function update_resend_preview(frm, dialog, file_name) {
    var mobile_number = dialog.get_value('mobile_number');
    var option = dialog.get_value('whatsapp_option');
    var purchase_order = frm.doc;

    var message_lines = [
        "Good day! 👋",
        "",
        "Thank you for your purchase!",
        "",
        "*Purchase Order Details:*",
        "Purchase Order: #" + purchase_order.name,
        "Date: " + frappe.datetime.str_to_user(purchase_order.transaction_date),
        "Amount: " + purchase_order.currency + " " + format_currency(purchase_order.grand_total, purchase_order.currency),
        "",
        "Supplier: " + (purchase_order.supplier_name || purchase_order.supplier),
    ];

    // if (purchase_order.delivery_date && purchase_order.outstanding_amount > 0) {
    //     message_lines.push("Due Date: " + frappe.datetime.str_to_user(purchase_order.delivery_date));
    //     message_lines.push("Outstanding: " + purchase_order.currency + " " + format_currency(purchase_order.outstanding_amount, purchase_order.currency));
    // }

    message_lines.push("");

    if (option === 'PDF for Manual Attachment') {
        message_lines.push("📄 Please find your purchase order PDF attached below.");
    } else {
        message_lines.push("Download purchase Order: [PDF Link will be added here]");
    }

    message_lines.push("");
    message_lines.push("Thank you for your business! 🙏");

    var preview_html = '<div class="whatsapp-preview">' +
        '<strong>📱 WhatsApp Message Preview:</strong>' +
        '<div style="margin-top: 10px; white-space: pre-line; font-size: 14px;">' +
        message_lines.join('\n') +
        '</div>';

    if (mobile_number) {
        preview_html += '<div style="margin-top: 10px; color: #666; font-size: 12px;">' +
            'Will be sent to: <strong>' + mobile_number + '</strong><br>' +
            'Mode: <strong>' + option + '</strong><br>' +
            'File: <strong>' + file_name + '</strong><br>' +
            'Using existing saved PDF' +
            '</div>';
    }

    preview_html += '</div>';

    dialog.set_df_property('message_preview', 'options', preview_html);
}

function send_existing_pdf_via_whatsapp(frm, mobile_number, option, file_name, file_url, dialog) {
    if (!mobile_number) {
        frappe.msgprint('Please enter mobile number');
        return;
    }

    frappe.call({
        method: 'calicut_textiles.calicut_textiles.events.purchase_order.resend_existing_pdf_whatsapp',
        args: {
            docname: frm.doc.name,
            mobile_number: mobile_number,
            option: option,
            file_name: file_name,
            file_url: file_url
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                dialog.hide();

                if (option === 'PDF for Manual Attachment') {
                    var attachment_message = '<div style="padding: 20px;">' +
                        '<div style="font-size: 16px; margin-bottom: 20px;">' +
                            '📱 Choose your preferred method:' +
                        '</div>' +
                        '<div style="margin-bottom: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px;">' +
                            '<strong>Option 1: WhatsApp Web (Recommended)</strong><br>' +
                            '<a href="' + r.message.whatsapp_web_url + '" target="_blank" ' +
                               'class="btn btn-success" ' +
                               'style="background: #25D366; border-color: #25D366; margin-top: 10px;">' +
                                '📱 Open WhatsApp Web' +
                            '</a>' +
                        '</div>' +
                        '<div style="margin-bottom: 20px; padding: 15px; background: #f0f8ff; border-radius: 5px;">' +
                            '<strong>Option 2: Mobile WhatsApp</strong><br>' +
                            '<a href="' + r.message.whatsapp_mobile_url + '" target="_blank" ' +
                               'class="btn btn-primary" ' +
                               'style="margin-top: 10px;">' +
                                '📱 Open Mobile WhatsApp' +
                            '</a>' +
                        '</div>' +
                        '<div style="margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 5px;">' +
                            '<strong>📄 PDF File:</strong><br>' +
                            '<a href="' + file_url + '" target="_blank" style="color: #666;">' +
                                '📥 Download ' + file_name +
                            '</a>' +
                        '</div>' +
                    '</div>';

                    frappe.msgprint({
                        title: 'WhatsApp Ready - Resend PDF',
                        message: attachment_message,
                        wide: true
                    });
                } else {
                    var link_message = '<div style="text-align: center; padding: 20px;">' +
                        '<div style="font-size: 16px; margin-bottom: 20px;">' +
                            'Your WhatsApp message is ready! 🎉' +
                        '</div>' +
                        '<div style="margin-bottom: 20px;">' +
                            '<a href="' + r.message.whatsapp_url + '" target="_blank" ' +
                               'class="btn btn-success btn-lg" ' +
                               'style="background: #25D366; border-color: #25D366; text-decoration: none;">' +
                                '📱 Open WhatsApp' +
                            '</a>' +
                        '</div>' +
                        '<div style="font-size: 12px; color: #666;">' +
                            '<a href="' + file_url + '" target="_blank" style="color: #666;">' +
                                '📄 View PDF Purchase Order' +
                            '</a>' +
                        '</div>' +
                    '</div>';

                    frappe.msgprint({
                        title: 'WhatsApp Link Ready - Resend PDF',
                        message: link_message,
                        wide: true
                    });
                }

                frappe.show_alert({
                    message: 'WhatsApp link ready for resending! 🎉',
                    indicator: 'green'
                });
            }
        }
    });
}

function get_supplier_mobile(supplier_name, dialog) {
    if (!supplier_name) return;

    frappe.call({
        method: 'calicut_textiles.calicut_textiles.events.purchase_order.get_supplier_mobile',
        args: {
            supplier_name: supplier_name
        },
        callback: function(r) {
            if (r.message && r.message.mobile) {
                if (dialog) {
                    dialog.set_value('mobile_number', r.message.mobile);
                    if (dialog.get_field('print_format')) {
                        update_message_preview_enhanced(cur_frm, dialog);
                    } else {
                        update_resend_preview(cur_frm, dialog, 'Existing PDF');
                    }
                }
                frappe.show_alert({
                    message: 'Supplier mobile: ' + r.message.mobile,
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: 'No mobile number found for supplier',
                    indicator: 'orange'
                });
            }
        }
    });
}

function send_whatsapp_with_attachment(frm, mobile_number, print_format, letterhead, dialog) {
    if (!mobile_number) {
        frappe.msgprint('Please enter mobile number');
        return;
    }

    frappe.show_alert({
        message: 'Generating PDF for WhatsApp attachment...',
        indicator: 'blue'
    });

    frappe.call({
        method: 'calicut_textiles.calicut_textiles.events.purchase_order.send_pdf_to_whatsapp',
        args: {
            docname: frm.doc.name,
            mobile_number: mobile_number,
            print_format: print_format,
            letterhead: letterhead
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                dialog.hide();

                var attachment_message = '<div style="padding: 20px;">' +
                    '<div style="font-size: 16px; margin-bottom: 20px;">' +
                        '📱 Choose your preferred method:' +
                    '</div>' +
                    '<div style="margin-bottom: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px;">' +
                        '<strong>Option 1: WhatsApp Web (Recommended)</strong><br>' +
                        '<a href="' + r.message.whatsapp_web_url + '" target="_blank" ' +
                           'class="btn btn-success" ' +
                           'style="background: #25D366; border-color: #25D366; margin-top: 10px;">' +
                            '📱 Open WhatsApp Web' +
                        '</a>' +
                        '<p style="margin-top: 10px; font-size: 12px;">' +
                            'After opening, drag and drop the PDF file to attach it.' +
                        '</p>' +
                    '</div>' +
                    '<div style="margin-bottom: 20px; padding: 15px; background: #f0f8ff; border-radius: 5px;">' +
                        '<strong>Option 2: Mobile WhatsApp</strong><br>' +
                        '<a href="' + r.message.whatsapp_mobile_url + '" target="_blank" ' +
                           'class="btn btn-primary" ' +
                           'style="margin-top: 10px;">' +
                            '📱 Open Mobile WhatsApp' +
                        '</a>' +
                        '<p style="margin-top: 10px; font-size: 12px;">' +
                            'Copy the PDF link and share it manually.' +
                        '</p>' +
                    '</div>' +
                    '<div style="margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 5px;">' +
                        '<strong>📄 PDF File:</strong><br>' +
                        '<a href="' + r.message.pdf_url + '" target="_blank" style="color: #666;">' +
                            '📥 Download ' + r.message.pdf_file_name +
                        '</a>' +
                        '<div style="margin-top: 5px; font-size: 12px; color: #666;">' +
                            'Print Format: <strong>' + r.message.print_format_used + '</strong><br>' +
                            'Letterhead: <strong>' + r.message.letterhead_used + '</strong>' +
                        '</div>' +
                    '</div>' +
                '</div>';

                frappe.msgprint({
                    title: 'WhatsApp Ready - Manual PDF Attachment',
                    message: attachment_message,
                    wide: true
                });

                frappe.show_alert({
                    message: 'WhatsApp link and PDF ready! 🎉',
                    indicator: 'green'
                });
            }
        }
    });
}

function update_message_preview_enhanced(frm, dialog) {
    var mobile_number = dialog.get_value('mobile_number');
    var option = dialog.get_value('whatsapp_option');
    var print_format = dialog.get_value('print_format');
    var letterhead = dialog.get_value('letterhead');
    var purchase_order = frm.doc;

    var message_lines = [
        "Good day! 👋",
        "",
        "Thank you for your purchase! 🛍️",
        "",
        "📋 *Purchase Order Details:*",
        "Purchase Order: #" + purchase_order.name,
        "Date: " + frappe.datetime.str_to_user(purchase_order.transaction_date),
        "Amount: " + purchase_order.currency + " " + format_currency(purchase_order.grand_total, purchase_order.currency),
        "",
        "Supplier: " + (purchase_order.supplier_name || purchase_order.supplier),
    ];

    // if (sales_order.delivery_date && sales_order.outstanding_amount > 0) {
    //     message_lines.push("Due Date: " + frappe.datetime.str_to_user(sales_order.delivery_date));
    //     message_lines.push("Outstanding: " + sales_order.currency + " " + format_currency(sales_order.outstanding_amount, sales_order.currency));
    // }

    message_lines.push("");

    if (option === 'PDF for Manual Attachment') {
        message_lines.push("📄 Please find your purchase order PDF attached below.");
    } else {
        message_lines.push("Download Purchase Order: [PDF Link will be added here]");
    }

    message_lines.push("");
    message_lines.push("Thank you for your business! 🙏");

    var preview_html = '<div class="whatsapp-preview">' +
        '<strong>📱 WhatsApp Message Preview:</strong>' +
        '<div style="margin-top: 10px; white-space: pre-line; font-size: 14px;">' +
        message_lines.join('\n') +
        '</div>';

    if (mobile_number) {
        preview_html += '<div style="margin-top: 10px; color: #666; font-size: 12px;">' +
            'Will be sent to: <strong>' + mobile_number + '</strong><br>' +
            'Mode: <strong>' + option + '</strong><br>' +
            'Print Format: <strong>' + (print_format || 'Standard') + '</strong><br>' +
            'Letterhead: <strong>' + (letterhead || 'Default') + '</strong><br>' +
            '📁 PDF will be saved to: <code>/files/PO_' + purchase_order.name + '.pdf</code>' +
            '</div>';
    }

    preview_html += '</div>';

    dialog.set_df_property('message_preview', 'options', preview_html);
}

function send_whatsapp_invoice(frm, mobile_number, print_format, letterhead, dialog) {
    if (!mobile_number) {
        frappe.msgprint('Please enter mobile number');
        return;
    }

    frappe.show_alert({
        message: 'Generating WhatsApp link and saving PDF...',
        indicator: 'blue'
    });

    frappe.call({
        method: 'calicut_textiles.calicut_textiles.events.purchase_order.send_invoice_whatsapp',
        args: {
            docname: frm.doc.name,
            mobile_number: mobile_number,
            print_format: print_format,
            letterhead: letterhead
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                dialog.hide();

                // Open WhatsApp in new tab
                window.open(r.message.whatsapp_url, '_blank');

                // Show success message
                var success_message = '<div style="text-align: center; padding: 20px;">' +
                    '<div style="font-size: 16px; margin-bottom: 20px;">' +
                        'WhatsApp chat opened with supplier! 🎉' +
                    '</div>' +
                    '<div style="margin-bottom: 15px; padding: 10px; background: #e8f5e8; border-radius: 5px;">' +
                        '<strong>📁 PDF Saved to:</strong><br>' +
                        '<a href="' + r.message.pdf_url + '" target="_blank" style="color: #333;">' +
                            r.message.pdf_file_name +
                        '</a><br>' +
                        '<small style="color: #666;">' +
                            'Print Format: ' + r.message.print_format_used + ' | ' +
                            'Letterhead: ' + r.message.letterhead_used +
                        '</small>' +
                    '</div>' +
                    '<div style="margin-bottom: 20px; color: #666; font-size: 14px;">' +
                        'If WhatsApp didn\'t open automatically, ' +
                        '<a href="' + r.message.whatsapp_url + '" target="_blank">click here</a>.' +
                    '</div>' +
                '</div>';

                frappe.msgprint({
                    title: 'WhatsApp Link Generated',
                    message: success_message,
                    wide: true
                });

                frappe.show_alert({
                    message: 'WhatsApp opened successfully!',
                    indicator: 'green'
                });

                frm.reload_doc();
            } else {
                frappe.msgprint({
                    title: 'Error',
                    message: 'Failed to generate WhatsApp link: ' + (r.message.error || 'Unknown error'),
                    indicator: 'red'
                });
            }
        }
    });
}

// Utility function to format currency
function format_currency(amount, currency) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency || 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

frappe.ui.form.on("Estimate bom Items", {
    custom_pcs: function(frm, cdt, cdn) {
        update_qty(frm, cdt, cdn)
    },
    custom_per_meter: function(frm, cdt, cdn) {
        update_qty(frm, cdt, cdn)
    },


});

function update_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
        row.qty = row.custom_pcs * row.custom_per_meter
        frm.refresh_field("items");
}

frappe.ui.form.on("Purchase Order Item", {
    custom_pcs: function(frm, cdt, cdn) {
        update_qty(frm, cdt, cdn)
    },
    custom_net_qty: function(frm, cdt, cdn) {
        update_qty(frm, cdt, cdn)
    },


});

function update_qty(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
        row.qty = row.custom_pcs * row.custom_net_qty
        frm.refresh_field("items");
}
