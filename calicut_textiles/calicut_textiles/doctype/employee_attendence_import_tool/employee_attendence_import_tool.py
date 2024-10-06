# Copyright (c) 2024, sammish and contributors
# For license information, please see license.txt

import frappe
import csv
from frappe import _
from frappe.utils.file_manager import get_file
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file, read_xls_file_from_attached_file
from frappe.model.document import Document

class EmployeeAttendenceImportTool(Document):
    pass


@frappe.whitelist()
def import_attendance_data(file_name, payroll_date, docname):
    
    file_doc, extension = get_file_and_extension(file_name)

    if extension == "csv":
        data = generate_data_from_csv(file_doc, as_dict=True)
    else:
        data = generate_data_from_excel(file_doc, extension, as_dict=True)

    success_count = 0
    error_count = 0
    log = []


    for row in data:
        employee_code = row.get('employee_code')

        if not employee_code:
            frappe.throw("Employee Code is required for each row. Import aborted.")
        
        employee = frappe.db.get_value("Employee", {"attendance_device_id": employee_code}, "employee")

        if not employee:
            frappe.throw(f"Employee with code {employee_code} not found. Import aborted.")
        
        ot = row.get('ot_hours')
        late_coming_hours = row.get('late_coming_hours')
        early_going_hours = row.get('early_going_hours')

        try:
            # Create and populate a new Employee Punching Data document
            attendance_doc = frappe.new_doc('Employee Punching Data')
            attendance_doc.employee_code = employee_code
            attendance_doc.ot_hours = convert_time_to_minutes(ot) 
            attendance_doc.late_coming_hours = convert_time_to_minutes(late_coming_hours) 
            attendance_doc.early_going_hours = convert_time_to_minutes(early_going_hours)
            attendance_doc.payroll_date = payroll_date

            # Save and submit the document
            attendance_doc.save()
            attendance_doc.submit()
            success_count += 1

        except Exception as e:
            frappe.throw(f"Error for Employee Code: {employee_code}, OT Hours: {ot}, Late Coming Hours: {late_coming_hours}, Early Going Hours: {early_going_hours} - {str(e)}")

    # Update the Employee Attendance Import Tool document with the result and log
    frappe.db.set_value("Employee Attendence Import Tool", docname, "status", "Success" if error_count == 0 else "Failed")
    frappe.db.set_value("Employee Attendence Import Tool", docname, "import_log", "\n".join(log))

    return {"success_count": success_count, "error_count": error_count}


def convert_time_to_minutes(time_str):
    if not time_str:
        return 0  

    parts = list(map(int, time_str.split(':')))
    total_minutes = 0

    if len(parts) == 3:  # HH:MM:SS
        total_minutes = parts[0] * 60 + parts[1] + (parts[2] / 60)  # Convert to minutes
    elif len(parts) == 2:  # MM:SS
        total_minutes = parts[0] + (parts[1] / 60)  # Convert to minutes
    return int(total_minutes)  # Return as integer for minutes

def get_file_and_extension(file_name):
    file_doc = frappe.get_doc("File", {"file_url": file_name})
    file_url = file_doc.file_url or file_doc.file_name
    extension = file_url.split('.')[-1].lower()

    if extension not in ("csv", "xlsx", "xls"):
        frappe.throw(_("Only CSV and Excel files (XLS/XLSX) are allowed. Please check the file format."))

    return file_doc, extension

def generate_data_from_csv(file_doc, as_dict=False):
    file_path = file_doc.get_full_path()
    data = []

    with open(file_path) as in_file:
        csv_reader = list(csv.reader(in_file))
        headers = csv_reader[0]
        del csv_reader[0]  # Remove headers row

        for row in csv_reader:
            if as_dict:
                data.append({frappe.scrub(header): row[index] for index, header in enumerate(headers)})
            else:
                data.append(row)

    return data

def generate_data_from_excel(file_doc, extension, as_dict=False):
    content = file_doc.get_content()

    if extension == "xlsx":
        rows = read_xlsx_file_from_attached_file(fcontent=content)
    elif extension == "xls":
        rows = read_xls_file_from_attached_file(fcontent=content)

    data = []
    headers = rows[0]
    del rows[0]  # Remove headers row

    for row in rows:
        if as_dict:
            data.append({frappe.scrub(header): row[index] for index, header in enumerate(headers)})
        else:
            data.append(row)

    return data
