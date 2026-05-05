frappe.ui.form.on("Employee Visa", {
	refresh(frm) {
		applyEmployeeVisaQueries(frm);
		lockEmployeeVisaLinks(frm);
		renderEmployeeVisaPaymentStatus(frm);
	},

	employee(frm) {
		applyEmployeeVisaQueries(frm);
		lockEmployeeVisaLinks(frm);
	},

	leave_application(frm) {
		applyEmployeeVisaQueries(frm);
		lockEmployeeVisaLinks(frm);
	},

	visa_request(frm) {
		applyEmployeeVisaQueries(frm);
		lockEmployeeVisaLinks(frm);
	},

	payment_request(frm) {
		if (!frm.doc.payment_request) {
			frm.set_value("payment_request_status", null);
			renderEmployeeVisaPaymentStatus(frm);
			return;
		}
		frappe.db.get_value("Government Payment Request", frm.doc.payment_request, "status").then(({ message }) => {
			frm.set_value("payment_request_status", message?.status || null);
			renderEmployeeVisaPaymentStatus(frm);
		});
	},
});

function applyEmployeeVisaQueries(frm) {
	const filters = {
		payment_type: "Exit Re-entry Visa Fee",
	};
	if (frm.doc.employee) filters.employee = frm.doc.employee;
	if (frm.doc.leave_application) filters.leave_application = frm.doc.leave_application;
	if (frm.doc.visa_request) filters.visa_request = frm.doc.visa_request;

	frm.set_query("payment_request", () => ({ filters }));
}

function lockEmployeeVisaLinks(frm) {
	const shouldLock = Boolean(
		frm.doc.employee && (frm.doc.leave_application || frm.doc.visa_request || frm.doc.payment_request || !frm.is_new())
	);
	frm.set_df_property("payment_request", "read_only", shouldLock ? 1 : 0);
}

function renderEmployeeVisaPaymentStatus(frm) {
	const df = frm.get_docfield("payment_request");
	if (!df) return;
	const status = frm.doc.payment_request_status;
	df.description = status ? `${__("Status")}: <b>${__(status)}</b>` : "";
	frm.refresh_field("payment_request");
}
