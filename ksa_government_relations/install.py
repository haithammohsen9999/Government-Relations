from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from ksa_government_relations.constants import APP_ROLES, ROLE_ASSET, ROLE_FINANCE, ROLE_GRO_MANAGER, ROLE_GRO_OFFICER, ROLE_SELF_SERVICE, ROLE_VIEWER, SAUDI_AIRPORTS, WORKFLOW_ACTIONS, WORKFLOW_STATES


CUSTOM_FIELDS = {
	"Employee": [
		{
			"fieldname": "custom_gr_section",
			"label": "Government Relations",
			"fieldtype": "Section Break",
			"insert_after": "attendance_device_id",
		},
		{
			"fieldname": "custom_government_profile",
			"label": "Employee Government Profile",
			"fieldtype": "Link",
			"options": "Employee Government Profile",
			"insert_after": "custom_gr_section",
			"read_only": 1,
		},
		{
			"fieldname": "custom_nationality",
			"label": "Nationality",
			"fieldtype": "Link",
			"options": "Country",
			"insert_after": "custom_government_profile",
		},
		{
			"fieldname": "custom_identity_type",
			"label": "Identity Type",
			"fieldtype": "Select",
			"options": "Saudi National\nResident\nVisitor\nGCC\nOther",
			"insert_after": "custom_nationality",
		},
		{
			"fieldname": "custom_government_portal",
			"label": "Government Portal",
			"fieldtype": "Select",
			"options": "Muqeem\nQiwa\nAbsher\nGOSI\nMHRSD\nOther",
			"insert_after": "custom_identity_type",
		},
		{
			"fieldname": "custom_iqama_number",
			"label": "Iqama Number",
			"fieldtype": "Data",
			"insert_after": "custom_government_portal",
		},
		{
			"fieldname": "custom_iqama_issue_date",
			"label": "Iqama Issue Date",
			"fieldtype": "Date",
			"insert_after": "custom_iqama_number",
		},
		{
			"fieldname": "custom_iqama_expiry_date",
			"label": "Iqama Expiry Date",
			"fieldtype": "Date",
			"insert_after": "custom_iqama_issue_date",
		},
		{
			"fieldname": "custom_passport_number",
			"label": "Passport Number",
			"fieldtype": "Data",
			"insert_after": "custom_iqama_expiry_date",
		},
		{
			"fieldname": "custom_passport_issue_date",
			"label": "Passport Issue Date",
			"fieldtype": "Date",
			"insert_after": "custom_passport_number",
		},
		{
			"fieldname": "custom_passport_expiry_date",
			"label": "Passport Expiry Date",
			"fieldtype": "Date",
			"insert_after": "custom_passport_issue_date",
		},
		{
			"fieldname": "custom_passport_issue_place",
			"label": "Passport Issue Place",
			"fieldtype": "Data",
			"insert_after": "custom_passport_expiry_date",
		},
		{
			"fieldname": "custom_passport_status",
			"label": "Passport Status",
			"fieldtype": "Select",
			"options": "Valid\nExpiring Soon\nExpired\nMissing",
			"insert_after": "custom_passport_issue_place",
			"read_only": 1,
		},
		{
			"fieldname": "custom_visa_status",
			"label": "Visa Status",
			"fieldtype": "Select",
			"options": "No Active Visa\nActive\nExpired\nCancelled",
			"insert_after": "custom_passport_status",
			"read_only": 1,
		},
		{
			"fieldname": "custom_current_exit_reentry_visa",
			"label": "Current Exit Re-entry Visa",
			"fieldtype": "Link",
			"options": "Employee Visa",
			"insert_after": "custom_visa_status",
			"read_only": 1,
		},
		{
			"fieldname": "custom_is_outside_ksa",
			"label": "Outside KSA",
			"fieldtype": "Check",
			"insert_after": "custom_current_exit_reentry_visa",
		},
		{
			"fieldname": "custom_last_exit_date",
			"label": "Last Exit Date",
			"fieldtype": "Date",
			"insert_after": "custom_is_outside_ksa",
			"read_only": 1,
		},
		{
			"fieldname": "custom_expected_return_date",
			"label": "Expected Return Date",
			"fieldtype": "Date",
			"insert_after": "custom_last_exit_date",
			"read_only": 1,
		},
		{
			"fieldname": "custom_actual_return_date",
			"label": "Actual Return Date",
			"fieldtype": "Date",
			"insert_after": "custom_expected_return_date",
			"read_only": 1,
		},
		{
			"fieldname": "custom_current_sponsor",
			"label": "Current Sponsor",
			"fieldtype": "Data",
			"insert_after": "custom_actual_return_date",
		},
		{
			"fieldname": "custom_qiwa_balance",
			"label": "Qiwa Balance",
			"fieldtype": "Currency",
			"insert_after": "custom_current_sponsor",
		},
		{
			"fieldname": "custom_latest_clearance",
			"label": "Latest Clearance",
			"fieldtype": "Link",
			"options": "Employee Clearance",
			"insert_after": "custom_qiwa_balance",
			"read_only": 1,
		},
		{
			"fieldname": "custom_latest_government_request",
			"label": "Latest Government Request",
			"fieldtype": "Link",
			"options": "Government Request",
			"insert_after": "custom_latest_clearance",
			"read_only": 1,
		},
	],
	"Leave Application": [
		{
			"fieldname": "custom_outside_ksa_section",
			"label": "Outside KSA Travel",
			"fieldtype": "Section Break",
			"insert_after": "follow_via_email",
		},
		{
			"fieldname": "custom_is_outside_ksa",
			"label": "Outside KSA Leave",
			"fieldtype": "Check",
			"insert_after": "custom_outside_ksa_section",
		},
		{
			"fieldname": "custom_destination_country",
			"label": "Destination Country",
			"fieldtype": "Link",
			"options": "Country",
			"insert_after": "custom_is_outside_ksa",
		},
		{
			"fieldname": "custom_destination_city",
			"label": "Destination City",
			"fieldtype": "Data",
			"insert_after": "custom_destination_country",
		},
		{
			"fieldname": "custom_departure_airport",
			"label": "Departure Airport",
			"fieldtype": "Link",
			"options": "Saudi Airport",
			"insert_after": "custom_destination_city",
		},
		{
			"fieldname": "custom_arrival_airport",
			"label": "Arrival Airport",
			"fieldtype": "Data",
			"insert_after": "custom_departure_airport",
		},
		{
			"fieldname": "custom_exit_reentry_required",
			"label": "Exit Re-entry Required",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "custom_arrival_airport",
		},
		{
			"fieldname": "custom_expected_travel_date",
			"label": "Expected Travel Date",
			"fieldtype": "Date",
			"insert_after": "custom_exit_reentry_required",
		},
		{
			"fieldname": "custom_expected_return_date",
			"label": "Expected Return Date",
			"fieldtype": "Date",
			"insert_after": "custom_expected_travel_date",
		},
		{
			"fieldname": "custom_actual_exit_date",
			"label": "Actual Exit Date",
			"fieldtype": "Date",
			"insert_after": "custom_expected_return_date",
		},
		{
			"fieldname": "custom_actual_return_date",
			"label": "Actual Return Date",
			"fieldtype": "Date",
			"insert_after": "custom_actual_exit_date",
			"allow_on_submit": 1,
		},
		{
			"fieldname": "custom_linked_government_request",
			"label": "Government Request",
			"fieldtype": "Link",
			"options": "Government Request",
			"insert_after": "custom_actual_return_date",
			"read_only": 1,
		},
		{
			"fieldname": "custom_linked_visa_request",
			"label": "Visa Request",
			"fieldtype": "Link",
			"options": "Government Request",
			"insert_after": "custom_linked_government_request",
			"read_only": 1,
		},
		{
			"fieldname": "custom_linked_employee_visa",
			"label": "Employee Visa",
			"fieldtype": "Link",
			"options": "Employee Visa",
			"insert_after": "custom_linked_visa_request",
			"read_only": 1,
		},
		{
			"fieldname": "custom_linked_clearance",
			"label": "Employee Clearance",
			"fieldtype": "Link",
			"options": "Employee Clearance",
			"insert_after": "custom_linked_employee_visa",
			"read_only": 1,
		},
		{
			"fieldname": "custom_linked_payment_request",
			"label": "Government Payment Request",
			"fieldtype": "Link",
			"options": "Government Payment Request",
			"insert_after": "custom_linked_clearance",
			"read_only": 1,
		},
		{
			"fieldname": "custom_linked_ticket_request",
			"label": "Travel Ticket Request",
			"fieldtype": "Link",
			"options": "Travel Ticket Request",
			"insert_after": "custom_linked_payment_request",
			"read_only": 1,
		},
		{
			"fieldname": "custom_gro_status",
			"label": "GRO Status",
			"fieldtype": "Select",
			"options": "Not Required\nPending\nApproved\nRejected",
			"default": "Not Required",
			"insert_after": "custom_linked_ticket_request",
			"read_only": 1,
		},
		{
			"fieldname": "custom_finance_status",
			"label": "Finance Status",
			"fieldtype": "Select",
			"options": "Not Required\nPending\nPaid\nRejected",
			"default": "Not Required",
			"insert_after": "custom_gro_status",
			"read_only": 1,
		},
		{
			"fieldname": "custom_clearance_status",
			"label": "Clearance Status",
			"fieldtype": "Select",
			"options": "Not Required\nPending\nCleared\nRejected",
			"default": "Not Required",
			"insert_after": "custom_finance_status",
			"read_only": 1,
		},
		{
			"fieldname": "custom_ticket_status",
			"label": "Ticket Status",
			"fieldtype": "Select",
			"options": "Not Required\nRequested\nBooked\nPaid\nCancelled",
			"default": "Not Required",
			"insert_after": "custom_clearance_status",
			"read_only": 1,
		},
		{
			"fieldname": "custom_return_status",
			"label": "Return Status",
			"fieldtype": "Select",
			"options": "Not Travelled\nOutside KSA\nReturned\nLate Return Stage 1\nLate Return Stage 2\nLate Return Stage 3",
			"default": "Not Travelled",
			"insert_after": "custom_ticket_status",
			"read_only": 1,
		},
	],
}

