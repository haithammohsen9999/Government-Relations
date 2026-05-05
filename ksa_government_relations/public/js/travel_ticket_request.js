frappe.ui.form.on("Travel Ticket Request", {
	refresh(frm) {
		frm.set_query("leave_application", () => ({
			filters: { employee: frm.doc.employee || "" },
		}));
		frm.set_query("payment_request", () => ({
			filters: {
				employee: frm.doc.employee || "",
				leave_application: frm.doc.leave_application || "",
				payment_type: "Ticket Fee",
			},
		}));
		renderTicketPaymentStatus(frm);
	},

	payment_request(frm) {
		if (!frm.doc.payment_request) {
			frm.set_value("payment_request_status", null);
			renderTicketPaymentStatus(frm);
			return;
		}
		frappe.db.get_value("Government Payment Request", frm.doc.payment_request, "status").then(({ message }) => {
			frm.set_value("payment_request_status", message?.status || null);
			renderTicketPaymentStatus(frm);
		});
	},
});

function renderTicketPaymentStatus(frm) {
	const df = frm.get_docfield("payment_request");
	if (!df) return;
	const status = frm.doc.payment_request_status;
	df.description = status ? `${__("Status")}: <b>${__(status)}</b>` : "";
	frm.refresh_field("payment_request");
}
