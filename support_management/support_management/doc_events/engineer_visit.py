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

        # append attachments here
        for i in doc.custom_attachments:
            new_doc = frappe.new_doc("Engineer Visit Attachments")
            new_doc.attachment = i.attachment
            warranty_claim.custom_attachments.append(new_doc)
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
            # check if already assigned contains doc.custom_assigned_engineer if yes then remove all other engineers
            for i in already_assigned:
                if i.get('owner') != doc.custom_assigned_engineer:
                    assign_to.remove("Maintenance Visit", doc.name, i.get('owner'))
    else:
        for i in already_assigned:
            assign_to.remove("Maintenance Visit", doc.name, i.get('owner'))


    # # send email here
    rows = ''

    for i in range(len(doc.custom_spare_requirements)):
        rows += f'''
<tr>
        <td>{i + 1}</td>
        <td>{doc.custom_spare_requirements[i].part}</td>
        <td>{doc.custom_spare_requirements[i].qty}</td>
        <td><img src="https://suba-services-test.frappe.cloud/{doc.custom_spare_requirements[i].image}" /></td>
      </tr>
'''

    email_string = f'''
<div class="ql-editor read-mode">
  <p>Dear Spares Team,</p>
  <p><br></p>
  <p><br></p>
  <p>Please find below the spares enquiry . Do share the Quote to the client accordingly.</p>
  <p>Engineer Name : {doc.custom_assigned_engineer_name}</p>
  <p><br></p>
  <p><br></p>
  <p><strong><u>Client Details:</u></strong></p>
  <p>Customer Name: {doc.customer}</p>
  <p>Company Code: {doc.company}</p>
  <p>Address: {doc.address_display}</p>
  <p>Contact Name: {doc.customer}</p>
  <p>Contact Phone No. : {doc.contact_mobile}</p>
  <p>Customer email: {doc.contact_email}</p>
  <p><br></p>
  <p><br></p>
  <p><strong><u>Machine Details:</u></strong></p>
  <p>Machine Name: {doc.purposes[0].item_name}</p>
  <p>Model No.: {doc.purposes[0].item_code}</p>
  <p>Serial No.: {doc.purposes[0].serial_no}</p>
  <p><br></p>
  <p><br></p>
  <p>Machine Breakdown: {doc.purposes[0].custom_is_machine_breakdown}</p>
  <p><br></p>
  <p><br></p>
  <table class="table table-bordered">
    <tbody>
        <tr>
            <th><strong>S no.</strong></th>
            <th><strong>Part Name</strong></th>
            <th><strong>Quantity</strong></th>
            <th><strong>Picture</strong></th>
        </tr>
        {rows}
    </tbody>
  </table> 
</div>
    '''
    if not doc.custom_is_spare_requirements_sent and doc.custom_is_spare_requirements:
        recipient = frappe.get_single("Suba Settings").recipient_email
        frappe.sendmail(recipient, sender='', subject='Maintenance visit updated', message=email_string,
                        as_markdown=False, now=True)
        doc.custom_is_spare_requirements_sent = 1
        doc.save(ignore_permissions=True)
