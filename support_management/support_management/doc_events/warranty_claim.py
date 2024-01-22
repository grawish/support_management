import frappe

def validate(doc,method):
    if doc.complaint == '‎' and not doc.custom_is_installation:
        frappe.throw("Issue is Mandatory")
    
def after_insert(doc,method):
    if doc.custom_is_installation:
        installation_note = frappe.get_doc({
            "doctype": "Installation Note",
            "customer": doc.customer,
            "territory": "All Territories",
            "inst_date": frappe.utils.today(),
            "items": [
                {
                    "item_code": doc.item_code,
                    "qty": doc.custom_quantity
                }
            ]
        })
        installation_note.insert()
    else:
        pass