from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate, today

from ksa_government_relations.utils import get_settings

LATE_RETURN_STATUSES = (
	"Late Return Stage 1",
	"Late Return Stage 2",
	"Late Return Stage 3",
)


def get_leave_return_status(leave_row, settings=None) -> str | None:
	if not leave_row:
		return None
	if leave_row.get("custom_actual_return_date"):
		return "Returned"
	if not leave_row.get("custom_is_outside_ksa"):
		return None
	if not leave_row.get("to_date") or getdate(leave_row.to_date) >= getdate(today()):
		return "Outside KSA"

	settings = settings or get_settings()
	delay = date_diff(today(), leave_row.to_date)
	if delay >= flt(settings.late_return_stage_3_days):
		return "Late Return Stage 3"
	if delay >= flt(settings.late_return_stage_2_days):
		return "Late Return Stage 2"
	if delay >= flt(settings.late_return_stage_1_days):
		return "Late Return Stage 1"
	return "Outside KSA"


def get_visa_validity_status(expiry_date) -> str | None:
	if not expiry_date:
		return None
	return "Expired" if getdate(expiry_date) < getdate(today()) else "Valid"


def get_outside_ksa_leave_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	conditions = {"docstatus": 1, "custom_is_outside_ksa": 1}
	if filters.get("employee"):
		conditions["employee"] = filters.employee
	if filters.get("company"):
		conditions["company"] = filters.company

	rows = frappe.get_all(
		"Leave Application",
		filters=conditions,
		fields=[
			"name",
			"employee",
			"employee_name",
			"company",
			"from_date",
			"to_date",
			"status",
			"custom_destination_country",
			"custom_destination_city",
			"custom_gro_status",
			"custom_finance_status",
			"custom_clearance_status",
			"custom_ticket_status",
			"custom_return_status",
			"custom_linked_government_request",
			"custom_linked_visa_request",
			"custom_linked_employee_visa",
			"custom_linked_clearance",
			"custom_linked_payment_request",
			"custom_linked_ticket_request",
		],
		order_by="from_date desc",
		limit_page_length=0,
	)
	return rows


def get_employees_outside_ksa_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	conditions = {"is_outside_ksa": 1}
	if filters.get("company"):
		conditions["company"] = filters.company
	if filters.get("employee"):
		conditions["employee"] = filters.employee
	return frappe.get_all(
		"Employee Government Profile",
		filters=conditions,
		fields=[
			"name",
			"employee",
			"employee_name",
			"company",
			"department",
			"passport_number",
			"passport_expiry_date",
			"iqama_number",
			"iqama_expiry_date",
			"current_exit_reentry_visa",
			"last_exit_date",
			"expected_return_date",
			"actual_return_date",
		],
		order_by="expected_return_date asc",
		limit_page_length=0,
	)


def get_late_return_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	conditions = {"docstatus": 1, "custom_is_outside_ksa": 1, "custom_return_status": ["in", LATE_RETURN_STATUSES]}
	if filters.get("custom_return_status"):
		conditions["custom_return_status"] = filters.custom_return_status
	return frappe.get_all(
		"Leave Application",
		filters=conditions,
		fields=[
			"name",
			"employee",
			"employee_name",
			"from_date",
			"to_date",
			"custom_expected_return_date",
			"custom_actual_return_date",
			"custom_return_status",
		],
		order_by="to_date asc",
		limit_page_length=0,
	)


def get_payment_request_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	conditions = {}
	if filters.get("status"):
		conditions["status"] = filters.status
	if filters.get("company"):
		conditions["company"] = filters.company
	if filters.get("employee"):
		conditions["employee"] = filters.employee
	return frappe.get_all(
		"Government Payment Request",
		filters=conditions,
		fields=[
			"name",
			"employee",
			"employee_name",
			"leave_application",
			"government_request",
			"payment_type",
			"destination_country",
			"destination_city",
			"visa_price",
			"employee_qiwa_balance",
			"company_payable_amount",
			"account",
			"payment_account",
			"cost_center",
			"status",
			"payment_reference",
			"payment_date",
			"journal_entry",
		],
		order_by="modified desc",
		limit_page_length=0,
	)


def get_visa_request_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	conditions = {}
	if filters.get("status"):
		conditions["status"] = filters.status
	if filters.get("employee"):
		conditions["employee"] = filters.employee
	rows = frappe.get_all(
		"Employee Visa",
		filters=conditions,
		fields=[
			"name",
			"employee",
			"employee_name",
			"leave_application",
			"visa_request",
			"payment_request",
			"destination_country",
			"destination_city",
			"visa_type",
			"entry_type",
			"duration_days",
			"issue_date",
			"expiry_date",
			"status",
		],
		order_by="modified desc",
		limit_page_length=0,
	)
	leave_names = [row.leave_application for row in rows if row.leave_application]
	leave_map = {}
	if leave_names:
		leave_map = {
			row.name: row
			for row in frappe.get_all(
				"Leave Application",
				filters={"name": ["in", leave_names]},
				fields=["name", "to_date", "custom_actual_return_date", "custom_is_outside_ksa"],
				limit_page_length=0,
			)
		}

	settings = get_settings() if leave_map else None
	for row in rows:
		leave = leave_map.get(row.leave_application)
		row.leave_end_date = leave.to_date if leave else None
		row.return_status = get_leave_return_status(leave, settings)
		row.visa_validity_status = get_visa_validity_status(row.expiry_date)

	return rows


