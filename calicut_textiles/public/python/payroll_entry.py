import frappe
from frappe.utils import getdate, add_days, get_time
from datetime import datetime, timedelta, time
from collections import defaultdict

# =====================================================
# CONFIG
# =====================================================

# =====================================================
# VALIDATIONS
# =====================================================
def validate_leave_type(leave_type, context):
    if not frappe.db.exists("Leave Type", leave_type):
        frappe.throw(
            f"Leave Type {leave_type} not found for {context}.",
            title="Invalid Leave Type"
        )

def get_max_consecutive_leave(leave_type):
    value = frappe.db.get_value(
        "Leave Type",
        leave_type,
        "max_continuous_days_allowed"
    )
    if not value:
        frappe.throw(
            f"Max Continuous Leave not set for {leave_type}.",
            title="Leave Type Configuration Error"
        )
    return int(value)

def get_leave_encashment_component(leave_type):
    component = frappe.db.get_value(
        "Leave Type",
        leave_type,
        "earning_component"
    )
    if not component:
        frappe.throw(
            f"Earning Component not set for {leave_type}.",
            title="Leave Type Configuration Error"
        )
    return component

# =====================================================
# ENTRY POINT
# =====================================================
@frappe.whitelist()
def enqueue_payroll_processing(payroll_entry):
    settings = frappe.get_single("Calicut Textiles Settings")
    leave_type = settings.leave_type
    if leave_type:
        process_payroll_entry(payroll_entry)
    else:
        frappe.throw(
            f"Leave Type {leave_type} not found for Payroll Processing.",
            title="Invalid Leave Type"
        )

# =====================================================
# MAIN PAYROLL FLOW
# =====================================================
def process_payroll_entry(payroll_entry):
    pe = frappe.get_doc("Payroll Entry", payroll_entry)

    employees = [
        row.employee for row in pe.employees
        if not row.is_salary_withheld
    ]

    if not employees:
        frappe.throw("No eligible employees found.")

    start_date = getdate(pe.start_date)
    end_date = getdate(pe.end_date)

    employee_map = load_employees(employees)
    holiday_map = load_holidays(employee_map)
    checkin_map = load_checkins(employees, start_date, end_date)

    create_overtime(
        pe, employees, employee_map, checkin_map
    )

    for emp in employees:
        process_attendance(
            emp,
            start_date,
            end_date,
            employee_map,
            holiday_map,
            checkin_map
        )

# =====================================================
# DATA LOADERS
# =====================================================
def load_employees(employees):
    data = frappe.get_all(
        "Employee",
        filters={"name": ["in", employees]},
        fields=["name", "holiday_list", "default_shift"]
    )
    return {d.name: d for d in data}

def load_holidays(employee_map):
    holiday_lists = {
        e.holiday_list for e in employee_map.values()
        if e.holiday_list
    }

    holidays = frappe.get_all(
        "Holiday",
        filters={"parent": ["in", list(holiday_lists)]},
        fields=["parent", "holiday_date"]
    )

    holiday_map = defaultdict(set)
    for h in holidays:
        holiday_map[h.parent].add(h.holiday_date)

    return holiday_map

def load_checkins(employees, start, end):
    rows = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": ["in", employees],
            "time": ["between", [start, end + timedelta(days=1)]]
        },
        fields=["employee", "time", "custom_late_early"],
        order_by="time asc"
    )

    result = defaultdict(lambda: defaultdict(list))
    for r in rows:
        result[r.employee][r.time.date()].append(r)

    return result

# =====================================================
# OVERTIME
# =====================================================
def create_overtime(pe, employees, employee_map, checkin_map):
    settings = frappe.get_single("Calicut Textiles Settings")
    threshold = settings.threshold_overtime_minutes or 0
    excluded_shift = settings.shift
    ot_component = settings.ot_component
    early_threshold = settings.threshold_early_minutes or 0
    early_component = settings.early_component

    for emp in employees:
        if frappe.db.exists(
            "Additional Salary",
            {
                "employee": emp,
                "salary_component": ot_component,
                "payroll_date": pe.end_date,
                "custom_is_overtime": 1,
                "docstatus": 1
            }
        ):
            continue

        shift_name = employee_map[emp].default_shift
        if not shift_name or shift_name == excluded_shift:
            continue

        shift = frappe.get_doc("Shift Type", shift_name)
        shift_hours = get_shift_hours(shift)
        if shift_hours <= 0:
            continue

        total_ot_minutes = 0
        total_early_minutes = 0

        for date, rows in checkin_map[emp].items():
            times = filter_noise([r.time for r in rows])
            if len(times) < 2:
                continue

            in_time, out_time = times[0], times[-1]
            shift_start, shift_end = shift_bounds(shift, date)

            normal_start = shift_start - timedelta(minutes=threshold)
            normal_end = shift_end + timedelta(minutes=threshold)

            if in_time < normal_start:
                total_ot_minutes += threshold + minutes(normal_start - in_time)

            if out_time > normal_end:
                total_ot_minutes += threshold + minutes(out_time - normal_end)

            for r in rows:
                if r.custom_late_early and r.custom_late_early > early_threshold:
                    total_early_minutes += r.custom_late_early

        rate = get_per_minute_salary(emp, pe.start_date, pe.end_date, shift_hours)

        if total_ot_minutes > 0:
            create_monthly_overtime(
                emp,
                pe.end_date,
                total_ot_minutes,
                round(rate * total_ot_minutes, 2),
                ot_component
            )
        elif total_early_minutes > 0:
            create_monthly_additional_salary(
                emp,
                pe.end_date,
                round(rate * total_early_minutes, 2),
                early_component
            )

