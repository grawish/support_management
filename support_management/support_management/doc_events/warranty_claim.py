import frappe

def validate(doc,method):
    if doc.complaint == '‎' and not doc.custom_is_installation:
        frappe.throw("Issue is Mandatory")