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
import math

class CalicutTextilesSettings(Document):
    pass


@frappe.whitelist()
def reset_late_early(from_date=None, to_date=None):
    from_date = from_date or get_first_day(frappe.utils.today())
    to_date = to_date or get_last_day(frappe.utils.today())

    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "time": ["between", [from_date, to_date]]
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
        emp = frappe.get_doc("Employee", employee)
        for date, entries in dates.items():
            entries_sorted = sorted(entries, key=lambda x: x["time"])

            if not entries_sorted:
                continue

            checkin_date = entries_sorted[0]["time"].date()
            if emp.holiday_list == "CT Holidays" and checkin_date.weekday() == 6:
                for entry in entries_sorted:
                    frappe.db.set_value("Employee Checkin", entry["name"], {
                        "custom_late_coming_minutes": 0,
                        "custom_early_going_minutes": 0,
                        "custom_late_early": 0
                    })
                continue

            # Mark first and last entry
            first_entry = entries_sorted[0]
            last_entry = entries_sorted[-1]

            frappe.db.set_value("Employee Checkin", first_entry["name"], {"log_type": "IN"})
            first_entry["log_type"] = "IN"

            if first_entry["name"] != last_entry["name"]:
                frappe.db.set_value("Employee Checkin", last_entry["name"], {"log_type": "OUT"})
                last_entry["log_type"] = "OUT"

            # Reset intermediate entries (between first and last)
            for inter_entry in entries_sorted[1:-1]:
                frappe.db.set_value("Employee Checkin", inter_entry["name"], {
                    "custom_late_coming_minutes": 0,
                    "custom_early_going_minutes": 0,
                    "custom_late_early": 0
                })

            # Calculate late coming (only first IN)
            late = calculate_late_minutes(first_entry) if first_entry else 0
            frappe.db.set_value("Employee Checkin", first_entry["name"], {
                "custom_late_coming_minutes": late
            })

            # Calculate early going (only last OUT if exists)
            early = calculate_early_minutes(last_entry) if last_entry else 0
            frappe.db.set_value("Employee Checkin", last_entry["name"], {
                "custom_early_going_minutes": early
            })

            # Combined late + early
            total = late + early
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
        diff_seconds = (checkin_time - shift_datetime).total_seconds()
        diff_minutes = int(diff_seconds // 60)
        return diff_minutes
    return 0

def calculate_early_minutes(checkout):
    if not checkout.get("shift"):
        return 0

    try:
        shift = frappe.get_doc("Shift Type", checkout["shift"])
    except frappe.DoesNotExistError:
        return 0

    shift_end = timedelta_to_time(shift.end_time)
    grace = 10
    checkout_time = checkout["time"]
    shift_datetime = datetime.combine(checkout_time.date(), shift_end)
    grace_start = shift_datetime - timedelta(minutes=grace)

    if checkout_time < grace_start:
        diff_seconds = (shift_datetime - checkout_time).total_seconds()
        diff_minutes = math.ceil(diff_seconds / 60)
        return int(diff_minutes)

    return 0


def timedelta_to_time(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return time(hour=hours, minute=minutes, second=seconds)
