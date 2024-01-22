frappe.ui.form.on("Maintenance Visit", {
  refresh: (frm) => {
    frm.add_custom_button(__("Create Invoice"), () => {
      frappe.model.open_mapped_doc({
        method:
          "support_management.support_management.doctype.engineer_visit.engineer_visit.create_invoice",
        frm: frm,
      });
    });
  },
  custom_assigned_engineer: (frm) => {
    // frm.set_query("custom_additional_engineer", ()=>{
    //     return {
    //         filters: {
    //           "name": frm.doc.custom_assigned_engineer
    //         }
    //     }
    // })
  },
  warranty_amc_status: (frm) => {
    if (
      !["Under Warranty", "Under AMC"].includes(frm.doc.warranty_amc_status)
    ) {
      frm.set_value("custom_is_billed", 1);
    } else {
      frm.set_value("custom_is_billed", 0);
    }
  },
});

frappe.ui.form.on("Maintenance Visit Purpose", {
  item_code: async (frm, cdt, cdn) => {
    const purposes = frm.doc.purposes;

    const warranty_period = JSON.parse(
      JSON.stringify(
        await frappe.db.get_value(
          "Item",
          frm.doc.purposes.find((p) => p.name === cdn).item_code,
          "warranty_period"
        )
      )
    ).message.warranty_period;

    console.log(warranty_period);
    frm.set_value(
      "purposes",
      purposes.map((purpose) => {
        if (purpose.name === cdn) {
          return {
            ...purpose,
            custom_warranty_period_in_days: warranty_period,
          };
        }
        return purpose;
      })
    );
    // custom_warranty_period_in_days
    // frm.set_value(
    //   "purposes",

    // );
  },
});
