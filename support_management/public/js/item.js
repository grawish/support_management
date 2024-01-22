frappe.ui.form.on("Item", {
    refresh: (frm) => {

    },
    custom_division_code: (frm) => {
        frm.doc.item_code = (frm?.doc?.custom_division_code ?? '') + "/" + (frm?.doc?.custom_segment_code ?? '') + "/" + (frm?.doc?.custom_manufacturer_code ?? '') + "/" + (frm?.doc?.custom_product_type_code ?? '')
        frm.refresh_field("item_code");
    },
    custom_segment_code: (frm) => {
        frm.doc.item_code = (frm?.doc?.custom_division_code ?? '') + "/" + (frm?.doc?.custom_segment_code ?? '') + "/" + (frm?.doc?.custom_manufacturer_code ?? '') + "/" + (frm?.doc?.custom_product_type_code ?? '')
        frm.refresh_field("item_code");
    },
    custom_manufacturer_code: (frm) => {
        frm.doc.item_code = (frm?.doc?.custom_division_code ?? '') + "/" + (frm?.doc?.custom_segment_code ?? '') + "/" + (frm?.doc?.custom_manufacturer_code ?? '') + "/" + (frm?.doc?.custom_product_type_code ?? '')
        frm.refresh_field("item_code");
    },
    custom_product_type_code: (frm) => {
        frm.doc.item_code = (frm?.doc?.custom_division_code ?? '') + "/" + (frm?.doc?.custom_segment_code ?? '') + "/" + (frm?.doc?.custom_manufacturer_code ?? '') + "/" + (frm?.doc?.custom_product_type_code ?? '')
        frm.refresh_field("item_code");
    }
});
