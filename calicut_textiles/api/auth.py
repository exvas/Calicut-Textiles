import frappe


@frappe.whitelist(allow_guest=True)
def response(message, data, success, status_code):
    '''method to generates responses of an API
       args:
            message : response message string
            data : json object of the data
            success : True or False depending on the API response
            status_code : status of the request'''
    frappe.clear_messages()
    frappe.local.response["message"] = message
    frappe.local.response["data"] = data
    frappe.local.response["success"] = success
    frappe.local.response["http_status_code"] = status_code
    return

@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def user_login(usr, pwd, device_id=None):
    if not usr or not pwd:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Both User and Password are required!",
        }
        frappe.local.response.http_status_code = 400
        return

    # Determine if usr is an email or phone/username
    filter_field = "email" if "@" in usr else ("mobile_no" if usr.isdigit() else "username")

    user = frappe.db.get_value("User", {filter_field: usr}, ["name", "username", "email", "mobile_no","api_key"], as_dict=True)

    if not user:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": f"{filter_field.capitalize()} {usr} Does Not Existeddddd!",
        }
        frappe.local.response.http_status_code = 404
        frappe.log_error(
            title="Login Failed", message=f"{filter_field.capitalize()} {usr} Does Not Exist!"
        )
        return

    try:
        login_manager = frappe.auth.LoginManager()
        frappe.form_dict.device = "mobile"
        login_manager.authenticate(user=user.name, pwd=pwd)
        login_manager.post_login()
        # Optionally handle device_id

        # Generate API key/secret
        api_generate = generate_keys(user.name)
        frappe.response["message"] = {
            "success_key": 1,
            "message": "Authentication success",
            "sid": frappe.session.sid,
            "api_key": user.api_key,
            "api_secret": api_generate,
            "username": user.username,
            "email": user.email,
            "mobile_no": user.mobile_no,
        }
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Incorrect password!",
        }
        frappe.local.response.http_status_code = 401
        return

def set_device_to_mobile():
    # Ensure session exists before modifying
    if hasattr(frappe.local, 'session') and frappe.local.session.data:
        # Set the device in session data to 'mobile'
        frappe.local.session.data['device'] = 'mobile'
        # Commit the session change
        frappe.local.session.save()
    else:
        frappe.throw("Session not found.")

def generate_device_id(user, device_id):
    user_deveice_id = frappe.db.get_value("User Device",{'user':user},'device_id')
    if not user_deveice_id:
        user_details = frappe.new_doc("User Device")
        user_details.device_id = device_id
        user_details.user = user
        user_details.save(ignore_permissions=True)
        frappe.db.commit()
        user_deveice_id = user_details.device_id
    else:
        user_details = frappe.get_doc("User Device",{'user':user})
        user_details.device_id = device_id
        user_details.save(ignore_permissions=True)
        frappe.db.commit()
        user_deveice_id = user_details.device_id
    return user_deveice_id

def generate_keys(user):
    user_details = frappe.get_doc("User", user)
    api_secret = frappe.generate_hash(length=15)

    # if not user_details.api_key:
    #     api_key = frappe.generate_hash(length=15)
    #     user_details.api_key = api_key
    api_key = frappe.generate_hash(length=15)
    user_details.api_key = api_key if not user_details.api_key else user_details.api_key
    user_details.api_secret = api_secret
    user_details.save(ignore_permissions=True)
    frappe.db.commit()

    return api_secret


@frappe.whitelist(methods=["GET", "POST"], allow_guest=True)
def logout(usr):
    users_list = ["Administrator"]
    users = frappe.get_all("User")
    for user in users:
        users_list.append(user)

    if usr in users_list:
        try:
            logout_manager = frappe.auth.LoginManager()
            logout_manager.logout(usr)
            frappe.local.response["message"] = {
                "success_key": 1,
                "message": "Logged out successfully!",
            }
            frappe.local.response.http_status_code = 200

        except Exception as e:
            frappe.local.response["message"] = {
                "success_key": 0,
                "message": "Error logging out!",
                "Exception": e,
            }
            frappe.local.response.http_status_code = 400

    else:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "User not found!",
        }
        frappe.local.response.http_status_code = 404

@frappe.whitelist(methods=["GET", "POST"], allow_guest=True)
def get_user_details(sid=None, user_id=None):
    try:
        if sid:
            # Validate and retrieve the user session using the sid
           get_cookie_options()

        if not user_id:
            frappe.throw("Either user_id or valid sid is required")

        # Fetch the user details using user_id
        user_doc = frappe.get_doc("User", user_id)
        user_data = {
            "sid": sid if sid else frappe.session.sid,  # Use provided SID or current session's SID
            "api_key": user_doc.api_key,
            "api_secret": user_doc.get_password('api_secret'),
            "username": user_doc.username,
            "email": user_doc.email,
            "mobile_no": user_doc.mobile_no,
            "employee_id": frappe.get_value("Employee", {'user_id': user_doc.name}),
        }

        frappe.local.response["message"] = {
            "success_key": 1,
            "message": "Fetched User details successfully!",
            "user": user_data,
        }
        frappe.local.response.http_status_code = 200
    except Exception as e:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Error!",
            "exception": str(e),
        }
        frappe.local.response.http_status_code = 404
        frappe.log_error(title="Get User Details Failed.", message=str(e))