def get_ticket_request_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	conditions = {}
	if filters.get("status"):
		conditions["status"] = filters.status
	return frappe.get_all(
		"Travel Ticket Request",
		filters=conditions,
		fields=[
			"name",
			"employee",
			"employee_name",
			"leave_application",
			"destination_country",
			"destination_city",
			"departure_date",
			"return_date",
			"airline",
			"booking_reference",
			"ticket_number",
			"ticket_amount",
			"status",
			"payment_request",
		],
		order_by="departure_date desc",
		limit_page_length=0,
	)


def get_clearance_liability_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	conditions = {}
	if filters.get("status"):
		conditions["status"] = filters.status
	if filters.get("employee"):
		conditions["employee"] = filters.employee
	return frappe.get_all(
		"Employee Clearance",
		filters=conditions,
		fields=[
			"name",
			"employee",
			"employee_name",
			"leave_application",
			"clearance_type",
			"status",
			"total_financial_liability",
			"total_asset_liability",
			"total_leave_settlement",
			"total_liability",
		],
		order_by="modified desc",
		limit_page_length=0,
	)


def get_passport_expiry_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	rows = frappe.get_all(
		"Employee Government Profile",
		filters={"passport_number": ["is", "set"]},
		fields=[
			"employee",
			"employee_name",
			"company",
			"department",
			"passport_number",
			"passport_expiry_date",
			"passport_status",
			"visa_expiry_date",
		],
		order_by="passport_expiry_date asc",
		limit_page_length=0,
	)
	for row in rows:
		row.days_remaining = date_diff(row.passport_expiry_date, today()) if row.passport_expiry_date else None
		row.expires_before_visa = int(bool(row.passport_expiry_date and row.visa_expiry_date and getdate(row.passport_expiry_date) < getdate(row.visa_expiry_date)))
	return rows


def get_iqama_expiry_rows(filters: dict | None = None) -> list[dict]:
	rows = frappe.get_all(
		"Employee Government Profile",
		filters={"iqama_number": ["is", "set"]},
		fields=[
			"employee",
			"employee_name",
			"company",
			"department",
			"iqama_number",
			"iqama_expiry_date",
			"iqama_status",
			"expected_return_date",
		],
		order_by="iqama_expiry_date asc",
		limit_page_length=0,
	)
	for row in rows:
		row.days_remaining = date_diff(row.iqama_expiry_date, today()) if row.iqama_expiry_date else None
		row.expires_before_return = int(bool(row.iqama_expiry_date and row.expected_return_date and getdate(row.iqama_expiry_date) < getdate(row.expected_return_date)))
	return rows


def get_sponsorship_transfer_payment_rows(filters: dict | None = None) -> list[dict]:
	return frappe.get_all(
		"Sponsorship Transfer Request",
		fields=[
			"name",
			"employee",
			"employee_name",
			"transfer_direction",
			"status",
			"amount",
			"account",
			"payment_request",
			"qiwa_request_no",
		],
		order_by="modified desc",
		limit_page_length=0,
	)


def get_sponsorship_transfer_rows(filters: dict | None = None) -> list[dict]:
	filters = frappe._dict(filters or {})
	conditions = {}
	if filters.get("status"):
		conditions["status"] = filters.status
	if filters.get("employee"):
		conditions["employee"] = filters.employee
	return frappe.get_all(
		"Sponsorship Transfer Request",
		filters=conditions,
		fields=[
			"name",
			"employee",
			"employee_name",
			"transfer_direction",
			"nationality",
			"current_sponsor",
			"new_sponsor",
			"qiwa_request_no",
			"status",
			"amount",
			"account",
			"payment_request",
			"clearance",
		],
		order_by="modified desc",
		limit_page_length=0,
	)


def get_government_expenses_gl_summary(filters: dict | None = None) -> list[dict]:
	rows = frappe.get_all(
		"Government Payment Request",
		filters={"status": ["in", ["Paid", "Posted to GL"]]},
		fields=["payment_type", "account", "company_payable_amount", "company", "cost_center", "journal_entry"],
		limit_page_length=0,
	)
	summary = {}
	for row in rows:
		key = (row.payment_type, row.account, row.company, row.cost_center)
		if key not in summary:
			summary[key] = {
				"payment_type": row.payment_type,
				"account": row.account,
				"company": row.company,
				"cost_center": row.cost_center,
				"total_amount": 0.0,
				"posted_count": 0,
			}
		summary[key]["total_amount"] += flt(row.company_payable_amount)
		summary[key]["posted_count"] += 1
	return list(summary.values())


