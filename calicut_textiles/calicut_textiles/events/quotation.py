import frappe

@frappe.whitelist()
def get_customer_mobile(customer_name):
    """Get mobile number from customer record"""
    try:
        if not customer_name:
            return {"mobile": ""}

        customer = frappe.get_doc("Customer", customer_name)
        mobile = customer.mobile_no or ""

        # Also check in customer's primary contact
        if not mobile:
            contacts = frappe.get_all("Dynamic Link",
                filters={
                    "link_doctype": "Customer",
                    "link_name": customer_name,
                    "parenttype": "Contact"
                },
                fields=["parent"]
            )

            if contacts:
                contact = frappe.get_doc("Contact", contacts[0].parent)
                mobile = contact.mobile_no or contact.phone or ""

        return {"mobile": mobile}

    except Exception as e:
        frappe.log_error(f"Error getting customer mobile: {str(e)}")
        return {"mobile": ""}


@frappe.whitelist()
def get_whatsapp_settings():
    """Get WhatsApp settings from Whatsapp Settings"""
    try:
        settings = frappe.get_single("Whatsapp Settings")
        return {
            "success": True,
            "print_format": settings.whatsapp__print_format or "Standard",
            "letterhead": settings.whatsapp_letter_head or "",
            "message": f"Settings: Print Format='{settings.whatsapp__print_format or 'Standard'}', Letterhead='{settings.whatsapp_letter_head or 'None'}'"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def send_pdf_to_whatsapp(docname, mobile_number, print_format=None, letterhead=None):
    """
    Generate quotation PDF for manual WhatsApp attachment
    """
    try:
        # Get the invoice document
        quotation = frappe.get_doc("Quotation", docname)

        # Check permissions
        if not frappe.has_permission("Quotation", "read", quotation.name):
            frappe.throw(_("No permission to access this quotation"))

        # Generate and save PDF/HTML
        pdf_data = generate_and_save_invoice_pdf(quotation, print_format, letterhead)

        # Create WhatsApp URLs (without PDF link in message)
        whatsapp_data = create_whatsapp_message_for_attachment(mobile_number, quotation, pdf_data)

        # Use the file URL directly instead of constructing physical path
        file_url = pdf_data.get('file_url', '')
        site_url = frappe.utils.get_url()
        full_download_url = f"{site_url}{file_url}" if file_url else ""

        return {
            "success": True,
            "whatsapp_web_url": whatsapp_data["whatsapp_web_url"],
            "whatsapp_mobile_url": whatsapp_data["whatsapp_mobile_url"],
            "pdf_url": whatsapp_data["pdf_url"],
            "pdf_file_name": pdf_data["file_name"],
            "pdf_download_url": full_download_url,
            "file_path": file_url,
            "print_format_used": pdf_data.get("print_format_used"),
            "letterhead_used": pdf_data.get("letterhead_used"),
            "message": f"File generated using {pdf_data.get('print_format_used')} with {pdf_data.get('letterhead_used')} letterhead"
        }

    except Exception as e:
        frappe.log_error(f"WhatsApp PDF error: {str(e)}", "WhatsApp PDF Error")
        return {
            "success": False,
            "error": str(e)
        }

def generate_and_save_invoice_pdf(quotation, custom_print_format=None, custom_letterhead=None):
    """
    Generate PDF for the quotation using Whatsapp Settings configuration or custom parameters
    Tries PDF first, falls back to HTML if PDF generation fails
    """
    try:
        # Get settings from Whatsapp Settings - FORCE READ EVERY TIME
        settings = frappe.get_single("Whatsapp Settings")

        # Use custom parameters if provided, otherwise use settings
        print_format = custom_print_format if custom_print_format is not None else (settings.whatsapp__print_format or "Standard")
        letterhead = custom_letterhead if custom_letterhead is not None else settings.whatsapp_letter_head

        # # Force logging to verify settings are being used
        frappe.logger().info(f"WhatsApp Generation: Using Print Format '{print_format}' with Letterhead '{letterhead}' (Custom PF: {custom_print_format is not None}, Custom LH: {custom_letterhead is not None})")

        # # Generate HTML using the custom settings
        html = frappe.get_print(
            "Quotation",
            quotation.name,
            print_format=print_format,
            letterhead=letterhead
        )

        # Try PDF generation first
        try:
            # Method 1: Try with frappe.get_print directly with as_pdf=True
            pdf_content = frappe.get_print(
                "Quotation",
                quotation.name,
                print_format=print_format,
                letterhead=letterhead,
                as_pdf=True
            )
            file_extension = "pdf"
            file_content = pdf_content
            frappe.logger().info("WhatsApp: PDF generated successfully")

        except Exception as pdf_error1:
            frappe.logger().warning(f"Method 1 PDF generation failed: {pdf_error1}")

            # Method 2: Try with minimal PDF options
            try:
                from frappe.utils.pdf import get_pdf
                pdf_content = get_pdf(html, options={
                    "page-size": "A4",
                    "encoding": "UTF-8",
                    "quiet": "",
                    "no-outline": "",
                    "disable-smart-shrinking": ""
                })
                file_extension = "pdf"
                file_content = pdf_content
                frappe.logger().info("WhatsApp: PDF generated with method 2")

            except Exception as pdf_error2:
                frappe.logger().warning(f"Method 2 PDF generation failed: {pdf_error2}")

                # Method 3: Use wkhtmltopdf with basic options
                try:
                    import subprocess
                    import tempfile
                    import os

                    # Save HTML to temp file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
                        temp_html.write(html)
                        temp_html_path = temp_html.name

                    # Generate PDF using subprocess
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                        temp_pdf_path = temp_pdf.name

                    # Use wkhtmltopdf directly with minimal options
                    cmd = [
                        'wkhtmltopdf',
                        '--page-size', 'A4',
                        '--encoding', 'UTF-8',
                        '--quiet',
                        '--disable-smart-shrinking',
                        temp_html_path,
                        temp_pdf_path
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                    if result.returncode == 0:
                        with open(temp_pdf_path, 'rb') as pdf_file:
                            file_content = pdf_file.read()
                        file_extension = "pdf"
                        frappe.logger().info("WhatsApp: PDF generated with subprocess")
                    else:
                        raise Exception(f"wkhtmltopdf failed: {result.stderr}")

                    # Clean up temp files
                    os.unlink(temp_html_path)
                    os.unlink(temp_pdf_path)

                except Exception as pdf_error3:
                    frappe.logger().warning(f"Method 3 PDF generation failed: {pdf_error3}")

                    # Final fallback: Use HTML
                    file_extension = "html"
                    file_content = html.encode('utf-8')
                    frappe.logger().info("WhatsApp: Using HTML format as final fallback")

        # Save the file
        file_name = f"Quotation{invoice.name}.{file_extension}"
        file_doc = save_file(
            fname=file_name,
            content=file_content,
            dt="Quotation",
            dn=quotation.name,
            is_private=0  # Make it public so it can be downloaded
        )

        frappe.logger().info(f"WhatsApp: Successfully generated {file_name} using {print_format} format with {letterhead} letterhead")

        return {
            "file_name": file_name,
            "file_url": file_doc.file_url,
            "file_path": f"/files/{file_name}",
            "file_doc": file_doc,
            "print_format_used": print_format,
            "letterhead_used": letterhead or "No Letterhead"
        }

    except Exception as e:
        frappe.log_error(f"WhatsApp file generation error: {str(e)}", "WhatsApp File Generation Error")

        # Fallback: Create a simple text file with invoice details
        try:
            settings = frappe.get_single("Whatsapp Settings")
            print_format = custom_print_format if custom_print_format is not None else (settings.whatsapp__print_format or "Standard")
            letterhead = custom_letterhead if custom_letterhead is not None else settings.whatsapp_letter_head

            fallback_content = f"""
QUOTATION DETAILS
===============

Quotation Number: {quotation.name}
Customer: {quotation.customer_name or invoice.party_name}
Date: {quotation.transaction_date}
Amount: {quotation.currency} {quotation.grand_total}

Attempted to use:
Print Format: {print_format}
Letterhead: {letterhead or "No Letterhead"}

Note: Both PDF and HTML generation failed. This is a text fallback.
Please contact support for assistance.
            """.strip()

            file_name = f"Quotation{quotation.name}_fallback.txt"
            file_doc = save_file(
                fname=file_name,
                content=fallback_content.encode('utf-8'),
                dt="Quotation",
                dn=quotation.name,
                is_private=0
            )

            return {
                "file_name": file_name,
                "file_url": file_doc.file_url,
                "file_path": f"/files/{file_name}",
                "file_doc": file_doc,
                "print_format_used": f"{print_format} (Fallback)",
                "letterhead_used": f"{letterhead or 'No Letterhead'} (Fallback)"
            }

        except Exception as final_error:
            frappe.log_error(f"Final fallback failed: {str(final_error)}", "WhatsApp Final Fallback Error")
            raise Exception(f"All file generation methods failed: {str(e)}")

def create_whatsapp_message_for_attachment(mobile_number, quotation, pdf_data):
    """Create WhatsApp message URLs for manual PDF attachment"""

    # Clean mobile number (remove spaces, dashes, etc.)
    clean_number = ''.join(filter(str.isdigit, mobile_number.replace('+', '')))

    # Get site URL
    site_url = frappe.utils.get_url()
    full_pdf_url = f"{site_url}{pdf_data['file_url']}"

    # Create message text (without PDF link since it will be attached manually)
    message_lines = [
        "Good day! 👋",
        "",
        "Thank you for your purchase! 🛍️",
        "",
        "📋 *Quotation Details:*",
        f"Quotation: #{quotation.name}",
        f"Date: {quotation.get_formatted('transaction_date')}",
        f"Amount: {quotation.currency} {quotation.get_formatted('grand_total')}",
        "",
        f"Customer: {quotation.customer_name or quotation.party_name}",
    ]

    # Add due date and outstanding if applicable
    if quotation.valid_till and quotation.outstanding_amount > 0:
        message_lines.extend([
            f"Due Date: {quotation.get_formatted('valid_till')}",
            f"Outstanding: {quotation.currency} {quotation.get_formatted('outstanding_amount')}"
        ])

    message_lines.extend([
        "",
        "📄 Please find your invoice attached below.",
        "",
        "Thank you for your business! 🙏"
    ])

    message = "\n".join(message_lines)

    # Encode message for URL
    import urllib.parse
    encoded_message = urllib.parse.quote(message)

    # Create WhatsApp URLs
    whatsapp_web_url = f"https://web.whatsapp.com/send?phone={clean_number}&text={encoded_message}"
    whatsapp_mobile_url = f"https://wa.me/{clean_number}?text={encoded_message}"

    return {
        "whatsapp_web_url": whatsapp_web_url,
        "whatsapp_mobile_url": whatsapp_mobile_url,
        "pdf_url": full_pdf_url,
        "message": message
    }

@frappe.whitelist()
def send_invoice_whatsapp(docname, mobile_number, print_format=None, letterhead=None):
    """
    Generate quotation PDF, save it to files, and create WhatsApp message link
    """
    try:
        # Get the invoice document
        quotation = frappe.get_doc("Quotation", docname)

        # Check permissions
        if not frappe.has_permission("Quotation", "read", quotation.name):
            frappe.throw(_("No permission to access this quotation"))

        # Generate and save PDF/HTML
        pdf_data = generate_and_save_invoice_pdf(quotation, print_format, letterhead)

        # Generate WhatsApp message
        whatsapp_data = create_whatsapp_message(mobile_number, quotation, pdf_data)

        return {
            "success": True,
            "whatsapp_url": whatsapp_data["whatsapp_url"],
            "pdf_url": whatsapp_data["pdf_url"],
            "pdf_file_name": pdf_data["file_name"],
            "pdf_file_path": pdf_data["file_path"],
            "print_format_used": pdf_data.get("print_format_used"),
            "letterhead_used": pdf_data.get("letterhead_used"),
            "message": f"WhatsApp link created using {pdf_data.get('print_format_used')} with {pdf_data.get('letterhead_used')} letterhead"
        }

    except Exception as e:
        frappe.log_error(f"WhatsApp send error: {str(e)}", "WhatsApp Invoice Error")
        return {
            "success": False,
            "error": str(e)
        }

def create_whatsapp_message(mobile_number, quotation, pdf_data):
    """Create WhatsApp message URL with quotation details and PDF link"""

    # Clean mobile number (remove spaces, dashes, etc.)
    clean_number = ''.join(filter(str.isdigit, mobile_number))

    if not clean_number.startswith('+91') and len(clean_number) == 10:
    	clean_number = '+91' + clean_number

    # Get site URL
    site_url = frappe.utils.get_url()
    full_pdf_url = f"{site_url}{pdf_data['file_url']}"

    # Create message text
    message_lines = [
        "Good day! 👋",
        "",
        "Thank you for your purchase! 🛍️",
        "",
        "📋 *Quotation Details:*",
        f"Invoice: #{quotation.name}",
        f"Date: {quotation.get_formatted('transaction_date')}",
        f"Amount: {quotation.currency} {quotation.get_formatted('grand_total')}",
        "",
        f"Customer: {quotation.customer_name or quotation.party_name}",
    ]

    # Add due date and outstanding if applicable
    if quotation.valid_till and quotation.outstanding_amount > 0:
        message_lines.extend([
            f"Due Date: {quotation.get_formatted('valid_till')}",
            f"Outstanding: {quotation.currency} {quotation.get_formatted('outstanding_amount')}"
        ])

    # Determine file type for message
    file_type = "PDF" if pdf_data['file_name'].endswith('.pdf') else "Quotation"

    message_lines.extend([
        "",
        f"📄 Download {file_type}: {full_pdf_url}",
        "",
        "Thank you for your business! 🙏"
    ])

    message = "\n".join(message_lines)

    # Encode message for URL
    from urllib.parse import quote
    encoded_message = quote(message)
    whatsapp_url = f"https://wa.me/{clean_number}?text={encoded_message}"

    return {
        "whatsapp_url": whatsapp_url,
        "pdf_url": full_pdf_url,
        "message": message
    }

frappe.whitelist()
def get_saved_invoice_files(docname):
    """Get all saved PDF files for the QUOTATION"""
    try:
        # Get all files attached to this Sales Invoice
        files = frappe.get_all("File",
            filters={
                "attached_to_doctype": "Quotation",
                "attached_to_name": docname,
                "file_name": ["like", "Quotation_%"]
            },
            fields=["name", "file_name", "file_url", "creation"],
            order_by="creation desc"
        )

        return {
            "success": True,
            "files": files
        }

    except Exception as e:
        frappe.log_error(f"Error getting saved files: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def resend_existing_pdf_whatsapp(docname, mobile_number, option, file_name, file_url):
    """
    Resend existing PDF via WhatsApp without regenerating
    """
    try:
        # Get the invoice document
        quotation = frappe.get_doc("Quotation", docname)

        # Check permissions
        if not frappe.has_permission("Quotation", "read", quotation.name):
            frappe.throw(_("No permission to access this quotation"))

        # Create fake pdf_data structure for existing file
        pdf_data = {
            "file_name": file_name,
            "file_url": file_url
        }

        if option == "PDF for Manual Attachment":
            # Create WhatsApp URLs (without PDF link in message)
            whatsapp_data = create_whatsapp_message_for_attachment(mobile_number, invoice, pdf_data)

            return {
                "success": True,
                "whatsapp_web_url": whatsapp_data["whatsapp_web_url"],
                "whatsapp_mobile_url": whatsapp_data["whatsapp_mobile_url"],
                "pdf_url": whatsapp_data["pdf_url"],
                "message": "Resend ready for manual attachment"
            }
        else:
            # Create WhatsApp message with PDF link
            whatsapp_data = create_whatsapp_message(mobile_number, invoice, pdf_data)

            return {
                "success": True,
                "whatsapp_url": whatsapp_data["whatsapp_url"],
                "pdf_url": whatsapp_data["pdf_url"],
                "message": "Resend ready with download link"
            }

    except Exception as e:
        frappe.log_error(f"WhatsApp resend error: {str(e)}", "WhatsApp Resend Error")
        return {
            "success": False,
            "error": str(e)
        }
