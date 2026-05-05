from __future__ import annotations

import frappe
from frappe import _

from ksa_government_relations import reporting
from ksa_government_relations.utils import cancel_outside_ksa_documents, create_outside_ksa_workflow, get_employee_snapshot, get_or_create_government_profile, sync_employee_to_profile, sync_leave_return_tracking, validate_outside_ksa_leave_requirements


def create_government_profile(doc, method=None):
	profile = get_or_create_government_profile(doc.name)
	frappe.db.set_value("Employee", doc.name, "custom_government_profile", profile.name, update_modified=False)


def sync_government_profile(doc, method=None):
	sync_employee_to_profile(doc)


def validate_leave_application(doc, method=None):
	if not getattr(doc, "custom_is_outside_ksa", 0):
		return

	issues = validate_outside_ksa_leave_requirements(doc)
	if issues:
		doc.custom_gro_status = "Rejected"
		frappe.throw("<br>".join(f"• {issue}" for issue in issues), title=_("Blocked / Missing Requirements"))

	doc.custom_gro_status = "Pending"
	if not doc.custom_finance_status:
		doc.custom_finance_status = "Pending"
	if not doc.custom_clearance_status:
		doc.custom_clearance_status = "Pending"
	if not doc.custom_ticket_status:
		doc.custom_ticket_status = "Requested"


def process_outside_ksa_leave(doc, method=None):
	if not getattr(doc, "custom_is_outside_ksa", 0):
		return
	if getattr(doc, "custom_linked_government_request", None):
		return
	create_outside_ksa_workflow(doc)


def cancel_outside_ksa_workflow(doc, method=None):
	if not getattr(doc, "custom_is_outside_ksa", 0):
		return
	cancel_outside_ksa_documents(doc)


def sync_return_tracking(doc, method=None):
	if not getattr(doc, "custom_is_outside_ksa", 0):
		return
	sync_leave_return_tracking(doc)


@frappe.whitelist()
def get_employee_context(employee: str):
	return get_employee_snapshot(employee)


@frappe.whitelist()
def get_dashboard_data():
	return reporting.get_dashboard_metrics()


@frappe.whitelist()
def get_outside_ksa_workflows(employee: str | None = None):
	return reporting.get_outside_ksa_leave_rows({"employee": employee} if employee else {})


@frappe.whitelist()
def get_employee_travel_profile(employee: str):
	return reporting.get_employee_travel_profile_data(employee)


@frappe.whitelist()
def get_clearance_center_data():
	return reporting.get_clearance_center_rows()


@frappe.whitelist()
def get_payment_center_data(status: str | None = None):
	filters = {"status": status} if status else {}
	return reporting.get_payment_request_rows(filters)


@frappe.whitelist()
def get_ticket_center_data(status: str | None = None):
	filters = {"status": status} if status else {}
	return reporting.get_ticket_request_rows(filters)


@frappe.whitelist()
def get_visa_request_data(status: str | None = None):
	filters = {"status": status} if status else {}
	return reporting.get_visa_request_rows(filters)


@frappe.whitelist()
def get_sponsorship_transfer_data(status: str | None = None):
	filters = {"status": status} if status else {}
	return reporting.get_sponsorship_transfer_rows(filters)


@frappe.whitelist()
def get_settings_pricing_data():
	settings = frappe.get_single("Government Relations Settings")
	return {
		"summary": {
			"default_company": settings.default_company,
			"default_cost_center": settings.default_cost_center,
			"default_currency": settings.default_currency,
			"default_departure_after_leave_start_days": settings.default_departure_after_leave_start_days,
			"default_return_before_leave_end_days": settings.default_return_before_leave_end_days,
			"late_return_stage_1_days": settings.late_return_stage_1_days,
			"late_return_stage_2_days": settings.late_return_stage_2_days,
			"late_return_stage_3_days": settings.late_return_stage_3_days,
			"visa_expense_account": settings.visa_expense_account,
			"ticket_expense_account": settings.ticket_expense_account,
			"sponsorship_transfer_expense_account": settings.sponsorship_transfer_expense_account,
			"default_payment_account": settings.default_payment_account,
		},
		"visa_rules": [row.as_dict() for row in settings.get("visa_pricing_rules") or []],
		"ticket_rules": [row.as_dict() for row in settings.get("ticket_pricing_rules") or []],
		"transfer_rules": [row.as_dict() for row in settings.get("sponsorship_transfer_pricing_rules") or []],
	}
