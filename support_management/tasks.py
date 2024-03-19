import frappe


def create_checkin(user, checkin_datetime):
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    already_checkin = frappe.db.get_value("Employee Checkin", {"employee": employee.get('name'), "log_type": "IN",
                                                               "custom_date_only": checkin_datetime.date() if type(
                                                                   checkin_datetime) != str else checkin_datetime[:10]},
                                          "name")
    if already_checkin:
        return already_checkin
    checkin = frappe.new_doc("Employee Checkin")
    checkin.employee = employee.get('name')
    checkin.time = checkin_datetime
    checkin.custom_checkin_type = "On Site"
    checkin.log_type = "IN"
    checkin.save(ignore_permissions=True)
    return checkin


def create_checkout(user, checkout_datetime):
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    already_checkout = frappe.db.get_value("Employee Checkin", {"employee": employee.get('name'), "log_type": "OUT",
                                                               "custom_date_only": checkout_datetime.date() if type(
                                                                   checkout_datetime) != str else checkout_datetime[
                                                                                                  :10]}, "name")
    if already_checkout:
        return already_checkout
    checkout = frappe.new_doc("Employee Checkin")
    checkout.employee = employee.get('name')
    checkout.time = checkout_datetime
    checkout.custom_checkin_type = "On Site"
    checkout.log_type = "OUT"
    checkout.save(ignore_permissions=True)
    return checkout


def create_attendance(user, checkin, checkout):
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    if frappe.db.exists("Attendance",
                        {"attendance_date": frappe.utils.today(),
                         "employee": employee.get("name")}):
        return frappe.db.get_value("Attendance",
                                   {"attendance_date": frappe.utils.today(),
                                    "employee": employee.get("name")})
    attendance = frappe.new_doc("Attendance")
    attendance.employee = employee.get('name')
    attendance.status = "Present"
    attendance.attendance_date = checkin.time.date()
    attendance.save(ignore_permissions=True)
    checkin.attendance = attendance
    checkout.attendance = attendance
    checkin.save(ignore_permissions=True)
    checkout.save(ignore_permissions=True)
    attendance.submit()
    return attendance


@frappe.whitelist(allow_guest=True)
def daily():
    from frappe.utils import get_datetime
    from_date = get_datetime(frappe.utils.today() + " 00:00:00")
    to_date = get_datetime(frappe.utils.today() + " 23:59:59")
    engineer_visits = frappe.get_all("Maintenance Visit", filters=[
        ["Maintenance Visit", "custom_checkin_time", "between", [from_date, to_date]],
        ["Maintenance Visit", "custom_assigned_engineer", "!=", ""],
        ["Maintenance Visit", "custom_checkout_time", "!=", None]
    ], fields=["*"])

    persons = dict()

    for engineer_visit in engineer_visits:
        if engineer_visit.custom_assigned_engineer:
            if engineer_visit.custom_assigned_engineer in persons:
                persons[engineer_visit.custom_assigned_engineer].append(engineer_visit)
            else:
                persons[engineer_visit.custom_assigned_engineer] = [engineer_visit]
        if engineer_visit.custom_additional_engineer:
            if engineer_visit.custom_additional_engineer in persons:
                persons[engineer_visit.custom_additional_engineer].append(engineer_visit)
            else:
                persons[engineer_visit.custom_additional_engineer] = [engineer_visit]

    for person in persons.keys():
        checkin_dates = [x.custom_checkin_time for x in persons[person]]
        checkout_dates = [x.custom_checkout_time for x in persons[person]]
        checkin = create_checkin(person, min(checkin_dates))
        checkout = create_checkout(person, max(checkout_dates))
        create_attendance(person, checkin, checkout)

    mark_absents()


def mark_absents():
    try:
        employee_list = frappe.db.get_all("Employee", ["name", "user_id"])
        for emp in employee_list:
            frappe.logger("utils").exception(emp)
            if not frappe.db.exists("Attendance",
                                    {"attendance_date": frappe.utils.today(),
                                     "employee": emp.get("name")}):
                att_doc = frappe.new_doc("Attendance")
                att_doc.update({
                    "employee": emp.get("name"),
                    "owner": emp.get("user_id") if emp.get("user_id") else "Administrator",
                    "status": "Absent",
                    "attendance_date": frappe.utils.today(),
                })
                att_doc.save(ignore_permissions=True)
                att_doc.submit()
                owner = emp.get("user_id") if emp.get("user_id") else "Administrator"
                frappe.db.set_value("Attendance", att_doc.name, 'owner', owner)
                frappe.db.set_value("Attendance", att_doc.name, 'modified_by', owner)
    except Exception as e:
        frappe.logger("utils").exception(e)
