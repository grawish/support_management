import frappe
from datetime import datetime
import json


def create_serial_no(serial_no, item_code, customer, warranty_period):
    # check if serial_no already exists
    serial = frappe.db.exists(
        "Serial No",
        {
            "serial_no": serial_no,
            "item_code": item_code,
            "custom_customer_code": customer,
        },
    )
    if serial:
        return serial
    # create a new document if not exists
    serial = frappe.new_doc("Serial No")
    serial.serial_no = serial_no
    serial.item_code = item_code
    serial.status = "Delivered"
    serial.custom_customer_code = customer
    serial.insert(ignore_permissions=True)
    serial.warranty_expiry_date = frappe.utils.add_to_date(
        frappe.utils.now(), days=int(warranty_period)
    )
    serial.save()
    return serial.name


def validate_installation_items(items, visit):
    installation_fields = ["serial_no"]
    non_installation_fields = [
        "custom_description_of_issue",
        "custom_is_machine_breakdown",
    ]
    common_fields = ["name", "work_done"]

    items_without_required_fields = []
    for i, item in enumerate(items):
        purpose = visit.purposes[i]
        if purpose.custom_is_installation == 1:
            missing_fields = [
                field for field in installation_fields if item.get(field) is None
            ]
        else:
            missing_fields = [
                field for field in non_installation_fields if item.get(field) is None
            ]

        # Check for fields required in both cases
        missing_fields += [field for field in common_fields if item.get(field) is None]

        if missing_fields:
            items_without_required_fields.append((item, missing_fields))

    if items_without_required_fields:
        error_message = ""
        for item, missing_fields in items_without_required_fields:
            error_message += f"Item is missing fields: {', '.join(missing_fields)}, "

        raise frappe.ValidationError(error_message)


@frappe.whitelist()
def validate_face(**kwargs):
    user = frappe.session.user
    image = kwargs.get("image")
    photo = frappe.get_doc("Photo", {"photo": image})
    people_array = photo.people
    if not photo.is_processed:
        raise frappe.ValidationError("Photo is not processed yet")
    if not people_array:
        raise frappe.ValidationError("No face detected")
    if len(people_array) > 0:
        for person in people_array:
            face = frappe.get_doc("ROI", person.face)
            if face.person is None:
                continue
            person = frappe.get_doc("Person", face.person)
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


def face_validation(photo):
    if not photo:
        raise frappe.ValidationError("Photo is required")
    try:
        validate_face(image=photo)
    except frappe.ValidationError as e:
        raise frappe.ValidationError(e)


@frappe.whitelist()
def checkin_visit():
    kwargs = json.loads(frappe.request.data)
    required_params = [
        "visit",
        "custom_checkin_photo",
        "custom_customer_actual_location",
    ]  # add geolocation later on
    if not all(p in kwargs for p in required_params):
        missing_params = [p for p in required_params if not kwargs.get(p)]
        raise frappe.ValidationError("Missing parameters:", missing_params)

    try:
        face_validation(kwargs.get("custom_checkin_photo"))
    except frappe.ValidationError as e:
        raise frappe.ValidationError(e)

    visit = frappe.get_doc("Maintenance Visit", kwargs.get("visit"))
    if not visit:
        raise frappe.DoesNotExistError("Engineer Visit does not exist")
    if visit.completion_status == "Fully Completed":
        raise frappe.ValidationError("Engineer Visit is already resolved or closed")
    # if visit.completion_status == "Under Progress":
    # raise frappe.ValidationError("Engineer Visit is already checked-in")
    visit.custom_checkin_time = frappe.utils.now()
    visit.completion_status = "Under Progress"
    visit.custom_checkin_photo = kwargs.get("custom_checkin_photo")
    location = '{"type": "FeatureCollection","features": [{"type": "Feature","properties": {},"geometry": {"type": "Point","coordinates": '+kwargs.get("custom_customer_actual_location")+' } } ]}'
    visit.custom_customer_actual_location = location
    visit.save(ignore_permissions=True)
    return visit


