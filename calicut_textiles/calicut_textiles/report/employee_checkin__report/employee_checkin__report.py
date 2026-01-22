import frappe
from datetime import datetime, timedelta, time
from collections import defaultdict
from frappe.utils import getdate, add_days


def execute(filters=None):
    filters = filters or {}
    columns, data = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 200},
        {"fieldname": "checkin_time", "label": "Check-in Time", "fieldtype": "Datetime", "width": 200},
        {"fieldname": "checkout_time", "label": "Check-out Time", "fieldtype": "Datetime", "width": 200},
        {"fieldname": "late_early_minutes", "label": "Late/Early Minutes", "fieldtype": "Float", "width": 150},
        {"fieldname": "overtime_minutes", "label": "Overtime Minutes", "fieldtype": "Float", "width": 150},
        {"fieldname": "work_duration_minutes", "label": "Work Duration (Minutes)", "fieldtype": "Float", "width": 180},
    ]

def get_data(filters):
    settings = frappe.get_single("Calicut Textiles Settings")

    threshold = settings.threshold_overtime_minutes or 0
    excluded_shift = settings.shift
    early_threshold = settings.threshold_early_minutes or 0

    employee_filter = {"status": "Active"}
    if filters.get("employee"):
        employee_filter = {"name": filters.get("employee"), "status": "Active"}

    employees = frappe.get_all("Employee", filters=employee_filter, fields=["name", "default_shift", "holiday_list", "employment_type"])
    employees_list = [e.name for e in employees]

    checkin_map = load_checkins(employees_list, filters.get("from_date"), filters.get("to_date"))
    holiday_map = load_holidays(employees)

    data = []

    for emp in employees:
        if not emp.default_shift or emp.default_shift == excluded_shift:
            continue
        if emp.employment_type == "Part-time":
            continue

        shift = frappe.get_doc("Shift Type", emp.default_shift)
        holidays = holiday_map.get(emp.holiday_list, set())

        for date, rows in checkin_map.get(emp.name, {}).items():
            times = filter_noise([r.time for r in rows])
            if len(times) < 2:
                continue

            in_time = times[0]
            out_time = times[-1]

            overtime_minutes = 0
            late_early_minutes = 0

            worked_minutes = minutes(out_time - in_time)

            # -------- HOLIDAY LOGIC --------
            if date in holidays:
                overtime_minutes = worked_minutes
                data.append({
                    "employee": emp.name,
                    "checkin_time": in_time,
                    "checkout_time": out_time,
                    "late_early_minutes": 0,
                    "overtime_minutes": overtime_minutes,
                    "work_duration_minutes": worked_minutes
                })
                continue

            shift_start, shift_end = shift_bounds(shift, date)

            normal_start = shift_start - timedelta(minutes=threshold)
            normal_end = shift_end + timedelta(minutes=threshold)

            late_start = shift_start + timedelta(minutes=early_threshold)
            early_end = shift_end - timedelta(minutes=early_threshold)

            # -------- OVERTIME --------
            if in_time < normal_start:
                overtime_minutes += minutes(normal_start - in_time)
            if out_time > normal_end:
                overtime_minutes += minutes(out_time - normal_end)

            # -------- LATE / EARLY --------
            if in_time > late_start:
                late_early_minutes += minutes(in_time - late_start)
            if out_time < early_end:
                late_early_minutes += minutes(early_end - out_time)

            data.append({
                "employee": emp.name,
                "employee_name": frappe.get_value("Employee", emp.name, "employee_name"),
                "checkin_time": in_time,
                "checkout_time": out_time,
                "late_early_minutes": late_early_minutes,
                "overtime_minutes": overtime_minutes,
                "work_duration_minutes": worked_minutes
            })

    return data

def load_checkins(employees, start, end):
    rows = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": ["in", employees],
            "time": ["between", [start, add_days(end, 1)]]
        },
        fields=["employee", "time"],
        order_by="time asc"
    )

    result = defaultdict(lambda: defaultdict(list))
    for r in rows:
        result[r.employee][r.time.date()].append(r)

    return result


def load_holidays(employees):
    holiday_lists = {e.holiday_list for e in employees if e.holiday_list}

    holidays = frappe.get_all(
        "Holiday",
        filters={"parent": ["in", list(holiday_lists)]},
        fields=["parent", "holiday_date"]
    )

    holiday_map = defaultdict(set)
    for h in holidays:
        holiday_map[h.parent].add(h.holiday_date)

    return holiday_map

def minutes(delta):
    return int(delta.total_seconds() / 60)

def filter_noise(times):
    clean, last = [], None
    for t in times:
        if not last or (t - last).total_seconds() > 300:
            clean.append(t)
            last = t
    return clean

def shift_bounds(shift, date):
    start = datetime.combine(date, to_time(shift.start_time))
    end = datetime.combine(date, to_time(shift.end_time))
    if end <= start:
        end += timedelta(days=1)
    return start, end

def to_time(value):
    if isinstance(value, timedelta):
        secs = int(value.total_seconds())
        return time(secs // 3600, (secs % 3600) // 60, secs % 60)
    return value
