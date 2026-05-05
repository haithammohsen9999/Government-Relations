frappe.pages["outside-ksa-leaves"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Outside KSA Leave Center"),
		single_column: true,
	});
	const body = $('<div class="ksa-gr-shell"><div id="workflow-table"></div></div>').appendTo(page.body);

	frappe.call("ksa_government_relations.api.get_outside_ksa_workflows").then(({ message }) => {
		window.ksaGovernmentRelations.renderTable(
			body.find("#workflow-table"),
			[
				{ label: "Leave", fieldname: "name", type: "link", doctype: "Leave Application" },
				{ label: "Employee", fieldname: "employee_name" },
				{ label: "From", fieldname: "from_date" },
				{ label: "To", fieldname: "to_date" },
				{ label: "GRO", fieldname: "custom_gro_status", type: "badge" },
				{ label: "Finance", fieldname: "custom_finance_status", type: "badge" },
				{ label: "Clearance", fieldname: "custom_clearance_status", type: "badge" },
				{ label: "Ticket", fieldname: "custom_ticket_status", type: "badge" },
				{ label: "Return", fieldname: "custom_return_status", type: "badge" },
			],
			message || []
		);
	});
};
