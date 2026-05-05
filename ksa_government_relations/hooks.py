app_name = "ksa_government_relations"
app_title = "KSA Government Relations"
app_publisher = "NextFlow HR"
app_description = "Saudi government relations, outside KSA travel, clearance, payment, ticketing, and compliance workflows for ERPNext."
app_email = "support@nextflow-hr.com"
app_license = "mit"

# The site already carries ERPNext and HRMS; keeping this empty avoids network
# validation during installation in restricted environments.
# required_apps = ["erpnext", "hrms"]

app_include_css = "/assets/ksa_government_relations/css/ksa_government_relations.css"
app_include_js = "/assets/ksa_government_relations/js/ksa_government_relations.js"

doctype_js = {
	"Employee Government Profile": "public/js/employee_government_profile.js",
	"Government Request": "public/js/government_request.js",
	"Employee Clearance": "public/js/employee_clearance.js",
	"Employee Visa": "public/js/employee_visa.js",
	"Government Payment Request": "public/js/government_payment_request.js",
	"Travel Ticket Request": "public/js/travel_ticket_request.js",
	"Sponsorship Transfer Request": "public/js/sponsorship_transfer_request.js",
	"Leave Application": "public/js/leave_application.js",
}

after_install = "ksa_government_relations.install.after_install"

fixtures = [
	{
		"dt": "Role",
		"filters": [["role_name", "in", [
			"Government Relations Manager",
			"Government Relations Officer",
			"Finance Clearance Officer",
			"Asset Clearance Officer",
			"HR Government Viewer",
			"Employee Self Service Government",
		]]],
	},
	{
		"dt": "Workflow",
		"filters": [["name", "in", [
			"Government Request Workflow",
			"Government Payment Request Workflow",
			"Employee Clearance Workflow",
			"Travel Ticket Request Workflow",
			"Sponsorship Transfer Workflow",
		]]],
	},
	{
		"dt": "Custom Field",
		"filters": [["dt", "in", ["Employee", "Leave Application"]]],
	},
]

doc_events = {
	"Employee": {
		"after_insert": "ksa_government_relations.api.create_government_profile",
		"on_update": "ksa_government_relations.api.sync_government_profile",
	},
	"Leave Application": {
		"validate": "ksa_government_relations.api.validate_leave_application",
		"on_submit": "ksa_government_relations.api.process_outside_ksa_leave",
		"on_cancel": "ksa_government_relations.api.cancel_outside_ksa_workflow",
		"on_update_after_submit": "ksa_government_relations.api.sync_return_tracking",
	},
}

permission_query_conditions = {
	"Government Request": "ksa_government_relations.permissions.get_self_service_query_condition",
	"Government Payment Request": "ksa_government_relations.permissions.get_self_service_query_condition",
	"Travel Ticket Request": "ksa_government_relations.permissions.get_self_service_query_condition",
	"Employee Clearance": "ksa_government_relations.permissions.get_self_service_query_condition",
	"Employee Visa": "ksa_government_relations.permissions.get_self_service_query_condition",
	"Employee Government Profile": "ksa_government_relations.permissions.get_self_service_query_condition",
}

has_permission = {
	"Government Request": "ksa_government_relations.permissions.has_self_service_permission",
	"Government Payment Request": "ksa_government_relations.permissions.has_self_service_permission",
	"Travel Ticket Request": "ksa_government_relations.permissions.has_self_service_permission",
	"Employee Clearance": "ksa_government_relations.permissions.has_self_service_permission",
	"Employee Visa": "ksa_government_relations.permissions.has_self_service_permission",
	"Employee Government Profile": "ksa_government_relations.permissions.has_self_service_permission",
}

scheduler_events = {
	"daily": [
		"ksa_government_relations.tasks.refresh_government_profile_statuses",
		"ksa_government_relations.tasks.check_outside_ksa_returns",
		"ksa_government_relations.tasks.send_expiry_alerts",
	],
	"hourly": [
		"ksa_government_relations.tasks.notify_pending_clearances",
	],
}