@frappe.whitelist()
def checkout_visit():
    kwargs = json.loads(frappe.request.data)
    required_params = ["completion_status", "visit", "item_status"]
    if not all(p in kwargs for p in required_params):
        missing_params = [p for p in required_params if not kwargs.get(p)]
        raise frappe.ValidationError("Missing parameters:", missing_params)

    user = frappe.session.user

    visit = frappe.get_doc("Maintenance Visit", kwargs.get("visit"))
    if not visit:
        raise frappe.DoesNotExistError("Engineer Visit does not exist")
    if visit.completion_status == "Fully Completed":
        raise frappe.ValidationError("Engineer Visit is already resolved or closed")
    if kwargs.get("completion_status") not in [
        "Partially Completed",
        "Fully Completed",
        "Customer Delay",
        "OEM Advice",
        "Spares Requirements",
    ]:
        raise frappe.ValidationError("Completion Status is not Valid")

    assigned_users = json.loads(visit._assign if visit._assign else "[]")
    if user not in assigned_users:
        raise frappe.ValidationError("You are not authorized to checkout this visit")
    if visit.completion_status != "Under Progress":
        raise frappe.ValidationError("Engineer Visit is not under progress")

    # item_status is an list of required items
    items = kwargs.get("item_status")
    if len(items) != len(visit.purposes):
        raise frappe.ValidationError(
            "Missing items reqd:", len(visit.purposes), "got", len(items)
        )
    try:
        validate_installation_items(items, visit)
    except frappe.ValidationError as e:
        raise frappe.ValidationError(e)

    try:
        for i, item in enumerate(items):
            visit.purposes[i].work_done = (
                item.get("work_done") if item.get("work_done") else ""
            )
            visit.purposes[i].serial_no = create_serial_no(
                item.get("serial_no"),
                visit.purposes[i].item_code,
                visit.customer,
                visit.purposes[i].custom_warranty_period_in_days,
            )
            visit.purposes[i].custom_description_of_issue = (
                item.get("custom_description_of_issue")
                if item.get("custom_description_of_issue")
                else ""
            )
            visit.purposes[i].custom_is_machine_breakdown = (
                item.get("custom_is_machine_breakdown")
                if item.get("custom_is_machine_breakdown")
                else ""
            )
            visit.purposes[i].custom_analysis = (
                item.get("custom_analysis") if item.get("custom_analysis") else ""
            )
            visit.purposes[i].custom_observations = (
                item.get("custom_observations")
                if item.get("custom_observations")
                else ""
            )
    except frappe.ValidationError as e:
        raise frappe.ValidationError(e)

    visit.custom_checkout_time = frappe.utils.now()
    visit.completion_status = kwargs.get("completion_status")
    if kwargs.get("completion_status") == "Fully Completed":
        if not visit.custom_customer_signature:
            raise frappe.ValidationError("Customer Signature is required")
        visit.custom_customer_signature = kwargs.get("custom_customer_signature")
        visit.customer_feedback = kwargs.get("customer_feedback")
    visit.save(ignore_permissions=True)
    if visit.completion_status not in ["Fully Completed", "Customer Delay"]:
        return create_visit(visit.name)
    return visit


def create_visit(visit):
    old_visit = frappe.get_doc("Maintenance Visit", visit)
    if old_visit.completion_status == "Fully Completed":
        return
    new_visit = frappe.new_doc("Maintenance Visit")
    new_visit.customer = old_visit.customer
    
    new_date = frappe.utils.add_to_date(
        str(old_visit.mntc_date) + " " + str(old_visit.mntc_time), days=1
    )
    new_visit.mntc_date = new_date.split(' ')[0]
    new_visit.mntc_time = new_date.split(' ')[1]
    new_visit.completion_status = "Not Started Yet"
    new_visit.purposes = old_visit.purposes
    new_visit.insert(ignore_permissions=True)
    new_visit.custom_assigned_engineer = old_visit.custom_assigned_engineer
    new_visit.custom_additional_engineer = old_visit.custom_additional_engineer
    new_visit.custom_reason_for_additional_engineer = (
        old_visit.custom_reason_for_additional_engineer
    )
    new_visit.save(ignore_permissions=True)
    return new_visit
