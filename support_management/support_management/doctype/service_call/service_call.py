import frappe

@frappe.whitelist()

def create_engineer_visit(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc, map_child_doc

    def _update_links(source_doc, target_doc, source_parent):
        target_doc.prevdoc_doctype = source_parent.doctype
        target_doc.prevdoc_docname = source_parent.name


    target_doc = get_mapped_doc(
			"Warranty Claim",
			source_name,
			{"Warranty Claim": {"doctype": "Maintenance Visit", "field_map": {}}},
			target_doc,
	)

    source_doc = frappe.get_doc("Warranty Claim", source_name)

    if source_doc.get("item_code"):
            # check if custom quantity is set and is int
        if source_doc.get("custom_quantity") and source_doc.get("custom_quantity").isnumeric():
            for i in range(int(source_doc.custom_quantity)):
                table_map = {"doctype": "Maintenance Visit Purpose", "postprocess": _update_links}
                map_child_doc(source_doc, target_doc, table_map, source_doc)
        else:
            table_map = {"doctype": "Maintenance Visit Purpose", "postprocess": _update_links}
            map_child_doc(source_doc, target_doc, table_map, source_doc)
    target_doc.custom_parent_service_call = source_name
    return target_doc
