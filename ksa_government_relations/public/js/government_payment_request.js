frappe.ui.form.on("Government Payment Request", {
	refresh(frm) {
		if (frm.doc.employee && !frm.doc.employee_name) {
			fillPaymentEmployee(frm);
		}
		applyPaymentQueries(frm);
		applyPaymentTypeUI(frm);
	},

	employee(frm) {
		fillPaymentEmployee(frm);
		applyPaymentQueries(frm);
	},

	leave_application(frm) {
		applyPaymentQueries(frm);
	},

	payment_type(frm) {
		applyPaymentTypeUI(frm);
		applyPaymentQueries(frm);
	},

	ticket_request(frm) {
		if (frm.doc.payment_type !== "Ticket Fee" || !frm.doc.ticket_request) return;
		frappe.db
			.get_value("Travel Ticket Request", frm.doc.ticket_request, [
				"ticket_amount",
				"destination_country",
				"destination_city",
				"departure_airport",
				"arrival_airport",
			])
			.then(({ message }) => {
				if (!message) return;
				frm.set_value("visa_price", message.ticket_amount || 0);
				frm.set_value("destination_country", message.destination_country || null);
				frm.set_value("destination_city", message.destination_city || null);
				frm.set_value("departure_airport", message.departure_airport || null);
				frm.set_value("arrival_airport", message.arrival_airport || null);
			});
	},
});

function fillPaymentEmployee(frm) {
	if (!frm.doc.employee) return;
	frappe.call({
		method: "ksa_government_relations.api.get_employee_context",
		args: { employee: frm.doc.employee },
		callback: ({ message }) => {
			if (!message) return;
			frm.set_value("employee_name", message.employee_name);
			frm.set_value("company", message.company);
			if (!frm.doc.employee_qiwa_balance && frm.doc.payment_type !== "Ticket Fee") {
				frm.set_value("employee_qiwa_balance", message.qiwa_balance || 0);
			}
		},
	});
}

function applyPaymentQueries(frm) {
	const commonFilters = {};
	if (frm.doc.employee) commonFilters.employee = frm.doc.employee;
	if (frm.doc.leave_application) commonFilters.leave_application = frm.doc.leave_application;

	frm.set_query("visa_request", () => ({
		filters: {
			...commonFilters,
			request_type: "Issue Exit Re-entry Visa",
		},
	}));

	frm.set_query("ticket_request", () => ({
		filters: {
			...commonFilters,
		},
	}));
}

function applyPaymentTypeUI(frm) {
	const isTicketFee = frm.doc.payment_type === "Ticket Fee";
	const isVisaFee = frm.doc.payment_type === "Exit Re-entry Visa Fee";

	frm.set_df_property("visa_price", "label", isTicketFee ? __("Ticket Amount") : __("Visa Price"));
	frm.set_df_property("employee_qiwa_balance", "hidden", isTicketFee ? 1 : 0);
	frm.set_df_property("visa_duration_days", "hidden", isTicketFee ? 1 : 0);
	frm.set_df_property("ticket_request", "hidden", isTicketFee ? 0 : 1);
	frm.set_df_property("visa_request", "hidden", isVisaFee ? 0 : 1);
	frm.set_df_property("ticket_request", "read_only", frm.doc.docstatus === 1 || frm.doc.ticket_request ? 1 : 0);
	frm.set_df_property("visa_request", "read_only", frm.doc.docstatus === 1 || frm.doc.visa_request ? 1 : 0);

	if (isTicketFee) {
		if (frm.doc.employee_qiwa_balance) {
			frm.set_value("employee_qiwa_balance", 0);
		}
		if (frm.doc.visa_duration_days) {
			frm.set_value("visa_duration_days", null);
		}
		if (frm.doc.visa_request) {
			frm.set_value("visa_request", null);
		}
	} else if (isVisaFee && frm.doc.ticket_request) {
		frm.set_value("ticket_request", null);
	}

	frm.refresh_fields([
		"visa_price",
		"employee_qiwa_balance",
		"visa_duration_days",
		"ticket_request",
		"visa_request",
	]);
}
