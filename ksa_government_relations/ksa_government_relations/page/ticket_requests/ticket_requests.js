frappe.pages["ticket-requests"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Ticket Center"),
		single_column: true,
	});
	const body = $('<div class="ksa-gr-shell"><div id="table"></div></div>').appendTo(page.body);

	function refresh(status) {
		frappe.call("ksa_government_relations.api.get_ticket_center_data", { status }).then(({ message }) => {
			window.ksaGovernmentRelations.renderTable(
				body.find("#table"),
				[
					{ label: "Ticket Request", fieldname: "name", type: "link", doctype: "Travel Ticket Request" },
					{ label: "Employee", fieldname: "employee_name" },
					{ label: "Destination", fieldname: "destination_city" },
					{ label: "Departure", fieldname: "departure_date" },
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
		options: "\nDraft\nRequested\nWaiting Approval\nBooked\nWaiting Payment\nPaid\nCancelled",
		change() {
			refresh(this.get_value());
		},
	});
	refresh();
};
