import frappe



def calculate_deducted_gross(doc, method):
    total_deducted_amount = 0
    base_amount = 0

    base_amount = frappe.db.get_value("Salary Structure Assignment", {"employee": doc.employee}, "base", order_by="creation desc")

    for row in doc.deductions:
        if row.custom_is_late_early:
            total_deducted_amount += row.amount
    deducted_gross = base_amount - total_deducted_amount

    doc.custom_deducted_gross = deducted_gross
    doc.custom_deducted_per_day = deducted_gross/doc.payment_days
    doc.custom_deducted_basic = deducted_gross/100*62.5
    doc.custom_deducted_da = deducted_gross/100*40

