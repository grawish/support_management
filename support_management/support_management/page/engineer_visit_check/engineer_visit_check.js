frappe.pages['engineer-visit-check'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: '',
		single_column: true
	});

	console.log(page);

	const heading = $('<suba-engineer-visit id="subaEngineerVisit"></suba-engineer-visit>');

	$(heading).appendTo(page.container);
	// set page container padding to none
	page.container.css('padding', '0px');

	// const subaComopnent = $("div#123");

	// $(subaComopnent).appendTo(page.main);

	// console.log(subaComopnent);
}