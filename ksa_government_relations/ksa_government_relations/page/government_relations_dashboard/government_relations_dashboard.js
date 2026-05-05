frappe.pages["government-relations-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Government Relations Dashboard"),
		single_column: true,
	});

	const body = $('<div class="ksa-gr-shell"><div id="kpi"></div><div class="ksa-gr-split"><div id="late"></div><div id="payments"></div></div></div>').appendTo(page.body);

	function refresh() {
		frappe.call("ksa_government_relations.api.get_dashboard_data").then(({ message }) => {
			const metrics = message || {};
			window.ksaGovernmentRelations.renderCards(body.find("#kpi"), [
				{ label: "Outside KSA Leaves Today", value: metrics.outside_ksa_today },
				{ label: "Employees Outside KSA", value: metrics.employees_outside_ksa },
				{ label: "Pending Payments", value: metrics.pending_payments },
				{ label: "Pending Tickets", value: metrics.pending_tickets },
				{ label: "Pending Clearances", value: metrics.pending_clearances },
				{ label: "Late Return Stage 3", value: metrics.late_return_stage_3 },
				{ label: "Expired Passports", value: metrics.expired_passports },
				{ label: "Expired Iqamas", value: metrics.expired_iqamas },
			]);
		});

		frappe.call("ksa_government_relations.api.get_outside_ksa_workflows").then(({ message }) => {
			const rows = (message || []).filter((row) => row.custom_return_status?.includes("Late Return"));
			body.find("#late").html(`<h4>${__("Late Return Cases")}</h4>`);
			window.ksaGovernmentRelations.renderTable(
				body.find("#late"),
				[
					{ label: "Leave", fieldname: "name", type: "link", doctype: "Leave Application" },
					{ label: "Employee", fieldname: "employee_name" },
					{ label: "Return Status", fieldname: "custom_return_status", type: "badge" },
				],
				rows
			);
		});

		frappe.call("ksa_government_relations.api.get_payment_center_data", { status: "Waiting Payment" }).then(({ message }) => {
			body.find("#payments").html(`<h4>${__("Pending Payment Requests")}</h4>`);
			window.ksaGovernmentRelations.renderTable(
				body.find("#payments"),
				[
					{ label: "Request", fieldname: "name", type: "link", doctype: "Government Payment Request" },
					{ label: "Employee", fieldname: "employee_name" },
					{ label: "Type", fieldname: "payment_type" },
					{ label: "Status", fieldname: "status", type: "badge" },
				],
				message || []
			);
		});
	}

	page.set_secondary_action(__("Outside KSA Center"), () => frappe.set_route("outside-ksa-leaves"));
	refresh();
};
