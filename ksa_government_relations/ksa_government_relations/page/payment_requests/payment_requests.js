frappe.pages["payment-requests"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Payment Center"),
		single_column: true,
	});
	const body = $('<div class="ksa-gr-shell"><div id="table"></div></div>').appendTo(page.body);

	function refresh(status) {
		frappe.call("ksa_government_relations.api.get_payment_center_data", { status }).then(({ message }) => {
			window.ksaGovernmentRelations.renderTable(
				body.find("#table"),
				[
					{ label: "Payment Request", fieldname: "name", type: "link", doctype: "Government Payment Request" },
					{ label: "Employee", fieldname: "employee_name" },
					{ label: "Type", fieldname: "payment_type" },
					{ label: "Amount", fieldname: "company_payable_amount" },
					{ label: "Status", fieldname: "status", type: "badge" },
				],
				message || []
			);
		});
	}

	page.add_field({
		label: __("Status"),
		fieldname: "status",
		fieldtype: "Select",
		options: "\nDraft\nWaiting Payment\nPaid\nPosted to GL\nCancelled",
		change() {
			refresh(this.get_value());
		},
	});
	refresh();
};
