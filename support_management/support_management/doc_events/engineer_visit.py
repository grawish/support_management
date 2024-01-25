import frappe


@frappe.whitelist()
def on_update(doc, method):
    from frappe.desk.form import assign_to

    if doc.custom_assigned_engineer:
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
            doc.custom_reason_for_additional_engineer = None
            assign_to.clear("Maintenance Visit", doc.name)
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
    else:
        doc.custom_additional_engineer = None
        doc.custom_assigned_engineer = None
        doc.custom_reason_for_additional_engineer = None
        assign_to.clear("Maintenance Visit", doc.name, ignore_permissions=True)
