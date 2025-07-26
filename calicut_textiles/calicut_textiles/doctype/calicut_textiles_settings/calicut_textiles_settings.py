# Copyright (c) 2024, sammish and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, time, timedelta
from frappe.utils import get_first_day, get_last_day
from frappe.model.document import Document
import calendar
from collections import defaultdict
import pytz
import json



class CalicutTextilesSettings(Document):
	pass


@frappe.whitelist()
def reset_late_early():
    """Method to reset the Log type and early late calculation"""
    today = frappe.utils.today()
    current_month_start = get_first_day(today)
    current_month_end = get_last_day(today)

    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "time": ["between", [current_month_start, current_month_end]]
        },
        fields=[
            "name",
            "employee",
            "log_type",
            "time",
            "shift",
            "custom_late_coming_minutes",
            "custom_early_going_minutes",
            "custom_late_early"
        ],
        order_by="employee, time ASC"
    )

    checkin_data = defaultdict(lambda: defaultdict(list))

    for checkin in checkins:
        date_str = checkin.time.date().isoformat()
        checkin_data[checkin.employee][date_str].append(checkin)

    for employee, dates in checkin_data.items():
        for date, entries in dates.items():
            entries_sorted = sorted(entries, key=lambda x: x["time"])

            if not entries_sorted:
                continue

            first_entry = entries_sorted[0]

            if len(entries_sorted) == 1:
                # Only one entry for the day: set as IN
                frappe.db.set_value("Employee Checkin", first_entry["name"], {
                    "log_type": "IN"
                })
                first_entry["log_type"] = "IN"
                last_entry = None
            else:
                last_entry = entries_sorted[-1]
                # Set first entry as IN
                frappe.db.set_value("Employee Checkin", first_entry["name"], {
                    "log_type": "IN"
                })
                # Set last entry as OUT
                frappe.db.set_value("Employee Checkin", last_entry["name"], {
                    "log_type": "OUT"
                })
                first_entry["log_type"] = "IN"
                last_entry["log_type"] = "OUT"

            # Calculate late coming minutes
            late = 0
            if first_entry:
                late = calculate_late_minutes(first_entry)
                frappe.db.set_value("Employee Checkin", first_entry["name"], {
                    "custom_late_coming_minutes": late
                })

            # Calculate early going minutes
            early = 0
            if last_entry:
                early = calculate_early_minutes(last_entry)
                frappe.db.set_value("Employee Checkin", last_entry["name"], {
                    "custom_early_going_minutes": early
                })

            total = late + early

            # Update combined late and early minutes
            frappe.db.set_value("Employee Checkin", first_entry["name"], {
                "custom_late_early": total
            })
            if last_entry and last_entry["name"] != first_entry["name"]:
                frappe.db.set_value("Employee Checkin", last_entry["name"], {
                    "custom_late_early": total
                })

    frappe.db.commit()
    return "Done"

def calculate_late_minutes(checkin):
    if not checkin.get("shift"):
        return 0

    try:
        shift = frappe.get_doc("Shift Type", checkin["shift"])
    except frappe.DoesNotExistError:
        return 0

    shift_start = timedelta_to_time(shift.start_time)
    grace = 10

    checkin_time = checkin["time"]
    shift_datetime = datetime.combine(checkin_time.date(), shift_start)
    grace_end = shift_datetime + timedelta(minutes=grace)


    if checkin_time > grace_end:
        return int((checkin_time - grace_end).total_seconds() / 60)
    return 0


def calculate_early_minutes(checkout):
    if not checkout.get("shift"): return 0

    shift = frappe.get_doc("Shift Type", checkout["shift"])
    shift_end = timedelta_to_time(shift.end_time)
    grace = 10

    checkout_time = checkout["time"]
    shift_datetime = datetime.combine(checkout_time.date(), shift_end)
    grace_start = shift_datetime - timedelta(minutes=grace)

    if checkout_time < grace_start:
        return int((grace_start - checkout_time).total_seconds() / 60)
    return 0


def timedelta_to_time(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return time(hour=hours, minute=minutes, second=seconds)