WORKSPACE_PAGE_SHORTCUTS = [
	("لوحة العلاقات الحكومية الحديثة", "government-relations-dashboard"),
	("إجازات خارج السعودية", "outside-ksa-leaves"),
	("طلبات التأشيرات", "visa-requests"),
	("طلبات السداد", "payment-requests"),
	("طلبات التذاكر", "ticket-requests"),
	("مركز المخالصات", "clearance-center"),
	("ملف سفر الموظف", "employee-travel-profile"),
	("الإعدادات والتسعير", "settings-pricing"),
	("نقل الكفالة", "sponsorship-transfers"),
]


def after_install():
	create_roles()
	create_core_custom_fields()
	ensure_workflow_states_actions()
	create_workflows()
	ensure_settings_defaults()
	ensure_saudi_airports()
	ensure_workspace_shortcuts()
	create_missing_government_profiles()
	backfill_employee_custom_fields_from_standard()
	backfill_employee_government_fields()


def create_roles():
	for role in APP_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)


def create_core_custom_fields():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True, update=True)
	enforce_employee_custom_field_properties()


def ensure_workflow_states_actions():
	for state, style in WORKFLOW_STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
			).insert(ignore_permissions=True)

	for action in WORKFLOW_ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)


def create_workflows():
	create_government_request_workflow()
	create_payment_request_workflow()
	create_employee_clearance_workflow()
	create_ticket_request_workflow()
	create_sponsorship_transfer_workflow()


