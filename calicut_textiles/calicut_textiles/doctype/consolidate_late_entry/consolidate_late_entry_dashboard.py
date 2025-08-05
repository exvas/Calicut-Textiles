from frappe import _


def get_data():
	return {
		"fieldname": "custom_consolidated_late_entry",
        "non_standard_fieldnames": {
			"Additional Salary": "custom_consolidated_late_entry"

		},
        
		"transactions": [
            {"label": _("Related"), "items": ["Additional Salary"]},
		],
    }
