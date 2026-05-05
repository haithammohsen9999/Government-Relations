frappe.pages["visa-requests"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Visa Requests"),
		single_column: true,
	});
	const body = $('<div class="ksa-gr-shell"><div id="table"></div></div>').appendTo(page.body);

	function refresh(status) {
		frappe.call("ksa_government_relations.api.get_visa_request_data", { status }).then(({ message }) => {
			window.ksaGovernmentRelations.renderTable(
				body.find("#table"),
				[
					{ label: "Visa", fieldname: "name", type: "link", doctype: "Employee Visa" },
					{ label: "Employee", fieldname: "employee_name" },
					{ label: "Type", fieldname: "visa_type" },
					{ label: "Country", fieldname: "destination_country" },
					{ label: "Leave End Date", fieldname: "leave_end_date" },
					{ label: "Visa Expiry Date", fieldname: "expiry_date" },
					{ label: "Return Status", fieldname: "return_status", type: "badge" },
					{ label: "Visa Status", fieldname: "visa_validity_status", type: "badge" },
					{ label: "Status", fieldname: "status", type: "badge" },
				],
				message || []
			);
		});
	}

	page.add_field({
		label: __("Status"),
		fieldname: "status",
		fieldtype: "Select",
		options: "\nRequested\nWaiting Payment\nPaid\nIssued\nActive\nUsed\nExpired\nCancelled",
		change() {
			refresh(this.get_value());
		},
	});
	page.set_primary_action(__("New Visa"), () => frappe.new_doc("Employee Visa"));
	page.set_secondary_action(__("Settings and Pricing"), () => frappe.set_route("settings-pricing"));
	refresh();
};