def create_government_request_workflow():
	workflow_name = "Government Request Workflow"
	workflow_doc = frappe.get_doc("Workflow", workflow_name) if frappe.db.exists("Workflow", workflow_name) else frappe.new_doc("Workflow")
	workflow_doc.workflow_name = workflow_name
	workflow_doc.document_type = "Government Request"
	workflow_doc.is_active = 1
	workflow_doc.workflow_state_field = "status"
	workflow_doc.send_email_alert = 0
	workflow_doc.states = []
	for state in [
		{"state": "Draft", "doc_status": "0", "allow_edit": ROLE_GRO_OFFICER},
		{"state": "Submitted", "doc_status": "1", "allow_edit": ROLE_GRO_OFFICER},
		{"state": "Under Review", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
		{"state": "Government Processing", "doc_status": "1", "allow_edit": ROLE_GRO_OFFICER},
		{"state": "Waiting Payment", "doc_status": "1", "allow_edit": ROLE_FINANCE},
		{"state": "Paid", "doc_status": "1", "allow_edit": ROLE_GRO_OFFICER},
		{"state": "Issued", "doc_status": "1", "allow_edit": ROLE_GRO_OFFICER},
		{"state": "Completed", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
		{"state": "Rejected", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
		{"state": "Cancelled", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
		{"state": "On Hold", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
	]:
		workflow_doc.append("states", state)

	workflow_doc.transitions = []
	for transition in [
		{"state": "Draft", "action": "Submit", "next_state": "Submitted", "allowed": ROLE_GRO_OFFICER},
		{"state": "Submitted", "action": "Review", "next_state": "Under Review", "allowed": ROLE_GRO_MANAGER},
		{"state": "Under Review", "action": "Process", "next_state": "Government Processing", "allowed": ROLE_GRO_OFFICER},
		{"state": "Government Processing", "action": "Request Payment", "next_state": "Waiting Payment", "allowed": ROLE_GRO_OFFICER},
		{"state": "Waiting Payment", "action": "Mark Paid", "next_state": "Paid", "allowed": ROLE_FINANCE},
		{"state": "Paid", "action": "Issue", "next_state": "Issued", "allowed": ROLE_GRO_OFFICER},
		{"state": "Paid", "action": "Complete", "next_state": "Completed", "allowed": ROLE_GRO_MANAGER},
		{"state": "Issued", "action": "Complete", "next_state": "Completed", "allowed": ROLE_GRO_MANAGER},
		{"state": "Submitted", "action": "Reject", "next_state": "Rejected", "allowed": ROLE_GRO_MANAGER},
		{"state": "Under Review", "action": "Reject", "next_state": "Rejected", "allowed": ROLE_GRO_MANAGER},
		{"state": "Government Processing", "action": "Hold", "next_state": "On Hold", "allowed": ROLE_GRO_MANAGER},
		{"state": "On Hold", "action": "Resume", "next_state": "Government Processing", "allowed": ROLE_GRO_MANAGER},
		{"state": "Submitted", "action": "Cancel", "next_state": "Cancelled", "allowed": ROLE_GRO_MANAGER},
	]:
		workflow_doc.append("transitions", transition)

	if workflow_doc.is_new():
		workflow_doc.insert(ignore_permissions=True)
	else:
		workflow_doc.save(ignore_permissions=True)


def create_payment_request_workflow():
	workflow_name = "Government Payment Request Workflow"
	if frappe.db.exists("Workflow", workflow_name):
		return

	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": workflow_name,
			"document_type": "Government Payment Request",
			"is_active": 1,
			"workflow_state_field": "status",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": ROLE_FINANCE},
				{"state": "Waiting Payment", "doc_status": "1", "allow_edit": ROLE_FINANCE},
				{"state": "Paid", "doc_status": "1", "allow_edit": ROLE_FINANCE},
				{"state": "Posted to GL", "doc_status": "1", "allow_edit": ROLE_FINANCE},
				{"state": "Cancelled", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
			],
			"transitions": [
				{"state": "Draft", "action": "Submit", "next_state": "Waiting Payment", "allowed": ROLE_FINANCE},
				{"state": "Waiting Payment", "action": "Mark Paid", "next_state": "Paid", "allowed": ROLE_FINANCE},
				{"state": "Paid", "action": "Post to GL", "next_state": "Posted to GL", "allowed": ROLE_FINANCE},
				{"state": "Waiting Payment", "action": "Cancel", "next_state": "Cancelled", "allowed": ROLE_GRO_MANAGER},
			],
		}
	).insert(ignore_permissions=True)


def create_employee_clearance_workflow():
	workflow_name = "Employee Clearance Workflow"
	if frappe.db.exists("Workflow", workflow_name):
		return

	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": workflow_name,
			"document_type": "Employee Clearance",
			"is_active": 1,
			"workflow_state_field": "status",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": ROLE_GRO_OFFICER},
				{"state": "Pending Finance Clearance", "doc_status": "1", "allow_edit": ROLE_FINANCE},
				{"state": "Pending Asset Clearance", "doc_status": "1", "allow_edit": ROLE_ASSET},
				{"state": "Pending HR Clearance", "doc_status": "1", "allow_edit": "HR Manager"},
				{"state": "Pending Government Clearance", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
				{"state": "Cleared", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
				{"state": "Rejected", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
				{"state": "Cancelled", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
			],
			"transitions": [
				{"state": "Draft", "action": "Submit", "next_state": "Pending Finance Clearance", "allowed": ROLE_GRO_OFFICER},
				{"state": "Pending Finance Clearance", "action": "Approve", "next_state": "Pending Asset Clearance", "allowed": ROLE_FINANCE},
				{"state": "Pending Asset Clearance", "action": "Approve", "next_state": "Pending HR Clearance", "allowed": ROLE_ASSET},
				{"state": "Pending HR Clearance", "action": "Approve", "next_state": "Pending Government Clearance", "allowed": "HR Manager"},
				{"state": "Pending Government Clearance", "action": "Complete", "next_state": "Cleared", "allowed": ROLE_GRO_MANAGER},
				{"state": "Pending Finance Clearance", "action": "Reject", "next_state": "Rejected", "allowed": ROLE_FINANCE},
				{"state": "Pending Asset Clearance", "action": "Reject", "next_state": "Rejected", "allowed": ROLE_ASSET},
				{"state": "Pending HR Clearance", "action": "Reject", "next_state": "Rejected", "allowed": "HR Manager"},
				{"state": "Pending Government Clearance", "action": "Cancel", "next_state": "Cancelled", "allowed": ROLE_GRO_MANAGER},
			],
		}
	).insert(ignore_permissions=True)


def create_ticket_request_workflow():
	workflow_name = "Travel Ticket Request Workflow"
	if frappe.db.exists("Workflow", workflow_name):
		return

	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": workflow_name,
			"document_type": "Travel Ticket Request",
			"is_active": 1,
			"workflow_state_field": "status",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": ROLE_GRO_OFFICER},
				{"state": "Requested", "doc_status": "1", "allow_edit": ROLE_GRO_OFFICER},
				{"state": "Waiting Approval", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
				{"state": "Booked", "doc_status": "1", "allow_edit": ROLE_GRO_OFFICER},
				{"state": "Waiting Payment", "doc_status": "1", "allow_edit": ROLE_FINANCE},
				{"state": "Paid", "doc_status": "1", "allow_edit": ROLE_FINANCE},
				{"state": "Cancelled", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
			],
			"transitions": [
				{"state": "Draft", "action": "Submit", "next_state": "Requested", "allowed": ROLE_GRO_OFFICER},
				{"state": "Requested", "action": "Approve", "next_state": "Waiting Approval", "allowed": ROLE_GRO_MANAGER},
				{"state": "Waiting Approval", "action": "Book", "next_state": "Booked", "allowed": ROLE_GRO_OFFICER},
				{"state": "Booked", "action": "Request Payment", "next_state": "Waiting Payment", "allowed": ROLE_GRO_OFFICER},
				{"state": "Waiting Payment", "action": "Mark Paid", "next_state": "Paid", "allowed": ROLE_FINANCE},
				{"state": "Requested", "action": "Cancel", "next_state": "Cancelled", "allowed": ROLE_GRO_MANAGER},
			],
		}
	).insert(ignore_permissions=True)


def create_sponsorship_transfer_workflow():
	workflow_name = "Sponsorship Transfer Workflow"
	if frappe.db.exists("Workflow", workflow_name):
		return

	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": workflow_name,
			"document_type": "Sponsorship Transfer Request",
			"is_active": 1,
			"workflow_state_field": "status",
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": ROLE_GRO_OFFICER},
				{"state": "Sent to Qiwa", "doc_status": "1", "allow_edit": ROLE_GRO_OFFICER},
				{"state": "Approved", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
				{"state": "Waiting Payment", "doc_status": "1", "allow_edit": ROLE_FINANCE},
				{"state": "Completed", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
				{"state": "Rejected", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
				{"state": "Cancelled", "doc_status": "1", "allow_edit": ROLE_GRO_MANAGER},
			],
			"transitions": [
				{"state": "Draft", "action": "Submit", "next_state": "Sent to Qiwa", "allowed": ROLE_GRO_OFFICER},
				{"state": "Sent to Qiwa", "action": "Approve", "next_state": "Approved", "allowed": ROLE_GRO_MANAGER},
				{"state": "Approved", "action": "Request Payment", "next_state": "Waiting Payment", "allowed": ROLE_GRO_OFFICER},
				{"state": "Waiting Payment", "action": "Mark Paid", "next_state": "Completed", "allowed": ROLE_FINANCE},
				{"state": "Sent to Qiwa", "action": "Reject", "next_state": "Rejected", "allowed": ROLE_GRO_MANAGER},
				{"state": "Sent to Qiwa", "action": "Cancel", "next_state": "Cancelled", "allowed": ROLE_GRO_MANAGER},
			],
		}
	).insert(ignore_permissions=True)


def ensure_settings_defaults():
	if not frappe.db.exists("DocType", "Government Relations Settings"):
		return

	doc = frappe.get_single("Government Relations Settings")
	doc.auto_create_profile_on_employee_creation = 1
	doc.auto_create_visa_request = 1
	doc.auto_create_clearance = 1
	doc.auto_create_payment_request = 1
	doc.auto_create_ticket_request = 1
	doc.default_departure_after_leave_start_days = doc.default_departure_after_leave_start_days or 3
	doc.default_return_before_leave_end_days = doc.default_return_before_leave_end_days or 1
	doc.block_if_passport_expired = 1
	doc.block_if_iqama_expired = 1
	doc.minimum_passport_validity_days_after_return = doc.minimum_passport_validity_days_after_return or 30
	doc.minimum_iqama_validity_days_after_return = doc.minimum_iqama_validity_days_after_return or 30
	doc.late_return_stage_1_days = doc.late_return_stage_1_days or 2
	doc.late_return_stage_2_days = doc.late_return_stage_2_days or 60
	doc.late_return_stage_3_days = doc.late_return_stage_3_days or 120
	doc.late_return_stage_1_label_en = doc.late_return_stage_1_label_en or "Late Return"
	doc.late_return_stage_1_label_ar = doc.late_return_stage_1_label_ar or "متأخر عن العودة"
	doc.late_return_stage_2_label_en = doc.late_return_stage_2_label_en or "Serious Delay"
	doc.late_return_stage_2_label_ar = doc.late_return_stage_2_label_ar or "تأخير جسيم"
	doc.late_return_stage_3_label_en = doc.late_return_stage_3_label_en or "Refer to Investigation / Termination Review"
	doc.late_return_stage_3_label_ar = doc.late_return_stage_3_label_ar or "تحويل للتحقيق / النظر في الفصل"
	doc.save(ignore_permissions=True)


def ensure_saudi_airports():
	if not frappe.db.exists("DocType", "Saudi Airport"):
		return

	for airport_code, airport_name, city in SAUDI_AIRPORTS:
		if frappe.db.exists("Saudi Airport", airport_code):
			frappe.db.set_value(
				"Saudi Airport",
				airport_code,
				{"airport_name": airport_name, "city": city, "active": 1},
				update_modified=False,
			)
			continue

		frappe.get_doc(
			{
				"doctype": "Saudi Airport",
				"airport_code": airport_code,
				"airport_name": airport_name,
				"city": city,
				"active": 1,
			}
		).insert(ignore_permissions=True, ignore_if_duplicate=True)


def ensure_workspace_shortcuts():
	if not frappe.db.exists("Workspace", "Government Relations"):
		return

	workspace = frappe.get_doc("Workspace", "Government Relations")
	shortcut_rows = {row.label: row for row in workspace.shortcuts}

	for label, page_name in WORKSPACE_PAGE_SHORTCUTS:
		row = shortcut_rows.get(label)
		if not row:
			child = frappe.get_doc(
				{
					"doctype": "Workspace Shortcut",
					"parent": workspace.name,
					"parenttype": "Workspace",
					"parentfield": "shortcuts",
					"label": label,
					"type": "Page",
					"link_to": page_name,
					"idx": len(workspace.shortcuts) + 1,
				}
			)
			child.db_insert()
			workspace.shortcuts.append(child)
			continue

		frappe.db.set_value("Workspace Shortcut", row.name, {"type": "Page", "link_to": page_name, "url": None}, update_modified=False)


def enforce_employee_custom_field_properties():
	for fieldname, values in {
		"custom_is_outside_ksa": {"read_only": 0},
		"custom_last_exit_date": {"read_only": 0},
		"custom_expected_return_date": {"read_only": 0},
		"custom_actual_return_date": {"read_only": 0},
		"government_relations_section": {"hidden": 1},
		"government_profile": {"hidden": 1},
		"iqama_number": {"hidden": 1},
		"passport_number": {"hidden": 1},
		"is_outside_ksa": {"hidden": 1},
		"current_sponsor": {"hidden": 1},
		"latest_government_request": {"hidden": 1},
		"latest_clearance": {"hidden": 1},
	}.items():
		custom_field_name = frappe.db.get_value("Custom Field", {"dt": "Employee", "fieldname": fieldname}, "name")
		if custom_field_name:
			frappe.db.set_value("Custom Field", custom_field_name, values, update_modified=False)


def create_missing_government_profiles():
	from ksa_government_relations.patches.v1_0.create_missing_government_profiles import execute

	execute()


def backfill_employee_government_fields():
	if not frappe.db.exists("DocType", "Employee Government Profile"):
		return

	employee_meta = frappe.get_meta("Employee")
	employee_fields = {
		fieldname for fieldname in [
			"custom_government_profile",
			"custom_nationality",
			"custom_identity_type",
			"custom_government_portal",
			"custom_iqama_number",
			"custom_iqama_issue_date",
			"custom_iqama_expiry_date",
			"custom_passport_number",
			"custom_passport_issue_date",
			"custom_passport_expiry_date",
			"custom_passport_issue_place",
			"custom_is_outside_ksa",
			"custom_last_exit_date",
			"custom_expected_return_date",
			"custom_actual_return_date",
			"custom_current_sponsor",
			"custom_qiwa_balance",
		] if employee_meta.has_field(fieldname)
	}
	for profile in frappe.get_all(
		"Employee Government Profile",
		fields=[
			"name",
			"employee",
			"nationality",
			"iqama_number",
			"iqama_issue_date",
			"iqama_expiry_date",
			"passport_number",
			"passport_issue_date",
			"passport_expiry_date",
			"passport_issue_place",
			"is_outside_ksa",
			"last_exit_date",
			"expected_return_date",
			"actual_return_date",
			"current_sponsor",
			"qiwa_balance",
			"identity_type",
		],
	):
		if not profile.employee or not frappe.db.exists("Employee", profile.employee):
			continue

		current = frappe.db.get_value("Employee", profile.employee, list(employee_fields), as_dict=True) or {}
		values = {"custom_government_profile": profile.name}
		if "custom_nationality" in employee_fields and not current.get("custom_nationality"):
			values["custom_nationality"] = profile.nationality
		if "custom_identity_type" in employee_fields and not current.get("custom_identity_type"):
			values["custom_identity_type"] = profile.identity_type
		if "custom_government_portal" in employee_fields and not current.get("custom_government_portal"):
			values["custom_government_portal"] = profile.government_portal
		if "custom_iqama_number" in employee_fields and not current.get("custom_iqama_number"):
			values["custom_iqama_number"] = profile.iqama_number
		if "custom_iqama_issue_date" in employee_fields and not current.get("custom_iqama_issue_date"):
			values["custom_iqama_issue_date"] = profile.iqama_issue_date
		if "custom_iqama_expiry_date" in employee_fields and not current.get("custom_iqama_expiry_date"):
			values["custom_iqama_expiry_date"] = profile.iqama_expiry_date
		if "custom_passport_number" in employee_fields and not current.get("custom_passport_number"):
			values["custom_passport_number"] = profile.passport_number
		if "custom_passport_issue_date" in employee_fields and not current.get("custom_passport_issue_date"):
			values["custom_passport_issue_date"] = profile.passport_issue_date
		if "custom_passport_expiry_date" in employee_fields and not current.get("custom_passport_expiry_date"):
			values["custom_passport_expiry_date"] = profile.passport_expiry_date
		if "custom_passport_issue_place" in employee_fields and not current.get("custom_passport_issue_place"):
			values["custom_passport_issue_place"] = profile.passport_issue_place
		if "custom_is_outside_ksa" in employee_fields and not current.get("custom_is_outside_ksa") and profile.is_outside_ksa:
			values["custom_is_outside_ksa"] = profile.is_outside_ksa
		if "custom_last_exit_date" in employee_fields and not current.get("custom_last_exit_date"):
			values["custom_last_exit_date"] = profile.last_exit_date
		if "custom_expected_return_date" in employee_fields and not current.get("custom_expected_return_date"):
			values["custom_expected_return_date"] = profile.expected_return_date
		if "custom_actual_return_date" in employee_fields and not current.get("custom_actual_return_date"):
			values["custom_actual_return_date"] = profile.actual_return_date
		if "custom_current_sponsor" in employee_fields and not current.get("custom_current_sponsor"):
			values["custom_current_sponsor"] = profile.current_sponsor
		if "custom_qiwa_balance" in employee_fields and not current.get("custom_qiwa_balance") and profile.qiwa_balance:
			values["custom_qiwa_balance"] = profile.qiwa_balance
		if len(values) > 1:
			frappe.db.set_value("Employee", profile.employee, values, update_modified=False)


def backfill_employee_custom_fields_from_standard():
	employee_meta = frappe.get_meta("Employee")
	available_fields = {field.fieldname for field in employee_meta.fields}
	query_fields = ["name"]
	for fieldname in [
		"nationality",
		"iqama_number",
		"passport_number",
		"date_of_issue",
		"valid_upto",
		"place_of_issue",
		"is_outside_ksa",
		"current_sponsor",
		"custom_nationality",
		"custom_identity_type",
		"custom_government_portal",
		"custom_iqama_number",
		"custom_passport_number",
		"custom_passport_issue_date",
		"custom_passport_expiry_date",
		"custom_passport_issue_place",
		"custom_is_outside_ksa",
		"custom_current_sponsor",
	]:
		if fieldname in available_fields:
			query_fields.append(fieldname)
	for employee in frappe.get_all(
		"Employee",
		fields=query_fields,
	):
		values = {}
		if "custom_nationality" in available_fields and not employee.custom_nationality and employee.nationality:
			values["custom_nationality"] = employee.nationality
		if "custom_identity_type" in available_fields and not employee.custom_identity_type:
			values["custom_identity_type"] = "Resident"
		if "custom_government_portal" in available_fields and not getattr(employee, "custom_government_portal", None):
			values["custom_government_portal"] = "Muqeem"
		if "custom_iqama_number" in available_fields and not employee.custom_iqama_number and employee.iqama_number:
			values["custom_iqama_number"] = employee.iqama_number
		if "custom_passport_number" in available_fields and not employee.custom_passport_number and employee.passport_number:
			values["custom_passport_number"] = employee.passport_number
		if "custom_passport_issue_date" in available_fields and not employee.custom_passport_issue_date and employee.date_of_issue:
			values["custom_passport_issue_date"] = employee.date_of_issue
		if "custom_passport_expiry_date" in available_fields and not employee.custom_passport_expiry_date and employee.valid_upto:
			values["custom_passport_expiry_date"] = employee.valid_upto
		if "custom_passport_issue_place" in available_fields and not employee.custom_passport_issue_place and employee.place_of_issue:
			values["custom_passport_issue_place"] = employee.place_of_issue
		if "custom_is_outside_ksa" in available_fields and not employee.custom_is_outside_ksa and employee.is_outside_ksa:
			values["custom_is_outside_ksa"] = employee.is_outside_ksa
		if "custom_current_sponsor" in available_fields and not employee.custom_current_sponsor and employee.current_sponsor:
			values["custom_current_sponsor"] = employee.current_sponsor
		if values:
			frappe.db.set_value("Employee", employee.name, values, update_modified=False)


def sync_all_employee_profiles():
	from ksa_government_relations.utils import sync_employee_to_profile

	for employee_name in frappe.get_all("Employee", pluck="name"):
		sync_employee_to_profile(frappe.get_doc("Employee", employee_name))


def sync_all_government_request_links():
	from ksa_government_relations.ksa_government_relations.doctype.government_request.government_request import (
		sync_request_snapshot,
	)

	for request_name in frappe.get_all("Government Request", pluck="name"):
		sync_request_snapshot(request_name)


def sync_all_ticket_payment_requests():
	for ticket_name in frappe.get_all("Travel Ticket Request", pluck="name"):
		ticket = frappe.get_doc("Travel Ticket Request", ticket_name)
		ticket.pull_linked_payment_request()
		if ticket.ticket_amount and not ticket.payment_request:
			ticket.ensure_payment_request()
			ticket.pull_linked_payment_request()
		ticket.sync_status_from_payment(update_db=True)


def sync_all_employee_visa_payment_links():
	for visa_name in frappe.get_all("Employee Visa", pluck="name"):
		visa = frappe.get_doc("Employee Visa", visa_name)
		visa.resolve_payment_request()
		visa.sync_status_from_payment()
		values = {
			"payment_request": visa.payment_request,
			"payment_request_status": visa.payment_request_status,
			"status": visa.status,
		}
		frappe.db.set_value("Employee Visa", visa_name, values, update_modified=False)


def sync_all_employee_visa_request_statuses():
	for visa_name in frappe.get_all("Employee Visa", pluck="name"):
		visa = frappe.get_doc("Employee Visa", visa_name)
		visa.sync_related_requests()
