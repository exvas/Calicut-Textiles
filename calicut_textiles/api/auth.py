import json
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
        api_key, api_secret = generate_keys(user.name)
        frappe.response["message"] = {
            "success_key": 1,
            "message": "Authentication success",
            "sid": frappe.session.sid,
            "api_key": api_key,
            "api_secret": api_secret,
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

from frappe.utils import nowdate
from frappe.utils.password import set_encrypted_password

def generate_keys(user):
    user_doc = frappe.get_doc("User", user)

    # Always generate new API secret
    new_api_secret = frappe.generate_hash(length=15)
    set_encrypted_password("User", user, new_api_secret, fieldname="api_secret")

    # Generate API key if not already set
    if not user_doc.api_key:
        user_doc.api_key = frappe.generate_hash(length=15)

    user_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return user_doc.api_key, new_api_secret
 # Return both!

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
def get_all_supplier_details_with_searh():
    page = int(frappe.form_dict.get("page", 1))
    page_size = int(frappe.form_dict.get("page_size", 50))
    supplier_name = frappe.form_dict.get("supplier_name")
    supplier_group = frappe.form_dict.get("supplier_group")
    supplier_id = frappe.form_dict.get("supplier_id")

    # Build filters dynamically
    filters = {}
    if supplier_id:
        filters["name"] = ["like", f"%{supplier_id}%"]
    if supplier_name:
        filters["supplier_name"] = ["like", f"%{supplier_name}%"]
    if supplier_group:
        filters["supplier_group"] = supplier_group

    # Get full filtered list without limit
    all_suppliers = frappe.get_all(
        "Supplier",
        filters=filters,
        fields=["name", "supplier_name", "supplier_group"]
    )

    total_suppliers = len(all_suppliers)
    total_pages = (total_suppliers + page_size - 1) // page_size

    # Slice manually for pagination
    offset = (page - 1) * page_size
    paginated_suppliers = all_suppliers[offset:offset + page_size]

    result = []
    for supplier in paginated_suppliers:
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
            "supplier_group": supplier.supplier_group,
            "address": full_address
        })

    return {
        "suppliers": result,
        "page": page,
        "page_size": page_size,
        "total_suppliers": total_suppliers,
        "total_pages": total_pages
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



@frappe.whitelist(allow_guest=True)
def create_product():
    try:
       

        # Create the Product Doc
        product_name = frappe.form_dict.get("product_name") or frappe.throw("Product name is required")
        doc = frappe.new_doc("Product")
        doc.product_name = product_name
        doc.quantity     = frappe.form_dict.get("qty")
        doc.rate         = frappe.form_dict.get("rate")
        doc.amount       = frappe.form_dict.get("amount")
        doc.uom          = frappe.form_dict.get("uom")

       
        doc.save(ignore_permissions=True)

        
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "message": "Product created successfully",
            "product_id": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(str(e), "Create Product Failed")
        return {
            "success": False,
            "message": "Failed to create product",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_all_products():
    try:
        # Parse pagination and search parameters
        page = int(frappe.form_dict.get("page", 1))
        page_size = int(frappe.form_dict.get("page_size", 20))
        search = frappe.form_dict.get("product_name", "").strip()

        # Calculate offset
        offset = (page - 1) * page_size

        # Build filters
        filters = {}
        if search:
            filters["product_name"] = ["like", f"%{search}%"]

        # Fetch filtered and paginated products
        products = frappe.get_all(
            "Product",
            filters=filters,
            fields=[
                "name",
                "product_name",
                "rate",
                "quantity",
                "amount",
                "uom"
            ],
            order_by="creation desc",
            limit_start=offset,
            limit_page_length=page_size
        )

        # Get total count for pagination
        total_count = frappe.db.count("Product", filters=filters)
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "success": True,
            "message": "Product list fetched successfully",
            "data": products,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_products": total_count,
                "total_pages": total_pages
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get All Products Error")
        return {
            "success": False,
            "message": "Failed to fetch product list",
            "error": str(e)
        }



# @frappe.whitelist(methods=["POST"], allow_guest=True)
# def create_supplier_order():
#     try:
#         user = frappe.session.user
#         if not user:
#             frappe.throw("No user session")

#         # Get Employee ID linked to user
#         employee_id = frappe.db.get_value("Employee", {"user_id": user}, "name")
#         if not employee_id:
#             frappe.throw("No employee linked to this user")

#         # Check permission
#         if not frappe.has_permission("Supplier Order", "create", user=user):
#             frappe.throw("You do not have permission to create Supplier Order")

#         # Parse form-data fields
#         supplier = frappe.form_dict.get("supplier")
#         order_date = frappe.form_dict.get("order_date")
#         grand_total = frappe.form_dict.get("grand_total")
#         products_json = frappe.form_dict.get("products")  # JSON string

#         if not supplier or not order_date or not products_json:
#             frappe.throw("Missing required fields: supplier, order_date, or products")

#         import json
#         products = json.loads(products_json)
#         supplier_name = frappe.db.get_value("Supplier", supplier, "supplier_name")
#         print("supplier_name",supplier_name)
#         # Step 1: Create Supplier Order and insert it to get doc.name
#         doc = frappe.new_doc("Supplier Order")
#         doc.supplier = supplier
#         doc.order_date = order_date
#         doc.grand_total = grand_total
#         doc.sales_person = employee_id
#         doc.supplier_name=supplier_name
#         doc.insert(ignore_permissions=True)  # Insert first to get doc.name

#         # Step 2: Handle child rows and image uploads
#         for idx, item in enumerate(products):
#             images = {}

#             for image_field in ["image_1", "image_2", "image_3"]:
#                 file_key = f"{image_field}_{idx}"
#                 if file_key in frappe.request.files:
#                     file = frappe.request.files[file_key]
#                     uploaded_file = frappe.utils.file_manager.save_file(
#                         fname=file.filename,
#                         content=file.stream.read(),
#                         dt="Supplier Order",
#                         dn=doc.name,
#                         is_private=0
#                     )
#                     images[image_field] = uploaded_file.file_url
#                 else:
#                     images[image_field] = ""

#             doc.append("products", {
#                 "product": item.get("product"),
#                 "quantity": item.get("qty"),
#                 "uom": item.get("uom"),
#                 "rate": item.get("rate"),
#                 "pcs": item.get("pcs"),
#                 "net_qty": item.get("net_qty"),
#                 "amount": item.get("amount"),
#                 "required_by": item.get("required_date"),
#                 "color": item.get("color"),
#                 "image_1": images["image_1"],
#                 "image_2": images["image_2"],
#                 "image_3": images["image_3"],
#             })

#         # Step 3: Save final document with child rows
#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "success": True,
#             "message": f"Supplier Order created by employee {employee_id}",
#             "docname": doc.name,
#             "employee_id": employee_id
#         }

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), "Supplier Order API Error")
#         return {
#             "success": False,
#             "message": "Error creating supplier order",
#             "error": str(e)
#         }


