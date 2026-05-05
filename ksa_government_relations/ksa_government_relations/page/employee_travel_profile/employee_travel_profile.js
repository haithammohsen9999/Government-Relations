frappe.pages["employee-travel-profile"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Employee Travel Profile"),
		single_column: true,
	});

	const employeeField = page.add_field({
		label: __("Employee"),
		fieldname: "employee",
		fieldtype: "Link",
		options: "Employee",
		change() {
			const employee = employeeField.get_value();
			if (employee) refresh(employee);
		},
	});

	const body = $('<div class="ksa-gr-shell"><div id="summary"></div><div class="ksa-gr-split"><div id="left"></div><div id="right"></div></div></div>').appendTo(page.body);

	function refresh(employee) {
		frappe.call("ksa_government_relations.api.get_employee_travel_profile", { employee }).then(({ message }) => {
			const profile = message?.profile || {};
			window.ksaGovernmentRelations.renderCards(body.find("#summary"), [
				{ label: "Passport Status", value: __(profile.passport_status || "Missing") },
				{ label: "Iqama Status", value: __(profile.iqama_status || "Missing") },
				{ label: "Visa Status", value: __(profile.visa_status || "No Active Visa") },
				{ label: "Qiwa Balance", value: profile.qiwa_balance || 0 },
			]);
			body.find("#left").html(`<h4>${__("Custodies and Clearances")}</h4>`);
			window.ksaGovernmentRelations.renderTable(
				body.find("#left"),
				[
					{ label: "Clearance", fieldname: "name", type: "link", doctype: "Employee Clearance" },
					{ label: "Type", fieldname: "clearance_type" },
					{ label: "Status", fieldname: "status", type: "badge" },
					{ label: "Liability", fieldname: "total_liability" },
				],
				message?.clearances || []
			);
			body.find("#right").html(`<h4>${__("Visas and Tickets")}</h4>`);
			window.ksaGovernmentRelations.renderTable(
				body.find("#right"),
				[
					{ label: "Visa", fieldname: "name", type: "link", doctype: "Employee Visa" },
					{ label: "Type", fieldname: "visa_type" },
					{ label: "Status", fieldname: "status", type: "badge" },
					{ label: "Expiry", fieldname: "expiry_date" },
				],
				message?.visas || []
			);
		});
	}

	const routeOptions = frappe.route_options || {};
	if (routeOptions.employee) {
		employeeField.set_value(routeOptions.employee);
		refresh(routeOptions.employee);
	}
};
