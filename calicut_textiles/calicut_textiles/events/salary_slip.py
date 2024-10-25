import frappe
from frappe.utils import getdate, month_diff
# from hrms.payroll.doctype.salary_slip.salary_slip import get_working_days_details


def before_save(doc, method):
    if doc.employee and doc.start_date:
        without_pay = frappe.db.get_list(
            "Leave Application",
            filters={
                "employee": doc.employee,
                "leave_type": "Leave Without Pay",
                "status": "Approved",
                "from_date": [">=", doc.start_date],
                "to_date": ["<=", doc.end_date]
            },
            fields=["total_leave_days"]
        )
        
        total_without_pay_days = sum(leave.total_leave_days for leave in without_pay) if without_pay else 0
      
        per_day = frappe.db.get_value("Salary Structure Assignment", {"employee": doc.employee}, "custom_leave_encashment_amount_per_day", order_by="creation desc")
        
        lop = per_day * total_without_pay_days
       
        deducted_gross = calculate_deducted_gross(doc.employee, doc.start_date) - lop
        
        if deducted_gross:
            doc.custom_deducted_gross = deducted_gross
            doc.custom_deducted_basic = deducted_gross * 62.5 / 100
            doc.custom_deducted_da = deducted_gross * 40 / 100



@frappe.whitelist()
def calculate_deducted_gross(employee, start_date):
    base_amount = 0
    deducted_gross = 0

    late_component = frappe.db.get_value("Calicut Textiles Settings", None, "early_component")

    base_amount = frappe.db.get_value("Salary Structure Assignment", {"employee": employee}, "base", order_by="creation desc")

    start_date = getdate(start_date)

    additional_salaries = frappe.get_all(
        "Additional Salary", 
        filters={
            "employee": employee,
            "Salary_component": late_component,
            "custom_is_late_early": 1,
            "docstatus": 1
        },
        fields=["amount", "payroll_date"]
    )

    lop = 0  
    for additional_salary in additional_salaries:
        payroll_date = getdate(additional_salary.get('payroll_date'))
        
        if payroll_date and payroll_date.month == start_date.month and payroll_date.year == start_date.year:
            lop = additional_salary.get('amount')

    if lop:
        deducted_gross = base_amount - lop
    else:
        deducted_gross = base_amount

    return deducted_gross
