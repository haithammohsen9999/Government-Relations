frappe.ui.form.on("Employee Government Profile", {
	refresh(frm) {
		if (frm.doc.employee && (!frm.doc.employee_name || !frm.doc.passport_number || !frm.doc.iqama_number)) {
			fillEmployeeContext(frm);
		}
	},

	employee(frm) {
		fillEmployeeContext(frm);
	},
});

function fillEmployeeContext(frm) {
	if (!frm.doc.employee) return;
	frappe.call({
		method: "ksa_government_relations.api.get_employee_context",
		args: { employee: frm.doc.employee },
		callback: ({ message }) => {
			if (!message) return;
			[
				"employee_name",
				"company",
				"branch",
				"department",
				"designation",
				"nationality",
				"identity_type",
				"government_portal",
				"iqama_number",
				"iqama_issue_date",
				"iqama_expiry_date",
				"iqama_status",
				"passport_number",
				"passport_issue_date",
				"passport_expiry_date",
				"passport_issue_place",
				"passport_status",
				"current_sponsor",
				"qiwa_balance",
				"is_outside_ksa",
				"current_exit_reentry_visa",
				"visa_status",
				"latest_clearance",
			].forEach((fieldname) => frm.set_value(fieldname, message[fieldname] || null));
		},
	});
}
