frappe.ui.form.on("Warranty Claim", {
  refresh: (frm) => {
    // https://github.com/frappe/frappe/pull/24199 known bug that does not remove custom_button on mobile view
    frm.remove_custom_button(__("Engineer Visit"));
    frm.remove_custom_button(__("Maintenance Visit"));
    if (!frm.doc.__islocal) {
      frm.add_custom_button(__("Create Engineer Visit"), () => {

        frappe.model.open_mapped_doc({
          method:
            "support_management.support_management.doctype.service_call.service_call.create_engineer_visit",
          frm: frm,
        });
      });
    }
  },

  customer: (frm) => {
    if(frm.doc.customer && frm.doc.custom_segment){
        frm.set_query("serial_no", ()=>{
            return {
                filters: {
                    custom_customer_code: frm.doc.customer,
                    custom_segment: frm.doc.custom_segment
                }
            }
        });
    }
  },
  custom_segment: (frm)=> {
    if(frm.doc.customer && frm.doc.custom_segment){
      frm.set_query("serial_no", ()=>{
        return {
          filters: {
            custom_customer_code: frm.doc.customer,
            custom_segment: frm.doc.custom_segment
          }
        }
      });
    }
  },
  custom_is_installation: (frm)=>{
    if(frm.doc.custom_is_installation){
        frm.set_value("serial_no","")
    }
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
