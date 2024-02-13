import frappe
from frappe import NotFound
from frappe.utils import getdate


def set_attendance_data(**kwargs):
    data = kwargs.get('data')
    photo = data.get('photo')
    image = photo.get('file_url')
    custom_customer = data.get('custom_customer') if data.get('custom_customer') else ''
    custom_call_type = data.get('custom_call_type') if data.get('custom_call_type') else ''
    custom_work_status = data.get('custom_work_status') if data.get('custom_work_status') else ''
    custom_comments = data.get('custom_comments') if data.get('custom_comments') else ''
    custom_documents_array = data.get('custom_documents') if data.get('custom_documents') else []
    custom_documents_obj = custom_documents_array[0] if len(custom_documents_array) > 0 else {}
    custom_documents = custom_documents_obj.get('file_url') if custom_documents_obj.get('file_url') else ''

    user = frappe.session.user
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    if not employee:
        raise frappe.NotFound("Employee not found")
    attendance = frappe.db.get_value("Attendance",
                                     {"employee": employee.get('name'), "attendance_date": frappe.utils.today()})
    if attendance:
        attendance = frappe.get_doc("Attendance", attendance)
        attendance.custom_photo = image
        attendance.custom_customer = custom_customer
        attendance.custom_call_type = custom_call_type
        attendance.custom_work_status = custom_work_status.capitalize()
        attendance.custom_comments = custom_comments
        attendance.custom_documents = custom_documents
        attendance.save(ignore_permissions=True)
        return True
    return False

@frappe.whitelist()
def mark_checkin(**kwargs):
    user = frappe.session.user
    data = kwargs.get('data')
    photo = data.get('photo')
    image = photo.get('file_url')
    datetime = frappe.utils.now_datetime()
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    if not employee:
        raise frappe.NotFound("Employee not found")
    attendance_doc = frappe.new_doc('Attendance')
    attendance_doc.employee = employee.get('name')
    attendance_doc.attendance_date = frappe.utils.today()
    attendance_doc.in_time = datetime
    attendance_doc.custom_photo_checkin = image
    attendance_doc.insert(ignore_permissions=True)

    checkin_doc = frappe.new_doc('Employee Checkin')
    checkin_doc.employee = employee.get('name')
    checkin_doc.time = datetime
    checkin_doc.log_type = "IN"
    checkin_doc.attendance = attendance_doc.name
    checkin_doc.save(ignore_permissions=True)
    return attendance_doc.name

@frappe.whitelist()
def mark_checkout():
    datetime = frappe.utils.now_datetime()
    user = frappe.session.user
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    if not employee:
        raise NotFound("Employee not found")
    attendance_doc = frappe.db.get_value("Attendance",
                                         {"employee": employee.get('name'), "attendance_date": frappe.utils.today()})
    if not attendance_doc:
        raise NotFound("Attendance not found")
    checkout_doc = frappe.new_doc('Employee Checkin')
    checkout_doc.employee = employee.get('name')
    checkout_doc.time = datetime
    checkout_doc.log_type = "OUT"
    checkout_doc.attendance = attendance_doc
    checkout_doc.insert(ignore_permissions=True)

    attendance_doc = frappe.get_doc("Attendance", attendance_doc)
    attendance_doc.out_time = datetime
    duration = (getdate(attendance_doc.out_time) - getdate(attendance_doc.in_time)).total_seconds()
    attendance_doc.custom_duration = duration
    attendance_doc.save(ignore_permissions=True)
    attendance_doc.submit()
    return attendance_doc.name


@frappe.whitelist()
def has_employee_checked_in_today():
    user = frappe.session.user
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    print(user)
    if not employee:
        raise frappe.NotFound("Employee not found")
    attendance = frappe.db.get_value("Attendance",
                                     {"employee": employee.get('name'), "attendance_date": frappe.utils.today()})
    if attendance:
        return True
    return False


@frappe.whitelist()
def has_employee_checked_out_today():
    user = frappe.session.user
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    if not employee:
        raise frappe.NotFound("Employee not found")
    attendance = frappe.db.get_value("Attendance",
                                     {"employee": employee.get('name'), "attendance_date": frappe.utils.today()})
    if attendance:
        attendance = frappe.get_doc("Attendance", attendance)
        if attendance.out_time:
            return True
    return False

@frappe.whitelist()
def validate_face(**kwargs):
    user = frappe.session.user
    image = kwargs.get('image')
    photo = frappe.get_doc("Photo", {'photo': image})
    people_array = photo.people
    if not photo.is_processed:
        raise frappe.ValidationError("Photo is not processed yet, Kindly Re-Click on submit in a few seconds")
    if not people_array:
        raise frappe.ValidationError("No face detected")
    if len(people_array) > 0:
        for person in people_array:
            face = frappe.get_doc("ROI", person.face)
            if face.person is None:
                continue
            person = frappe.get_doc('Person', face.person)
            if person.user != user:
                continue
            if face.person is not None and person.user == user:
                return True
        raise frappe.ValidationError("Face not matched")
    else:
        raise frappe.ValidationError("No face detected")

@frappe.whitelist()
def has_face_enrolled():
    user = frappe.session.user
    person = frappe.get_value("Person", {"user": user}, ["enrolled"], as_dict=True)
    if not person:
        return False
    if person.enrolled:
        return True
    return False
