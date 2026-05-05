frappe.ui.form.on("Employee Clearance", {
	refresh(frm) {
		setQueries(frm);
		frm.add_custom_button(__("Generate Clearance Items"), () => {
			frm.call("generate_clearance_items").then(() => frm.refresh_field("clearance_items"));
		});
	},

	employee(frm) {
		setQueries(frm);
		if (frm.doc.employee && !frm.doc.employee_name) {
			frappe.call({
				method: "ksa_government_relations.api.get_employee_context",
				args: { employee: frm.doc.employee },
				callback: ({ message }) => {
					if (!message) return;
					frm.set_value("employee_name", message.employee_name);
				},
			});
		}
	},
});

function setQueries(frm) {
	frm.set_query("leave_application", () => ({
		filters: {
			employee: frm.doc.employee || "",
			custom_is_outside_ksa: 1,
			docstatus: 1,
		},
	}));
}
