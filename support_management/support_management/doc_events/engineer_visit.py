import frappe
from frappe.utils import time_diff_in_hours
from datetime import datetime


@frappe.whitelist()
def before_save(doc, method):
    if doc.custom_checkin_time and doc.custom_checkout_time:
        cit = doc.custom_checkin_time
        cot = doc.custom_checkout_time
        str_type = type("sample")
        if (type(doc.custom_checkin_time) == str_type):
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
                    child_doc.completion_status = doc.completion_status
                    child_doc.total_expenses = doc.custom_service_charges
                    # child_doc.save(ignore_permissions=True)
                    warranty_claim.save(ignore_permissions=True)
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

    # send email here
    email_string = f'''
    <div class="ql-editor read-mode"><p>Dear Spares Team,</p><p><br></p><p><br></p><p>Please find below the spares enquiry . Do share the Quote to the client accordingly.</p><p>Engineer Name : {doc.custom_assigned_engineer_name}</p><p><br></p><p><br></p><p><strong><u>Client Details:</u></strong></p><p>Customer Name:</p><p>Company Code:</p><p>Address:</p><p>Contact Name</p><p>Contact Phone No.</p><p>Customer email</p><p><br></p><p><br></p><p><strong><u>Machine Details:</u></strong></p><p>Machine Name: </p><p>Model No.</p><p>Serial No.</p><p><br></p><p><br></p><p>Machine Breakdown: </p><p><br></p><p><br></p></div>
    '''
    frappe.sendmail('goblinsanger@gmail.com', 'grawish@hybrowlabs.com', 'Maintenance visit updated',
                    '<h1>Maintainance Visit</h1>', False, now=True)
