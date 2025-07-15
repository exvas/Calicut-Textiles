import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta, time as dtime


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




@frappe.whitelist()
def update_employee_checkin_fields(doc, method):
    """Calculate Late Entry and early Going """
    if not doc.employee or not doc.time or not doc.log_type:
        return

    default_shift = frappe.db.get_value("Employee", doc.employee, "default_shift")
    if not default_shift:
        return

    shift = frappe.get_doc("Shift Type", default_shift)
    if not shift.start_time or not shift.end_time:
        return

    time_obj = doc.time
    start_time = as_time(shift.start_time)
    end_time = as_time(shift.end_time)

    shift_start = datetime.combine(time_obj.date(), start_time)
    shift_end = datetime.combine(time_obj.date(), end_time)

    if shift_end <= shift_start:
        shift_end += timedelta(days=1)

    total_hours = (shift_end - shift_start).seconds / 3600
    doc.custom_total_hours = round(total_hours, 2)

    if doc.log_type == 'IN':
        diff_minutes = int((time_obj - shift_start).total_seconds() / 60)
        doc.custom_late_coming_minutes = diff_minutes if diff_minutes > 10 else 0

    elif doc.log_type == 'OUT':
        diff_minutes = int((shift_end - time_obj).total_seconds() / 60)
        doc.custom_early_going_minutes = diff_minutes if diff_minutes > 20 else 0

        # IN check-in on same day
        in_checkin = frappe.db.get_value("Employee Checkin", {
            "employee": doc.employee,
            "log_type": "IN",
            "time": ["between", [time_obj.date().strftime('%Y-%m-%d') + " 00:00:00",
                                 time_obj.date().strftime('%Y-%m-%d') + " 23:59:59"]],
            "docstatus": ["<", 2]
        }, ["custom_late_coming_minutes"])

        late = in_checkin or 0
        early = doc.custom_early_going_minutes or 0
        doc.custom_late_coming_minutes = late
        doc.custom_late_early = float(late) + float(early)


def as_time(value):
    """Convert timedelta or string to datetime.time."""
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return dtime(hour=hours, minute=minutes, second=seconds)
    elif isinstance(value, dtime):
        return value
    else:
        return datetime.strptime(value, "%H:%M:%S").time()