def handle_cors():
    frappe.local.response.headers["Access-Control-Allow-Origin"] = "*"
    frappe.local.response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    frappe.local.response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    ("Access-Control-Allow-Headers", "Access-Control-Allow-Headers, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers")
    
    # Respond to OPTIONS preflight requests
    if frappe.request.method == "OPTIONS":
        frappe.local.response["status_code"] = 200
        return {}

def get_cookie_options():
    options = {}
    if frappe.session and frappe.session.sid and hasattr(frappe.local, "request"):
        # Use wkhtmltopdf's cookie-jar feature to set cookies and restrict them to host domain
        cookiejar = f"/tmp/{frappe.generate_hash()}.jar"

        # Remove port from request.host
        # https://werkzeug.palletsprojects.com/en/0.16.x/wrappers/#werkzeug.wrappers.BaseRequest.host
        domain = frappe.utils.get_host_name().split(":", 1)[0]
        with open(cookiejar, "w") as f:
            f.write(f"sid={frappe.session.sid}; Domain={domain};\n")

        options["cookie-jar"] = cookiejar

    return options


@frappe.whitelist(allow_guest=True)
def get_all_supplier_details():
    page = int(frappe.form_dict.get("page", 1))
    page_size = int(frappe.form_dict.get("page_size", 50))

    # Calculate offset for SQL query
    offset = (page - 1) * page_size

    suppliers = frappe.get_all("Supplier",
                              fields=["name", "supplier_name"],
                              limit_start=offset,
                              limit_page_length=page_size)

    result = []

    for supplier in suppliers:
        # (same address fetching code here...)

        # Example for address fetching as before:
        address_name = frappe.db.sql("""
            SELECT a.name FROM `tabAddress` a
            INNER JOIN `tabDynamic Link` dl ON dl.parent = a.name
            WHERE dl.link_doctype = 'Supplier'
              AND dl.link_name = %s
              AND a.is_primary_address = 1
              AND a.docstatus = 0
            LIMIT 1
        """, (supplier.name,), as_dict=True)

        if address_name:
            address_name = address_name[0].name
        else:
            address_name = frappe.db.get_value("Dynamic Link", {
                "link_doctype": "Supplier",
                "link_name": supplier.name,
                "parenttype": "Address"
            }, "parent")

        address_doc = None
        if address_name:
            address_doc = frappe.get_value("Address", address_name,
                                           ["address_line1", "address_line2", "city", "state", "pincode", "country", "phone"],
                                           as_dict=True)

        full_address = None
        if address_doc:
            full_address = ", ".join(filter(None, [
                address_doc.get("address_line1"),
                address_doc.get("address_line2"),
                address_doc.get("city"),
                address_doc.get("state"),
                address_doc.get("pincode"),
                address_doc.get("country"),
                address_doc.get("phone")
            ]))

        result.append({
            "supplier_id": supplier.name,
            "supplier_name": supplier.supplier_name,
            "address": full_address
        })

    total_suppliers = frappe.db.count("Supplier")

    return {
        "suppliers": result,
        "page": page,
        "page_size": page_size,
        "total_suppliers": total_suppliers,
        "total_pages": (total_suppliers + page_size - 1) // page_size
    }


@frappe.whitelist(allow_guest=True)
def search_suppliers():
    search = frappe.form_dict.get("search", "").strip()

    if not search:
        frappe.throw("Please provide a search term.")

    # Get suppliers matching the search term
    suppliers = frappe.get_all("Supplier",
        fields=["name", "supplier_name"],
        filters={"supplier_name": ["like", f"%{search}%"]},
        order_by="supplier_name asc"
    )

    result = []

    for supplier in suppliers:
        # Try to find primary address from Dynamic Link
        address_name = frappe.db.get_value("Dynamic Link", {
            "link_doctype": "Supplier",
            "link_name": supplier.name,
            "parenttype": "Address"
        }, "parent")

        address_doc = None
        if address_name:
            address_doc = frappe.get_value("Address", address_name,
                ["address_line1", "address_line2", "city", "state", "pincode", "country", "phone"],
                as_dict=True)

        full_address = None
        if address_doc:
            full_address = ", ".join(filter(None, [
                address_doc.address_line1,
                address_doc.address_line2,
                address_doc.city,
                address_doc.state,
                address_doc.pincode,
                address_doc.country,
                address_doc.phone
            ]))

        result.append({
            "supplier_id": supplier.name,
            "supplier_name": supplier.supplier_name,
            "address": full_address
        })

    return result

# import frappe
# import base64
# import os
# from frappe.utils.file_manager import save_file


# @frappe.whitelist(allow_guest=True)
# def create_product():
#     try:
#         product_name = frappe.form_dict.get("product_name")
#         if not product_name:
#             frappe.throw("product name is required")

#         doc = frappe.new_doc("Product")
#         doc.product_name = product_name
#         doc.qty = frappe.form_dict.get("qty")
#         doc.rate = frappe.form_dict.get("rate")
#         doc.amount = frappe.form_dict.get("amount")
#         doc.color = frappe.form_dict.get("color")
#         doc.uom = frappe.form_dict.get("uom")
#         doc.insert()
#         frappe.db.commit()

#         return {
#             "success": True,
#             "message": "Product created successfully",
#             "product_id": doc.name
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "message": "Failed to create product",
#             "error": str(e)
#         }
