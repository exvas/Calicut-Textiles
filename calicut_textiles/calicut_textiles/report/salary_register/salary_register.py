# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import flt

import erpnext  # Ensure the ERPNext module is imported

salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")
salary_component = frappe.qb.DocType("Salary Component")


def execute(filters=None):
    if not filters:
        filters = {}

    currency = filters.get("currency")
    company_currency = erpnext.get_company_currency(filters.get("company"))

    salary_slips = get_salary_slips(filters, company_currency)
    if not salary_slips:
        return [], []

    earning_types, ded_types = get_earning_and_deduction_types(salary_slips)
    columns = get_columns(earning_types, ded_types)

    ss_earning_map = get_salary_slip_details(salary_slips, currency, company_currency, "earnings")
    ss_ded_map = get_salary_slip_details(salary_slips, currency, company_currency, "deductions")

    doj_map = get_employee_doj_map()

    data = []
    for ss in salary_slips:
        custom_deducted_gross = ss.gross_pay - ss.total_deduction
        esi_lt = (
            custom_deducted_gross 
            if flt(custom_deducted_gross) < 21000 
            else 21000 
        )
        pf_lt = (
            (ss.custom_deducted_basic + ss.custom_deducted_da) 
            if flt(ss.custom_deducted_basic + ss.custom_deducted_da)  < 15000
            else 15000
        )
        print("rrrrrrr", esi_lt)
        print("ddddddddf", pf_lt)
        row = {
            "salary_slip_id": ss.name,
            "employee": ss.employee,
            "employee_name": ss.employee_name,
            "data_of_joining": doj_map.get(ss.employee),
            "branch": ss.branch,
            "department": ss.department,
            "designation": ss.designation,
            "company": ss.company,
            "start_date": ss.start_date,
            "end_date": ss.end_date,
            "leave_without_pay": ss.leave_without_pay,
            "absent_days": ss.absent_days,
            "payment_days": ss.payment_days,
            "currency": currency or company_currency,
            "total_loan_repayment": ss.total_loan_repayment,
            "esi_lt": esi_lt,
            "pf_lt": pf_lt,  # Added `pf_lt` to the row
        }

        for e in earning_types:
            row.update({frappe.scrub(e): ss_earning_map.get(ss.name, {}).get(e)})

        for d in ded_types:
            row.update({frappe.scrub(d): ss_ded_map.get(ss.name, {}).get(d)})

        if currency == company_currency:
            row.update(
                {
                    "gross_pay": flt(ss.gross_pay) * flt(ss.exchange_rate),
                    "total_deduction": flt(ss.total_deduction) * flt(ss.exchange_rate),
                    "net_pay": flt(ss.net_pay) * flt(ss.exchange_rate),
                }
            )
        else:
            row.update(
                {"gross_pay": ss.gross_pay, "total_deduction": ss.total_deduction, "net_pay": ss.net_pay}
            )

        data.append(row)

    return columns, data


def get_columns(earning_types, ded_types):
    """
    Generate column definitions for the report.
    """
    columns = [
        {"fieldname": "salary_slip_id", "label": "Salary Slip ID", "fieldtype": "Data", "width": 150},
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "data_of_joining", "label": "Date of Joining", "fieldtype": "Date", "width": 120},
        {"fieldname": "branch", "label": "Branch", "fieldtype": "Link", "options": "Branch", "width": 120},
        {"fieldname": "department", "label": "Department", "fieldtype": "Link", "options": "Department", "width": 120},
        {"fieldname": "designation", "label": "Designation", "fieldtype": "Link", "options": "Designation", "width": 120},
        {"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 120},
        {"fieldname": "start_date", "label": "Start Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "end_date", "label": "End Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "leave_without_pay", "label": "Leave Without Pay", "fieldtype": "Int", "width": 150},
        {"fieldname": "absent_days", "label": "Absent Days", "fieldtype": "Int", "width": 120},
        {"fieldname": "payment_days", "label": "Payment Days", "fieldtype": "Int", "width": 120},
        {"fieldname": "currency", "label": "Currency", "fieldtype": "Data", "width": 100},
        {"fieldname": "total_loan_repayment", "label": "Total Loan Repayment", "fieldtype": "Currency", "width": 150},
        {"fieldname": "esi_lt", "label": "ESI LT", "fieldtype": "Currency", "width": 120},
        {"fieldname": "pf_lt", "label": "PF LT", "fieldtype": "Currency", "width": 120},
    ]

    for e in earning_types:
        columns.append(
            {"fieldname": frappe.scrub(e), "label": e, "fieldtype": "Currency", "width": 120}
        )

    for d in ded_types:
        columns.append(
            {"fieldname": frappe.scrub(d), "label": d, "fieldtype": "Currency", "width": 120}
        )

    columns.extend(
        [
            {"fieldname": "gross_pay", "label": "Gross Pay", "fieldtype": "Currency", "width": 150},
            {"fieldname": "total_deduction", "label": "Total Deduction", "fieldtype": "Currency", "width": 150},
            {"fieldname": "net_pay", "label": "Net Pay", "fieldtype": "Currency", "width": 150},
        ]
    )

    return columns


def get_salary_slips(filters, company_currency):
    doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

    query = frappe.qb.from_(salary_slip).select(salary_slip.star)

    if filters.get("docstatus"):
        query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

    if filters.get("from_date"):
        query = query.where(salary_slip.start_date >= filters.get("from_date"))

    if filters.get("to_date"):
        query = query.where(salary_slip.end_date <= filters.get("to_date"))

    if filters.get("company"):
        query = query.where(salary_slip.company == filters.get("company"))

    if filters.get("employee"):
        query = query.where(salary_slip.employee == filters.get("employee"))

    if filters.get("currency") and filters.get("currency") != company_currency:
        query = query.where(salary_slip.currency == filters.get("currency"))

    return query.run(as_dict=1) or []


def get_earning_and_deduction_types(salary_slips):
    salary_component_and_type = {"Earning": [], "Deduction": []}

    for salary_component in get_salary_components(salary_slips):
        component_type = frappe.db.get_value("Salary Component", salary_component, "type", cache=True)
        salary_component_and_type[component_type].append(salary_component)

    return sorted(salary_component_and_type["Earning"]), sorted(salary_component_and_type["Deduction"])


def get_salary_components(salary_slips):
    return (
        frappe.qb.from_(salary_detail)
        .where((salary_detail.amount != 0) & (salary_detail.parent.isin([d.name for d in salary_slips])))
        .select(salary_detail.salary_component)
        .distinct()
    ).run(pluck=True)


def get_employee_doj_map():
    employee = frappe.qb.DocType("Employee")
    result = (frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)).run()
    return frappe._dict(result)


def get_salary_slip_details(salary_slips, currency, company_currency, component_type):
    salary_slips = [ss.name for ss in salary_slips]

    result = (
        frappe.qb.from_(salary_slip)
        .join(salary_detail)
        .on(salary_slip.name == salary_detail.parent)
        .where((salary_detail.parent.isin(salary_slips)) & (salary_detail.parentfield == component_type))
        .select(
            salary_detail.parent,
            salary_detail.salary_component,
            salary_detail.amount,
            salary_slip.exchange_rate,
        )
    ).run(as_dict=1)

    ss_map = {}

    for d in result:
        ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, 0.0)
        if currency == company_currency:
            ss_map[d.parent][d.salary_component] += flt(d.amount) * flt(
                d.exchange_rate if d.exchange_rate else 1
            )
        else:
            ss_map[d.parent][d.salary_component] += flt(d.amount)

    return ss_map
