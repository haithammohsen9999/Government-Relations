frappe.ui.form.on("Leave Application", {
	refresh(frm) {
		toggleOutsideKsaFields(frm);
	},

	custom_is_outside_ksa(frm) {
		if (frm.doc.custom_is_outside_ksa && !frm.doc.custom_exit_reentry_required) {
			frm.set_value("custom_exit_reentry_required", 1);
		}
		toggleOutsideKsaFields(frm);
		checkEmployeeTravelWarnings(frm);
	},

	employee(frm) {
		checkEmployeeTravelWarnings(frm);
	},
});

function toggleOutsideKsaFields(frm) {
	const show = !!frm.doc.custom_is_outside_ksa;
	[
		"custom_destination_country",
		"custom_destination_city",
		"custom_departure_airport",
		"custom_arrival_airport",
		"custom_exit_reentry_required",
		"custom_expected_travel_date",
		"custom_expected_return_date",
		"custom_actual_exit_date",
		"custom_actual_return_date",
	].forEach((fieldname) => frm.toggle_display(fieldname, show));
}

function checkEmployeeTravelWarnings(frm) {
	if (!frm.doc.custom_is_outside_ksa || !frm.doc.employee) return;
	frappe.call({
		method: "ksa_government_relations.api.get_employee_context",
		args: { employee: frm.doc.employee },
		callback: ({ message }) => {
			if (!message) return;
			if (message.passport_status === "Expired" || message.iqama_status === "Expired") {
				frappe.show_alert({
					message: __("Passport or Iqama is expired for this employee."),
					indicator: "red",
				});
			}
		},
	});
}