def get_dashboard_metrics() -> dict:
	passports = get_passport_expiry_rows()
	iqamas = get_iqama_expiry_rows()
	late_returns = get_late_return_rows()
	pending_payments = get_payment_request_rows({"status": "Waiting Payment"})
	pending_tickets = get_ticket_request_rows({"status": ["in", ["Requested", "Waiting Approval", "Booked", "Waiting Payment"]]})
	pending_clearances = get_clearance_liability_rows({"status": ["in", ["Pending Finance Clearance", "Pending Asset Clearance", "Pending HR Clearance", "Pending Government Clearance"]]})
	workflow_rows = get_outside_ksa_leave_rows()

	return {
		"outside_ksa_today": len([row for row in workflow_rows if row.get("from_date") and getdate(row.from_date) == getdate(today())]),
		"employees_outside_ksa": len(get_employees_outside_ksa_rows()),
		"late_return_stage_1": len([row for row in late_returns if row.custom_return_status == "Late Return Stage 1"]),
		"late_return_stage_2": len([row for row in late_returns if row.custom_return_status == "Late Return Stage 2"]),
		"late_return_stage_3": len([row for row in late_returns if row.custom_return_status == "Late Return Stage 3"]),
		"pending_payments": len(pending_payments),
		"pending_tickets": len(pending_tickets),
		"pending_clearances": len(pending_clearances),
		"expired_passports": len([row for row in passports if row.passport_status == "Expired"]),
		"passports_expiring_soon": len([row for row in passports if row.passport_status == "Expiring Soon"]),
		"expired_iqamas": len([row for row in iqamas if row.iqama_status == "Expired"]),
		"iqamas_expiring_soon": len([row for row in iqamas if row.iqama_status == "Expiring Soon"]),
	}


def get_employee_travel_profile_data(employee: str) -> dict:
	profile = frappe.db.get_value(
		"Employee Government Profile",
		{"employee": employee},
		[
			"name",
			"employee",
			"employee_name",
			"company",
			"department",
			"designation",
			"passport_number",
			"passport_expiry_date",
			"passport_status",
			"iqama_number",
			"iqama_expiry_date",
			"iqama_status",
			"current_sponsor",
			"qiwa_balance",
			"visa_status",
			"current_exit_reentry_visa",
			"is_outside_ksa",
			"last_exit_date",
			"expected_return_date",
			"actual_return_date",
			"latest_clearance",
		],
		as_dict=True,
	) or {}
	return {
		"profile": profile,
		"custodies": frappe.get_all(
			"Employee Custody",
			filters={"employee": employee, "status": ["not in", ["Returned", "Written Off"]]},
			fields=["name", "custody_type", "description", "estimated_value", "amount_due", "status"],
			limit_page_length=0,
		),
		"clearances": frappe.get_all(
			"Employee Clearance",
			filters={"employee": employee},
			fields=["name", "clearance_type", "status", "total_liability", "leave_application"],
			order_by="modified desc",
			limit_page_length=10,
		),
		"leaves": frappe.get_all(
			"Leave Application",
			filters={"employee": employee, "custom_is_outside_ksa": 1},
			fields=["name", "from_date", "to_date", "custom_return_status", "status"],
			order_by="from_date desc",
			limit_page_length=10,
		),
		"visas": frappe.get_all(
			"Employee Visa",
			filters={"employee": employee},
			fields=["name", "visa_type", "destination_country", "destination_city", "status", "expiry_date"],
			order_by="modified desc",
			limit_page_length=10,
		),
		"payments": frappe.get_all(
			"Government Payment Request",
			filters={"employee": employee},
			fields=["name", "payment_type", "company_payable_amount", "status", "payment_date"],
			order_by="modified desc",
			limit_page_length=10,
		),
		"tickets": frappe.get_all(
			"Travel Ticket Request",
			filters={"employee": employee},
			fields=["name", "departure_date", "return_date", "ticket_amount", "status", "booking_reference"],
			order_by="modified desc",
			limit_page_length=10,
		),
	}


def get_clearance_center_rows() -> list[dict]:
	rows = frappe.get_all(
		"Employee Clearance Item",
		filters={"status": ["in", ["Pending", "Rejected"]]},
		fields=["parent", "department", "item_type", "reference_doctype", "reference_name", "description", "amount", "mandatory", "status", "allow_travel_with_employee", "approved_by"],
		order_by="department asc, modified desc",
		limit_page_length=0,
	)
	return rows


def get_report_summary_card(label: str, value: float | int, indicator: str = "blue") -> dict:
	return {"value": value, "indicator": indicator, "label": _(label), "datatype": "Float"}
