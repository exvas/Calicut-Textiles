import frappe

@frappe.whitelist()
def get_late_minutes_from_in_log(employee, date):
    """Fetch custom_late_coming_minutes from IN check-in on same date"""
    record = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "log_type": "IN",
            "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]
        },
        fields=["custom_late_coming_minutes"],
        order_by="time ASC",
        limit=1
    )
    return record[0] if record else {}

