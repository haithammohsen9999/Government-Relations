frappe.ui.form.on("Government Request", {
	refresh(frm) {
		if (frm.doc.employee && !frm.doc.employee_name) {
			fillGovernmentRequestEmployee(frm);
		}
		applyGovernmentRequestQueries(frm);
		lockAutoLinkedFields(frm);
		applyGovernmentRequestContextUI(frm);
		refreshLinkedStatuses(frm);
		renderGovernmentRequestProgress(frm);

		if (!frm.is_new()) {
			frm.add_custom_button(__("Open Travel Profile"), () => {
				frappe.set_route("government-relations-dashboard");
			});
			if (frm.doc.parent_request) {
				frm.add_custom_button(__("Open Main Request"), () => {
					frappe.set_route("Form", "Government Request", frm.doc.parent_request);
				});
			}
		}
	},

	employee(frm) {
		fillGovernmentRequestEmployee(frm);
		applyGovernmentRequestQueries(frm);
	},

	leave_application(frm) {
		applyGovernmentRequestQueries(frm);
		lockAutoLinkedFields(frm);
		applyGovernmentRequestContextUI(frm);
	},

	request_type(frm) {
		applyGovernmentRequestQueries(frm);
		applyGovernmentRequestContextUI(frm);
	},

	linked_visa(frm) {
		fetchLinkedStatus(frm, "linked_visa", "Employee Visa", "linked_visa_status");
	},

	linked_payment_request(frm) {
		fetchLinkedStatus(frm, "linked_payment_request", "Government Payment Request", "linked_payment_request_status");
	},

	linked_ticket_request(frm) {
		fetchLinkedStatus(frm, "linked_ticket_request", "Travel Ticket Request", "linked_ticket_request_status");
	},

	linked_clearance(frm) {
		fetchLinkedStatus(frm, "linked_clearance", "Employee Clearance", "linked_clearance_status");
	},
});

function fillGovernmentRequestEmployee(frm) {
	if (!frm.doc.employee) return;
	frappe.call({
		method: "ksa_government_relations.api.get_employee_context",
		args: { employee: frm.doc.employee },
		callback: ({ message }) => {
			if (!message) return;
			frm.set_value("employee_name", message.employee_name);
			frm.set_value("employee_government_profile", message.employee_government_profile);
			frm.set_value("company", message.company);
			frm.set_value("branch", message.branch);
			frm.set_value("department", message.department);
		},
	});
}

function applyGovernmentRequestQueries(frm) {
	const commonFilters = {};
	if (frm.doc.employee) commonFilters.employee = frm.doc.employee;
	if (frm.doc.leave_application) commonFilters.leave_application = frm.doc.leave_application;
	const isVisaChild = frm.doc.request_type === "Issue Exit Re-entry Visa" || Boolean(frm.doc.parent_request);

	frm.set_query("linked_visa", () => ({ filters: commonFilters }));
	frm.set_query("linked_payment_request", () => ({
		filters: {
			...commonFilters,
			...(isVisaChild ? { payment_type: "Exit Re-entry Visa Fee" } : {}),
		},
	}));
	frm.set_query("linked_ticket_request", () => ({ filters: commonFilters }));
	frm.set_query("linked_clearance", () => ({ filters: commonFilters }));
}

function lockAutoLinkedFields(frm) {
	const shouldLock = Boolean(frm.doc.employee && (frm.doc.leave_application || frm.doc.parent_request || !frm.is_new()));
	["linked_visa", "linked_payment_request", "linked_ticket_request", "linked_clearance"].forEach((fieldname) => {
		frm.set_df_property(fieldname, "read_only", shouldLock ? 1 : 0);
	});
}

