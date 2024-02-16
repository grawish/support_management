import frappe
from frappe.utils import time_diff_in_hours
from datetime import datetime

@frappe.whitelist()
def before_save(doc, method):
    if doc.custom_checkin_time and doc.custom_checkout_time:
        cit = doc.custom_checkin_time
        cot = doc.custom_checkout_time
        str_type = type("sample")
        if(type(doc.custom_checkin_time) == str_type):
            cit = datetime.strptime(doc.custom_checkin_time, '%Y-%m-%d %H:%M:%S')
        if (type(doc.custom_checkout_time) == str_type):
            cot = datetime.strptime(doc.custom_checkout_time, '%Y-%m-%d %H:%M:%S')
        if cit > cot:
            frappe.throw("Checkin time cannot be greater than checkout time")
        doc.custom_visit_hours = time_diff_in_hours(doc.custom_checkout_time, doc.custom_checkin_time)
    if doc.custom_assigned_engineer:
        if doc.custom_additional_engineer:
            pass
        else:
            doc.custom_reason_for_additional_engineer = ''
    else:
        doc.custom_reason_for_additional_engineer = ''
        doc.custom_additional_engineer = None

@frappe.whitelist()
def on_update(doc, method):
    from frappe.desk.form import assign_to

    already_assigned = assign_to.get({"doctype": "Maintenance Visit", "name": doc.name})

    if doc.custom_parent_service_call:
        warranty_claim = frappe.get_doc("Warranty Claim", doc.custom_parent_service_call)
        valid = True
        if warranty_claim.custom_visits:
            for child_visit in warranty_claim.custom_visits:
                if child_visit.engineer_visit == doc.name:
                    child_doc = frappe.get_doc("Engineer Visits", child_visit.name)
                    child_doc.date_of_visit = doc.mntc_date
                    child_doc.hours = doc.custom_visit_hours
                    child_doc.custom_completion_status = doc.completion_status
                    child_doc.custom_total_expenses = doc.custom_service_charges
                    child_doc.save(ignore_permissions=True)
                    valid = False
                    break
        if valid:
            child_visit = frappe.new_doc("Engineer Visits")
            child_visit.engineer_visit = doc.name
            warranty_claim.custom_visits.append(child_visit)
        warranty_claim.save(ignore_permissions=True)

    if doc.custom_assigned_engineer:
        if doc.custom_assigned_engineer not in already_assigned:
            assign_to.add(
                dict(
                    assign_to=[doc.custom_assigned_engineer],
                    doctype="Maintenance Visit",
                    name=doc.name,
                    assigned_by="Administrator",
                    assigned_by_full_name="Administrator",
                    description=doc.name,
                    notify=True,
                ),
                ignore_permissions=True,
            )
        if doc.custom_additional_engineer:
            if doc.custom_additional_engineer not in already_assigned:
                assign_to.add(
                    dict(
                        assign_to=[doc.custom_additional_engineer],
                        doctype="Maintenance Visit",
                        name=doc.name,
                        assigned_by="Administrator",
                        assigned_by_full_name="Administrator",
                        description=doc.name,
                        notify=True,
                    ),
                    ignore_permissions=True,
                )
        else:
#             check if already assigned contains doc.custom_assigned_engineer if yes then remove all other engineers
            for i in already_assigned:
                if i.get('owner') != doc.custom_assigned_engineer:
                    assign_to.remove("Maintenance Visit", doc.name, i.get('owner'))
    else:
        for i in already_assigned:
            assign_to.remove("Maintenance Visit", doc.name, i.get('owner'))
