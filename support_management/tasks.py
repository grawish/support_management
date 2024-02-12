import frappe

def create_checkin(user, checkin_datetime):
    checkin = frappe.new_doc("Employee Checkin")
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    checkin.employee = employee.get('name')
    checkin.time = checkin_datetime
    checkin.log_type = "IN"
    checkin.save()
    return checkin

def create_checkout(user, checkout_datetime):
    checkout = frappe.new_doc("Employee Checkin")
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    checkout.employee = employee.get('name')
    checkout.time = checkout_datetime
    checkout.log_type = "OUT"
    checkout.save()
    return checkout

def create_attendance(user, checkin, checkout):
    attendance = frappe.new_doc("Attendance")
    employee = frappe.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    attendance.employee = employee.get('name')
    attendance.status = "Present"
    attendance.attendance_date = checkin.time.date()
    attendance.save()
    checkin.attendance = attendance
    checkout.attendance = attendance
    checkin.save()
    checkout.save()
    attendance.submit()
    return attendance


@frappe.whitelist()
def daily():
    from frappe.utils import get_datetime
    from_date = get_datetime(frappe.utils.today() + " 00:00:00")
    to_date = get_datetime(frappe.utils.today() + " 23:59:59")
    engineerVisits = frappe.get_all("Maintenance Visit", filters=[["Maintenance Visit", "custom_checkin_time", "between", [from_date, to_date]], ["Maintenance Visit", "custom_assigned_engineer", "!=", ""],["Maintenance Visit", "custom_checkout_time", "!=", None]], fields=["*"])


    persons = dict()

    for engineerVisit in engineerVisits:
        if(engineerVisit.custom_assigned_engineer):
            if(engineerVisit.custom_assigned_engineer in persons):
                persons[engineerVisit.custom_assigned_engineer].append(engineerVisit)
            else:
                persons[engineerVisit.custom_assigned_engineer] = [engineerVisit]
        if(engineerVisit.custom_additional_engineer):
            if(engineerVisit.custom_additional_engineer in persons):
                persons[engineerVisit.custom_additional_engineer].append(engineerVisit)
            else:
                persons[engineerVisit.custom_additional_engineer] = [engineerVisit]



    for person in persons.keys():
        checkin_dates = [x.custom_checkin_time for x in persons[person]]
        checkout_dates = [x.custom_checkout_time for x in persons[person]]
        checkin = create_checkin(person, min(checkin_dates))
        checkout = create_checkout(person, max(checkout_dates))
        create_attendance(person, checkin, checkout)

