import frappe

def before_submit(doc, method):
    for item in doc.items:
        item_doc = frappe.get_doc("Item", item.item_code, as_dict=True)
        if not item.serial_no:
            frappe.throw(f"Serial numbers for {item.item_code} are not specified.")

        # Split serial numbers by new line
        serial_numbers = item.serial_no.split("\n")

        # Validate that the number of serial numbers equals the quantity
        if len(serial_numbers) != int(item.qty):
            frappe.throw(f"Number of serial numbers for {item.item_code} does not match the specified quantity.")

        if any(not serial_no.strip() for serial_no in serial_numbers):
            frappe.throw(f"At least one serial number for {item.item_code} is null or an empty string.")

        for i in range(int(item.qty)):
            serial_no_doc = frappe.get_doc({
                "doctype": "Serial No",
                "serial_no": serial_numbers[i].strip(),  # Remove leading/trailing spaces
                "item_code": item.item_code,
                "status": "Delivered",
                "warranty_expiry_date": frappe.utils.add_to_date(frappe.utils.now(), days=int(item_doc.warranty_period))
            })
            serial_no_doc.insert()
