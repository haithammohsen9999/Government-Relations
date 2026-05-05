from __future__ import annotations

import frappe

from ksa_government_relations.utils import create_notification_logs, get_settings, refresh_profile_status, sync_leave_return_tracking


def refresh_government_profile_statuses():
	if not frappe.db.exists("DocType", "Employee Government Profile"):
		return
	for name in frappe.get_all("Employee Government Profile", pluck="name"):
		doc = frappe.get_doc("Employee Government Profile", name)
		refresh_profile_status(doc)
		doc.save(ignore_permissions=True)


def check_outside_ksa_returns():
	if not frappe.db.exists("Custom Field", {"dt": "Leave Application", "fieldname": "custom_is_outside_ksa"}):
		return
	for row in frappe.get_all(
		"Leave Application",
		filters={"docstatus": 1, "custom_is_outside_ksa": 1},
		fields=["name"],
		limit_page_length=0,
	):
		sync_leave_return_tracking(frappe.get_doc("Leave Application", row.name))


def send_expiry_alerts():
	settings = get_settings()
	users = [settings.default_government_relations_user, settings.default_finance_user, settings.default_asset_user]
	if not any(users):
		return

	for row in frappe.get_all(
		"Employee Government Profile",
		filters={"passport_status": ["in", ["Expired", "Expiring Soon"]]},
		fields=["name", "employee_name", "passport_status"],
		limit_page_length=0,
	):
		create_notification_logs(
			users,
			f"Passport alert for {row.employee_name}: {row.passport_status}",
			"Employee Government Profile",
			row.name,
		)

	for row in frappe.get_all(
		"Employee Government Profile",
		filters={"iqama_status": ["in", ["Expired", "Expiring Soon"]]},
		fields=["name", "employee_name", "iqama_status"],
		limit_page_length=0,
	):
		create_notification_logs(
			users,
			f"Iqama alert for {row.employee_name}: {row.iqama_status}",
			"Employee Government Profile",
			row.name,
		)


def notify_pending_clearances():
	settings = get_settings()
	users = [settings.default_finance_user, settings.default_asset_user, settings.default_government_relations_user]
	if not any(users):
		return

	for row in frappe.get_all(
		"Employee Clearance",
		filters={"status": ["in", ["Pending Finance Clearance", "Pending Asset Clearance", "Pending HR Clearance", "Pending Government Clearance"]]},
		fields=["name", "employee_name", "status"],
		limit_page_length=0,
	):
		create_notification_logs(users, f"Pending clearance for {row.employee_name}: {row.status}", "Employee Clearance", row.name)
