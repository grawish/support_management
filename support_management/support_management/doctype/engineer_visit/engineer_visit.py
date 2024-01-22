import frappe

@frappe.whitelist()

def create_invoice(source_doc,target_doc=None):
    from frappe.model.mapper import get_mapped_doc, map_child_doc

    def _update_links(source_doc, target_doc, source_parent):
        target_doc.prevdoc_doctype = source_parent.doctype
        target_doc.prevdoc_docname = source_parent.name

    visit = frappe.db.sql(
		"""select t1.name
		from `tabSales Invoice` t1, `tabMaintenance Visit Purpose` t2
		where t2.parent=t1.name and t2.prevdoc_docname=%s
		and t1.docstatus=1 and t1.completion_status='Fully Completed'""",
		source_name,
	)

    if not visit:
        target_doc = get_mapped_doc(
			"Warranty Claim",
			source_name,
			{"Warranty Claim": {"doctype": "Sales Invoice", "field_map": {}}},
			target_doc,
		)
        
        source_doc = frappe.get_doc("Warranty Claim", source_name)
        
        if source_doc.get("item_code"):
            # check if custom quantity is set and is int
            if source_doc.get("custom_quantity") and isinstance(source_doc.custom_quantity, int):
                for i in range(int(source_doc.custom_quantity)):
                    table_map = {"doctype": "Maintenance Visit Purpose", "postprocess": _update_links}
                    map_child_doc(source_doc, target_doc, table_map, source_doc)
            else:
                table_map = {"doctype": "Maintenance Visit Purpose", "postprocess": _update_links}
                map_child_doc(source_doc, target_doc, table_map, source_doc)
                
        return target_doc