# =====================================================
# ATTENDANCE / LEAVE
# =====================================================
def process_attendance(emp, start, end, employee_map, holiday_map, checkin_map):
    settings = frappe.get_single("Calicut Textiles Settings")
    leave_type = settings.leave_type
    holidays = holiday_map.get(
        employee_map[emp].holiday_list,
        set()
    )

    working_days = set()
    current = start
    while current <= end:
        if current not in holidays:
            working_days.add(current)
        current = add_days(current, 1)

    present_days = set(checkin_map[emp].keys())
    missing_days = sorted(working_days - present_days)

    max_leave = get_max_consecutive_leave(leave_type)
    used_leave = count_existing_leave(emp, start, end)

    for d in missing_days:
        if used_leave < max_leave:
            create_leave_application(emp, d)
            used_leave += 1
        else:
            mark_absent(emp, d)

    encash = max_leave - used_leave
    if encash > 0:
        create_leave_encashment(emp, end, encash)

# =====================================================
# HELPERS
# =====================================================
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

def get_shift_hours(shift):
    s, e = shift_bounds(shift, getdate())
    return (e - s).total_seconds() / 3600

def minutes(delta):
    return int(delta.total_seconds() / 60)

def get_per_minute_salary(emp, start, end, shift_hours):
    base = frappe.db.get_value(
        "Salary Structure Assignment",
        {"employee": emp, "docstatus": 1},
        "base",
        order_by="from_date desc"
    )
    if not base:
        return 0

    days = (getdate(end) - getdate(start)).days + 1
    return base / (days * shift_hours * 60)

# =====================================================
# DOCUMENT CREATORS
# =====================================================
def create_monthly_additional_salary(emp, date, amount, component):
    if amount <= 0:
        return
    if frappe.db.exists(
        "Additional Salary",
        {
            "employee": emp,
            "salary_component": component,
            "payroll_date": date,
            "docstatus": 1
        }
    ):
        return
    doc = frappe.new_doc("Additional Salary")
    doc.employee = emp
    doc.salary_component = component
    doc.amount = amount
    doc.payroll_date = date
    doc.docstatus = 1
    doc.insert(ignore_permissions=True)

def create_monthly_overtime(emp, date, minutes, amount, component):
    if amount <= 0:
        return
    doc = frappe.new_doc("Additional Salary")
    doc.employee = emp
    doc.salary_component = component
    doc.custom_is_overtime = 1
    doc.custom_ot_min = minutes
    doc.amount = amount
    doc.payroll_date = date
    doc.docstatus = 1
    doc.insert(ignore_permissions=True)

# =====================================================
# LEAVE
# =====================================================
def count_existing_leave(emp, start, end):
    settings = frappe.get_single("Calicut Textiles Settings")
    leave_type = settings.leave_type
    return frappe.db.count(
        "Leave Application",
        {
            "employee": emp,
            "leave_type": leave_type,
            "docstatus": 1,
            "from_date": ["<=", end],
            "to_date": [">=", start]
        }
    )

def create_leave_application(emp, date):
    settings = frappe.get_single("Calicut Textiles Settings")
    leave_type = settings.leave_type
    doc = frappe.new_doc("Leave Application")
    doc.employee = emp
    doc.leave_type = leave_type
    doc.from_date = date
    doc.to_date = date
    doc.status = "Approved"
    doc.docstatus = 1
    doc.insert(ignore_permissions=True)

def mark_absent(emp, date):
    if frappe.db.exists(
        "Attendance",
        {"employee": emp, "attendance_date": date}
    ):
        return
    doc = frappe.new_doc("Attendance")
    doc.employee = emp
    doc.attendance_date = date
    doc.status = "Absent"
    doc.docstatus = 1
    doc.insert(ignore_permissions=True)

def create_leave_encashment(emp, date, days):
    settings = frappe.get_single("Calicut Textiles Settings")
    leave_type = settings.leave_type
    component = get_leave_encashment_component(leave_type)
    if frappe.db.exists(
        "Additional Salary",
        {
            "employee": emp,
            "salary_component": component,
            "docstatus": 1
        }
    ):
        return

    daily = frappe.db.get_value(
        "Salary Structure Assignment",
        {"employee": emp, "docstatus": 1},
        "custom_leave_encashment_amount_per_day",
        order_by="from_date desc"
    )

    if not daily:
        return

    doc = frappe.new_doc("Additional Salary")
    doc.employee = emp
    doc.salary_component = component
    doc.amount = round(daily * days, 2)
    doc.payroll_date = date
    doc.docstatus = 1
    doc.insert(ignore_permissions=True)

def to_time(value):
    if isinstance(value, timedelta):
        secs = int(value.total_seconds())
        return time(secs // 3600, (secs % 3600) // 60, secs % 60)
    return value
