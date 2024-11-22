from frappe import _

def get_data():
	return {
		"fieldname": "custom_bulk_employee_advance",
		"non_standard_fieldnames": {
			"Employee Advance": "custom_bulk_employee_advance",
			"Additional Salary": "custom_bulk_employee_advance"
			
		},
		
		"transactions": [
            {"label": _("Related"), "items": ["Employee Advance", "Additional Salary"]},
							
		],
    }