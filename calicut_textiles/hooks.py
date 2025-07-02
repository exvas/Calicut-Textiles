app_name = "calicut_textiles"
app_title = "Calicut Textiles"
app_publisher = "sammish"
app_description = "Textile exporter in Kozhikode"
app_email = "sammish.thundiyil@gmail.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/calicut_textiles/css/calicut_textiles.css"
app_include_js = ["/assets/calicut_textiles/js/barcode_scan_38.js"]

# include js, css files in header of web template
# web_include_css = "/assets/calicut_textiles/css/calicut_textiles.css"
# web_include_js = "/assets/calicut_textiles/js/calicut_textiles.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "calicut_textiles/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Purchase Receipt" : "public/purchase_recipt.js",
              "Item" : "public/item.js",
              "Purchase Order" : "public/purchase_order.js",
              "Salary Slip" : "public/salary_slip.js",
              "Sales Invoice" : "public/sales_invoice.js",
              "Sales Order" : "public/sales_order.js",
              "Purchase Invoice" : "public/purchase_invoice.js",
              }

doctype_list_js = {"Item" : "public/item_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "calicut_textiles/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "calicut_textiles.utils.jinja_methods",
# 	"filters": "calicut_textiles.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "calicut_textiles.install.before_install"
# after_install = "calicut_textiles.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "calicut_textiles.uninstall.before_uninstall"
# after_uninstall = "calicut_textiles.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "calicut_textiles.utils.before_app_install"
# after_app_install = "calicut_textiles.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "calicut_textiles.utils.before_app_uninstall"
# after_app_uninstall = "calicut_textiles.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "calicut_textiles.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Leave Encashment": "calicut_textiles.calicut_textiles.events.encashment.CustomLeaveEncashment",
    "Department": "calicut_textiles.calicut_textiles.events.department.CustomDepartment"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Item": {
        "before_insert":["calicut_textiles.calicut_textiles.item.update_item_code"],
        "validate": ["calicut_textiles.calicut_textiles.item.update_batch_number_series",
                    "calicut_textiles.calicut_textiles.item.item_name_unique", ]

	},
    "Item Price": {
        "validate":["calicut_textiles.calicut_textiles.item_price.update_custom_rate_code"]
	},
    "Purchase Receipt": {
        "validate":["calicut_textiles.calicut_textiles.purchase_receipt.custom_date_code"],
        "before_submit": ["calicut_textiles.calicut_textiles.purchase_receipt.update_supplier_packing_slip"],
        "on_cancel":"calicut_textiles.calicut_textiles.purchase_receipt.delete_item_prices"
	},
    "Salary Slip": {
        "before_insert": "calicut_textiles.calicut_textiles.events.salary_slip.before_save",

    },
    "Purchase Invoice": {
        "before_submit": "calicut_textiles.calicut_textiles.events.purchase_invoice.create_purchase_invoices",

    },
    "Salary Structure Assignment": {
        "validate": "calicut_textiles.calicut_textiles.events.salary_structure_assignment.validate_encashment_amount",

    },

    "Serial and Batch Bundle": {
        "before_save":["calicut_textiles.calicut_textiles.events.event.custom_date_code"],
        "on_submit": "calicut_textiles.calicut_textiles.events.batch.update_qty"

    },
    "Employee Advance": {
        "on_submit":["calicut_textiles.calicut_textiles.events.event.update_employee_advance"],
    },
     "Additional Salary": {
        "on_submit":["calicut_textiles.calicut_textiles.events.event.update_employee_additional"],
    },

}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"calicut_textiles.tasks.all"
	# ],
	"daily": [
		"calicut_textiles.calicut_textiles.events.encashment.process_monthly_leave_encashment"
	]
	# "hourly": [
	# 	"calicut_textiles.tasks.hourly"
	# ],
	# "weekly": [
	# 	"calicut_textiles.tasks.weekly"
	# ],
	# "monthly": [
	# 	"calicut_textiles.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "calicut_textiles.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "erpnext.stock.utils.scan_barcode": "calicut_textiles.calicut_textiles.events.sales_invoice.scan_barcode",
    "hrms.hr.doctype.leave_encashment.leave_encashment.get_leave_details_for_encashment": "calicut_textiles.calicut_textiles.events.encashment.get_leave_details_for_encashment",

}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Purchase Order": "calicut_textiles.calicut_textiles.events.dashboard.dashboard.purchase_order_dashboard",
    "Purchase Receipt": "calicut_textiles.calicut_textiles.events.dashboard.dashboard.purchase_receipt"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["calicut_textiles.utils.before_request"]
# after_request = ["calicut_textiles.utils.after_request"]

# Job Events
# ----------
# before_job = ["calicut_textiles.utils.before_job"]
# after_job = ["calicut_textiles.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

fixtures =[
    {"dt":"Custom Field","filters":[["module","in",["Calicut Textiles"]]]},
    {"dt":"Property Setter","filters":[["module","in",["Calicut Textiles"]]]}
]



# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
