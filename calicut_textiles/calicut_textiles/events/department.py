import frappe
from frappe.utils.nestedset import NestedSet, get_root_of

from erpnext.utilities.transaction_base import delete_events
from erpnext.setup.doctype.department.department import Department


class CustomDepartment(Department):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		company: DF.Link
		department_name: DF.Data
		disabled: DF.Check
		is_group: DF.Check
		lft: DF.Int
		old_parent: DF.Data | None
		parent_department: DF.Link | None
		rgt: DF.Int
	# end: auto-generated types

	nsm_parent_field = "parent_department"

	def autoname(self):
		root = get_root_of("Department")
		if root and self.department_name != root:
			self.name = get_abbreviated_name(self.department_name, self.company)
		else:
			self.name = self.department_name
			
def get_abbreviated_name(name, company):
    abbr = frappe.get_cached_value("Company", company, "abbr")
    new_name = f"{name}"
    return new_name