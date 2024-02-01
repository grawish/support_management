import frappe
from frappe.utils import time_diff_in_hours

@frappe.whitelist()
def before_save(doc, method):
    if doc.custom_checkin_time and doc.custom_checkout_time:
        if doc.custom_checkin_time > doc.custom_checkout_time:
            frappe.throw("Checkin time cannot be greater than checkout time")
        doc.custom_visit_hours = time_diff_in_hours(doc.custom_checkout_time, doc.custom_checkin_time)

@frappe.whitelist()
def on_update(doc, method):
    from frappe.desk.form import assign_to

    if doc.custom_parent_service_call:
        warranty_claim = frappe.get_doc("Warranty Claim", doc.custom_parent_service_call)
        if warranty_claim.custom_visits:
            valid = True
            for child_visit in warranty_claim.custom_visits:
                if child_visit.engineer_visit == doc.name:
                    child_doc = frappe.get_doc("Engineer Visits", child_visit.name)
                    child_doc.date_of_visit = doc.mntc_date
                    child_doc.hours = doc.custom_visit_hours
                    child_doc.save(ignore_permissions=True)
                    valid = False
                    break
            if valid:
                child_visit = frappe.new_doc("Engineer Visits")
                child_visit.engineer_visit = doc.name
                warranty_claim.custom_visits.append(child_visit)
                warranty_claim.save(ignore_permissions=True)

    if doc.custom_assigned_engineer:
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
            doc.custom_reason_for_additional_engineer = None
            assign_to.clear("Maintenance Visit", doc.name)
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
    else:
        doc.custom_additional_engineer = None
        doc.custom_assigned_engineer = None
        doc.custom_reason_for_additional_engineer = None
        assign_to.clear("Maintenance Visit", doc.name, ignore_permissions=True)
