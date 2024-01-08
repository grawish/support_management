import frappe
from datetime import datetime

@frappe.whitelist()
def mark_visit(**kwargs):
    user = frappe.session.user
    visit=frappe.get_doc("Site Visit", kwargs.get("visit"))
    if not visit:
        raise frappe.DoesNotExistError("Site Visit does not exist")
    if visit.visit_status == "Complete":
        raise frappe.ValidationError("Site Visit is already resolved or closed")
    employee = frappe.get_doc("Employee", {"user_id": user})
    if visit.engineer != employee.get('name'):
        raise frappe.ValidationError("You are not authorized to mark this visit")
    visit.visit_status = kwargs.get("visit_status")
    if kwargs.get("visit_status") == "Complete":
        visit.signature = kwargs.get('signature')
    visit.save(ignore_permissions=True)
    visit.submit()
    if kwargs.get("visit_status") != "Complete":
        return create_visit(issue=visit.issue_code, schedule=kwargs.get("schedule"), previous_visit=visit.name)
    return visit


def create_visit(**kwargs):
    issue = frappe.get_doc("Issue", kwargs.get("issue"))
    schedule = kwargs.get("schedule")
    if not issue:
        raise frappe.DoesNotExistError("Issue does not exist")
    if issue.status == "Resolved" and issue.status == "Closed":
        raise frappe.ValidationError("Issue is already resolved or closed")
    user = frappe.session.user
    employee = frappe.get_doc("Employee", {"user_id": user})
    visit = frappe.new_doc("Site Visit")
    visit.engineer = employee.name
    visit.issue_code = issue.name
    visit.schedule = datetime.strptime(schedule, "%Y-%m-%dT%H:%M:%S+05:30")
    visit.customer = issue.customer
    visit.amended_from = kwargs.get("previous_visit")
    visit.insert(ignore_permissions=True)
    return visit
