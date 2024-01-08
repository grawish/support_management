// Copyright (c) 2024, @grawish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Site Visit", {
    refresh(frm) {
        const wrapper = frm.get_field("preview").$wrapper;
        wrapper.html(`<img id="signature-preview" class="img-responsive" src="${frm.doc['signature']}" alt="signature preview" />`);

    },
});