function applyGovernmentRequestContextUI(frm) {
	const isVisaChild = frm.doc.request_type === "Issue Exit Re-entry Visa" || Boolean(frm.doc.parent_request);
	const showTicketAndClearance = !isVisaChild;

	frm.set_df_property("linked_ticket_request", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("linked_ticket_request_status", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("linked_ticket_payment_request", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("linked_ticket_payment_request_status", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("ticket_amount", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("linked_clearance", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("linked_clearance_status", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("clearance_amount", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("custody_amount", "hidden", showTicketAndClearance ? 0 : 1);
	frm.set_df_property("parent_request", "hidden", frm.doc.parent_request ? 0 : 1);
	frm.set_df_property(
		"linked_payment_request",
		"label",
		isVisaChild ? __("Visa Payment Request") : __("Linked Payment Request")
	);

	frm.refresh_fields([
		"linked_ticket_request",
		"linked_ticket_request_status",
		"linked_ticket_payment_request",
		"linked_ticket_payment_request_status",
		"ticket_amount",
		"linked_clearance",
		"linked_clearance_status",
		"clearance_amount",
		"custody_amount",
		"parent_request",
		"linked_payment_request",
	]);
}

function fetchLinkedStatus(frm, fieldname, doctype, statusField) {
	const name = frm.doc[fieldname];
	if (!name) {
		frm.set_value(statusField, null);
		renderLinkedStatuses(frm);
		return;
	}
	frappe.db.get_value(doctype, name, "status").then(({ message }) => {
		frm.set_value(statusField, message?.status || null);
		renderLinkedStatuses(frm);
	});
}

function refreshLinkedStatuses(frm) {
	[
		["linked_visa", "Employee Visa", "linked_visa_status"],
		["linked_payment_request", "Government Payment Request", "linked_payment_request_status"],
		["linked_ticket_request", "Travel Ticket Request", "linked_ticket_request_status"],
		["linked_ticket_payment_request", "Government Payment Request", "linked_ticket_payment_request_status"],
		["linked_clearance", "Employee Clearance", "linked_clearance_status"],
	].forEach(([fieldname, doctype, statusField]) => fetchLinkedStatus(frm, fieldname, doctype, statusField));
}

function renderLinkedStatuses(frm) {
	const config = [
		["linked_visa", "linked_visa_status"],
		["linked_payment_request", "linked_payment_request_status"],
		["linked_ticket_request", "linked_ticket_request_status"],
		["linked_ticket_payment_request", "linked_ticket_payment_request_status"],
		["linked_clearance", "linked_clearance_status"],
	];
	config.forEach(([linkField, statusField]) => {
		const status = frm.doc[statusField];
		const df = frm.get_docfield(linkField);
		if (!df) return;
		df.description = status ? `${__("Status")}: <b>${__(status)}</b>` : "";
	});
	frm.refresh_fields(config.map(([linkField, statusField]) => [linkField, statusField]).flat());
}

function renderGovernmentRequestProgress(frm) {
	if (frm.dashboard?.hide_progress) {
		frm.dashboard.hide_progress();
	}

	const wrapper = frm.fields_dict.progress_bar_html?.$wrapper;
	if (!wrapper) return;

	const percent = Number(frm.doc.completion_percent || 0);
	const safePercent = Math.max(0, Math.min(100, percent));
	const progressLabel = __("Completion Progress");
	const percentLabel = __("Completion Percent");

	wrapper.html(`
		<div class="government-request-progress-card" style="margin-bottom: 12px; padding: 14px 16px; border: 1px solid var(--border-color); border-radius: 12px; background: var(--subtle-fg);">
			<div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px;">
				<div style="font-weight: 700; color: var(--text-color);">${frappe.utils.escape_html(progressLabel)}</div>
				<div style="font-size: 16px; font-weight: 800; color: var(--primary);">${frappe.utils.escape_html(percentLabel)}: ${safePercent.toFixed(0)}%</div>
			</div>
			<div style="height: 12px; border-radius: 999px; overflow: hidden; background: rgba(15, 23, 42, 0.08);">
				<div style="width: ${safePercent}%; height: 100%; border-radius: 999px; background: linear-gradient(90deg, #16a34a 0%, #22c55e 100%); transition: width 0.25s ease;"></div>
			</div>
		</div>
	`);
}
