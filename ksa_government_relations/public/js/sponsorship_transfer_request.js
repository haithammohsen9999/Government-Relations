frappe.ui.form.on("Sponsorship Transfer Request", {
	employee(frm) {
		if (!frm.doc.employee) return;
		frappe.call({
			method: "ksa_government_relations.api.get_employee_context",
			args: { employee: frm.doc.employee },
			callback: ({ message }) => {
				if (!message) return;
				frm.set_value("employee_name", message.employee_name);
				frm.set_value("iqama_number", message.iqama_number);
				frm.set_value("current_sponsor", message.current_sponsor);
				frm.set_value("nationality", message.nationality);
			},
		});
	},
});
