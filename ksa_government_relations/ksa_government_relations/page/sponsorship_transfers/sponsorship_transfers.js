frappe.pages["sponsorship-transfers"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Sponsorship Transfers"),
		single_column: true,
	});
	const body = $('<div class="ksa-gr-shell"><div id="table"></div></div>').appendTo(page.body);

	function refresh(status) {
		frappe.call("ksa_government_relations.api.get_sponsorship_transfer_data", { status }).then(({ message }) => {
			window.ksaGovernmentRelations.renderTable(
				body.find("#table"),
				[
					{ label: "Transfer Request", fieldname: "name", type: "link", doctype: "Sponsorship Transfer Request" },
					{ label: "Employee", fieldname: "employee_name" },
					{ label: "Direction", fieldname: "transfer_direction" },
					{ label: "Current Sponsor", fieldname: "current_sponsor" },
					{ label: "New Sponsor", fieldname: "new_sponsor" },
					{ label: "Qiwa Request", fieldname: "qiwa_request_no" },
					{ label: "Amount", fieldname: "amount" },
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
		options: "\nDraft\nSent to Qiwa\nApproved\nWaiting Payment\nCompleted\nRejected\nCancelled",
		change() {
			refresh(this.get_value());
		},
	});
	page.set_primary_action(__("New Transfer"), () => frappe.new_doc("Sponsorship Transfer Request"));
	page.set_secondary_action(__("Settings and Pricing"), () => frappe.set_route("settings-pricing"));
	refresh();
};
