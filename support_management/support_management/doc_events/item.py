import frappe

selected_number = 0

def generate_next_number(names, prefix):
    existing_numbers = [int(name[len(prefix):len(prefix)+4]) for name in names if name.startswith(prefix) and name[len(prefix):len(prefix)+4].isdigit()]
    if not existing_numbers:
        next_number = 1
    else:
        next_number = max(existing_numbers) + 1
    return f"{prefix}{next_number:04d}/00"

@frappe.whitelist()
def before_insert(doc, method):
    _list = frappe.get_list("Item")
    name_list = [item["name"] for item in _list]
    if not doc.item_code:
        doc.item_code = generate_next_number(name_list, doc.custom_division_code+"/"+doc.custom_segment_code+"/"+doc.custom_Manufacturer_code+"/"+doc.custom_product_type_code)
    else:
        doc.item_code = generate_next_number(name_list, doc.item_code)
    doc.item_name = doc.custom_division + '/' + doc.custom_segment + '/' + doc.custom_Manufacturer + '/' + doc.custom_product_type

@frappe.whitelist()
def on_update(doc, method):
    doc.item_name = doc.custom_division + '/' + doc.custom_segment + '/' + doc.custom_Manufacturer + '/' + doc.custom_product_type