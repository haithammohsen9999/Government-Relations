frappe.pages["settings-pricing"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Settings and Pricing"),
		single_column: true,
	});

	const body = $(
		'<div class="ksa-gr-shell"><div id="summary"></div><div class="ksa-gr-panel" id="visa_rules"></div><div class="ksa-gr-panel" id="ticket_rules"></div><div class="ksa-gr-panel" id="transfer_rules"></div></div>'
	).appendTo(page.body);

	function refresh() {
		frappe.call("ksa_government_relations.api.get_settings_pricing_data").then(({ message }) => {
			const data = message || {};
			const summary = data.summary || {};
			window.ksaGovernmentRelations.renderCards(body.find("#summary"), [
				{ label: "Default Company", value: summary.default_company || "-" },
				{ label: "Currency", value: summary.default_currency || "-" },
				{ label: "Cost Center", value: summary.default_cost_center || "-" },
				{ label: "Departure Offset", value: summary.default_departure_after_leave_start_days ?? 0 },
				{ label: "Return Offset", value: summary.default_return_before_leave_end_days ?? 0 },
				{ label: "Late Return Stage 1", value: summary.late_return_stage_1_days ?? 0 },
				{ label: "Late Return Stage 2", value: summary.late_return_stage_2_days ?? 0 },
				{ label: "Late Return Stage 3", value: summary.late_return_stage_3_days ?? 0 },
			]);

			body.find("#visa_rules").html(`<h4>${__("Visa Pricing Rules")}</h4>`);
			window.ksaGovernmentRelations.renderTable(
				body.find("#visa_rules"),
				[
					{ label: "Nationality", fieldname: "nationality" },
					{ label: "Country", fieldname: "country" },
					{ label: "Departure Airport", fieldname: "departure_airport" },
					{ label: "Arrival Airport", fieldname: "arrival_airport" },
					{ label: "Destination", fieldname: "destination_city" },
					{ label: "Visa Type", fieldname: "visa_type" },
					{ label: "Entry Type", fieldname: "entry_type" },
					{ label: "Minimum Days", fieldname: "minimum_days" },
					{ label: "Maximum Days", fieldname: "maximum_days" },
					{ label: "Amount", fieldname: "amount" },
					{ label: "Account", fieldname: "account" },
				],
				data.visa_rules || []
			);

			body.find("#ticket_rules").html(`<h4>${__("Ticket Pricing Rules")}</h4>`);
			window.ksaGovernmentRelations.renderTable(
				body.find("#ticket_rules"),
				[
					{ label: "Nationality", fieldname: "nationality" },
					{ label: "Country", fieldname: "country" },
					{ label: "Departure Airport", fieldname: "departure_airport" },
					{ label: "Arrival Airport", fieldname: "arrival_airport" },
					{ label: "Destination", fieldname: "destination_city" },
					{ label: "Ticket Class", fieldname: "ticket_class" },
					{ label: "Amount", fieldname: "amount" },
					{ label: "Account", fieldname: "account" },
				],
				data.ticket_rules || []
			);

			body.find("#transfer_rules").html(`<h4>${__("Sponsorship Transfer Pricing Rules")}</h4>`);
			window.ksaGovernmentRelations.renderTable(
				body.find("#transfer_rules"),
				[
					{ label: "Direction", fieldname: "transfer_direction" },
					{ label: "Nationality", fieldname: "nationality" },
					{ label: "Amount", fieldname: "amount" },
					{ label: "Account", fieldname: "account" },
					{ label: "Cost Center", fieldname: "cost_center" },
				],
				data.transfer_rules || []
			);
		});
	}

	page.set_primary_action(__("Open Settings"), () => {
		frappe.set_route("Form", "Government Relations Settings", "Government Relations Settings");
	});
	page.set_secondary_action(__("Open Sponsorship Transfers"), () => frappe.set_route("sponsorship-transfers"));
	refresh();
};
