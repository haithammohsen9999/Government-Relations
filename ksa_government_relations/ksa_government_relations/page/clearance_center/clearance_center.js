frappe.pages["clearance-center"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Clearance Center"),
		single_column: true,
	});
	const body = $('<div class="ksa-gr-shell"><div id="table"></div></div>').appendTo(page.body);

	frappe.call("ksa_government_relations.api.get_clearance_center_data").then(({ message }) => {
		window.ksaGovernmentRelations.renderTable(
			body.find("#table"),
			[
				{ label: "Clearance", fieldname: "parent", type: "link", doctype: "Employee Clearance" },
				{ label: "Department", fieldname: "department" },
				{ label: "Type", fieldname: "item_type" },
				{ label: "Description", fieldname: "description" },
				{ label: "Status", fieldname: "status", type: "badge" },
			],
			message || []
		);
	});
};