from frappe import _

@frappe.whitelist(methods=["POST"], allow_guest=True)
def create_supplier_order():
    try:
        user = frappe.session.user
        if not user:
            frappe.throw(_("No user session"))

        # Get Employee ID linked to user
        employee_id = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee_id:
            frappe.throw(_("No employee linked to this user"))

        # Check permission
        if not frappe.has_permission("Supplier Order", "create", user=user):
            frappe.throw(_("You do not have permission to create Supplier Order"))

        # Parse form‑data fields
        supplier      = frappe.form_dict.get("supplier")
        order_date    = frappe.form_dict.get("order_date")
        grand_total   = frappe.form_dict.get("grand_total")
        products_json = frappe.form_dict.get("products")  # JSON string

        if not supplier or not order_date or not products_json:
            frappe.throw(_("Missing required fields: supplier, order_date, or products"))

        # Load the JSON into a Python list
        products = json.loads(products_json)

        # (Optional) Fetch supplier_name
        supplier_name = frappe.db.get_value("Supplier", supplier, "supplier_name") or ""

        # Create the new Supplier Order
        doc = frappe.new_doc("Supplier Order")
        doc.supplier      = supplier
        doc.supplier_name = supplier_name
        doc.order_date    = order_date
        doc.grand_total   = grand_total
        doc.sales_person  = employee_id
        doc.insert(ignore_permissions=True)

        # Loop over each product line
        for idx, item in enumerate(products):
            # Front‑end provided values
            color  = (item.get("color")  or "").strip()
            typ    = (item.get("type")   or "").strip()
            design = (item.get("design") or "").strip()

            # Build product_name parts in the order: product–type–design–color
            parts = [
                item.get("product"),  # e.g. "skert"
                typ,                  # e.g. "Cotton"
                design,               # e.g. "Floral"
                color                 # e.g. "Red"
            ]
            # Filter out any blank entries
            parts = [p for p in parts if p]

            # Join all parts with hyphens
            product_name = "-".join(parts)

            # Handle image uploads for this row
            images = {}
            for image_field in ("image_1", "image_2", "image_3"):
                file_key = f"{image_field}_{idx}"
                if file_key in frappe.request.files:
                    f = frappe.request.files[file_key]
                    uploaded = frappe.utils.file_manager.save_file(
                        fname     = f.filename,
                        content   = f.stream.read(),
                        dt        = "Supplier Order",
                        dn        = doc.name,
                        is_private= 0
                    )
                    images[image_field] = uploaded.file_url
                else:
                    images[image_field] = ""

            # Append this line to the child table
            doc.append("products", {
                "product":      item.get("product"),
                "product_name": product_name,
                "quantity":     item.get("qty"),
                "uom":          item.get("uom"),
                "rate":         item.get("rate"),
                "pcs":          item.get("pcs"),
                "net_qty":      item.get("net_qty"),
                "amount":       item.get("amount"),
                "required_by":  item.get("required_date"),
                "color":        color,
                "type":         typ,
                "design":       design,
                "image_1":      images["image_1"],
                "image_2":      images["image_2"],
                "image_3":      images["image_3"],
            })

        # Save everything
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "message": _("Supplier Order {0} created by employee {1}").format(doc.name, employee_id),
            "docname": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Supplier Order API Error")
        return {
            "success": False,
            "message": _("Error creating supplier order"),
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_all_supplier_orders():
    try:
        # Get pagination + search filters
        page = int(frappe.form_dict.get("page", 1))
        page_size = int(frappe.form_dict.get("page_size", 20))
        order_id_filter = frappe.form_dict.get("supplier_order_id", "").strip()
        supplier_name_filter = frappe.form_dict.get("supplier_name", "").strip()

        # Build SQL conditions and values
        conditions = "WHERE 1=1"
        values = {}

        if order_id_filter:
            conditions += " AND so.name LIKE %(order_id)s"
            values["order_id"] = f"%{order_id_filter}%"

        if supplier_name_filter:
            conditions += " AND so.supplier_name LIKE %(supplier_name)s"
            values["supplier_name"] = f"%{supplier_name_filter}%"

        # Count total matching records
        count_query = f"""
            SELECT COUNT(*) AS total
            FROM `tabSupplier Order` so
            {conditions}
        """
        total_orders = frappe.db.sql(count_query, values)[0][0]
        total_pages = (total_orders + page_size - 1) // page_size

        # Adjust page number
        if page > total_pages and total_pages > 0:
            page = total_pages
        elif total_pages == 0:
            page = 1

        offset = (page - 1) * page_size

        # Fetch paginated Supplier Orders
        data_query = f"""
            SELECT so.name, so.supplier, so.supplier_name, so.order_date,
                   so.grand_total, so.docstatus, so.creation
            FROM `tabSupplier Order` so
            {conditions}
            ORDER BY so.creation DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        values.update({"limit": page_size, "offset": offset})
        supplier_orders = frappe.db.sql(data_query, values, as_dict=True)

        result = []
        for order in supplier_orders:
            # Map docstatus to readable status
            status_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
            readable_status = status_map.get(order.docstatus, "Unknown")

            products = frappe.get_all(
                "Supplier Order Product",
                filters={"parent": order.name},
                fields=[
                    "product", "quantity", "uom", "rate", "amount",
                    "required_by", "net_qty", "pcs", "color", "design", "type"
                ]
            )

            result.append({
                "order_id": order.name,
                "supplier_name": order.supplier_name or "",
                "order_date": order.order_date,
                "grand_total": order.grand_total,
                "status": readable_status,
                "products": products,
            })

        return {
            "success": True,
            "message": "Supplier Orders fetched successfully",
            "orders": result,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_orders": total_orders,
                "total_pages": total_pages
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get All Supplier Orders Error")
        return {
            "success": False,
            "message": "Failed to fetch supplier orders",
            "error": str(e)
        }


@frappe.whitelist(methods=["POST"])
def update_supplier_order():
    try:
        data = frappe.request.get_json()
        name = data.get("so_name")  # Supplier Order name

        if not name:
            frappe.throw("Supplier Order name is required")

        user = frappe.session.user
        if not user:
            frappe.throw("No active user session")

        # Get Employee ID linked to the user
        employee_id = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee_id:
            frappe.throw("No employee linked to this user")

        supplier_order = frappe.get_doc("Supplier Order", name)

        # Ensure it's not submitted
        if supplier_order.docstatus != 0:
            return {
                "success": False,
                "message": "Cannot update. Supplier Order has been submitted."
            }

        # Update parent fields
        new_supplier = data.get("supplier")
        if new_supplier:
            supplier_order.supplier = new_supplier
            supplier_order.supplier_name = frappe.db.get_value("Supplier", new_supplier, "supplier_name") or ""

        supplier_order.order_date = data.get("order_date", supplier_order.order_date)
        supplier_order.grand_total = data.get("grand_total", supplier_order.grand_total)
        supplier_order.sales_person = employee_id

        # Update child table if provided
        if "products" in data:
            supplier_order.set("products", [])  # Clear existing

            for item in data.get("products", []):
                color  = (item.get("color")  or "").strip()
                typ    = (item.get("type")   or "").strip()
                design = (item.get("design") or "").strip()

                # Build product_name: product-type-design-color
                parts = [
                    item.get("product"),  # required
                    typ,
                    design,
                    color
                ]
                parts = [p for p in parts if p]
                product_name = "-".join(parts)

                supplier_order.append("products", {
                    "product":      item.get("product"),
                    "product_name": product_name,
                    "quantity":     item.get("qty"),
                    "uom":          item.get("uom"),
                    "rate":         item.get("rate"),
                    "amount":       item.get("amount"),
                    "required_by":  item.get("required_date"),
                    "pcs":          item.get("pcs", 0),
                    "net_qty":      item.get("net_qty", 0),
                    "color":        color,
                    "type":         typ,
                    "design":       design
                })

        supplier_order.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "message": f"Supplier Order {name} updated by {employee_id}",
            "docname": supplier_order.name,
            "employee_name": employee_id
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Supplier Order Error")
        return {
            "success": False,
            "message": "Failed to update Supplier Order",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_supplier_groups():
    try:
        supplier_groups = frappe.get_all(
            "Supplier Group",
            filters={"is_group": 0},  # Only non-group (leaf) entries
            fields=["name", "parent_supplier_group"]
        )

        return {
            "success": True,
            "data": supplier_groups
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Supplier Group API Error")
        return {
            "success": False,
            "message": "Failed to fetch supplier groups",
            "error": str(e)
        }



@frappe.whitelist(allow_guest=True)
def get_attribute_values_by_parent(parent_name):
    try:
        values = frappe.get_all(
            "Item Attribute Value",  # ✅ Correct child doctype name
            filters={"parent": parent_name},
            fields=["attribute_value"],
            order_by="attribute_value"
        )

        return {
            "success": True,
            "data": [v.attribute_value for v in values]
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Attribute Values API Error")
        return {
            "success": False,
            "message": "Failed to fetch attribute values",
            "error": str(e)
        }



@frappe.whitelist(allow_guest=True)
def get_all_colours():
   
    try:
        rows = frappe.get_all(
            "Item Attribute Value",
            filters={"parent": "Colour"},
            fields=["attribute_value"],
            order_by="idx"
        )
        # extract the strings
        colours = [r.attribute_value for r in rows]

        return {
            "success": True,
            "data": colours
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get All Colours API Error")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_all_types():
   
    try:
        rows = frappe.get_all(
            "Item Attribute Value",
            filters={"parent": "Type"},
            fields=["attribute_value"],
            order_by="idx"
        )
        # extract the strings
        colours = [r.attribute_value for r in rows]

        return {
            "success": True,
            "data": colours
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get All type API Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_all_designs():
   
    try:
        rows = frappe.get_all(
            "Item Attribute Value",
            filters={"parent": "Design"},
            fields=["attribute_value"],
            order_by="idx"
        )
        # extract the strings
        colours = [r.attribute_value for r in rows]

        return {
            "success": True,
            "data": colours
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get All type API Error")
        return {
            "success": False,
            "error": str(e)
        }
# @frappe.whitelist(allow_guest=True)
# def get_all_designs():
#     values = frappe.get_all(
#         "Item Attribute Value",
#         filters={"parent": "Design"},
#         fields=["attribute_value"],
#         order_by="attribute_value"
#     )
#     return [v.attribute_value for v in values]
