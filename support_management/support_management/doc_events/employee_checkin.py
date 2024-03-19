import frappe


@frappe.whitelist()
def before_save(doc, method):
    doc.custom_date_only = doc.time
