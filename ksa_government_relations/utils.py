from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, get_datetime, getdate, now_datetime, today

from ksa_government_relations.constants import ACTIVE_VISA_STATUSES, FINAL_REQUEST_STATUSES, PAYMENT_ACCOUNT_FIELD_MAP


def get_settings():
	return frappe.get_single("Government Relations Settings")


def get_ticket_travel_dates(from_date, to_date, departure_after_days: int | None = None, return_before_days: int | None = None):
	departure_date = add_days(from_date, departure_after_days or 3)
	return_date = add_days(to_date, -(return_before_days or 1))

	# Short leaves can make the configured offsets cross over.
	# In that case, keep the ticket dates within the approved leave window.
	if getdate(return_date) < getdate(departure_date):
		departure_date = from_date
		return_date = to_date

	return departure_date, return_date


def get_first_available_value(doc, *fieldnames):
	for fieldname in fieldnames:
		if isinstance(doc, dict):
			value = doc.get(fieldname)
		else:
			value = getattr(doc, fieldname, None)
		if value not in (None, ""):
			return value
	return None


def get_employee_core_details(employee: str) -> dict[str, Any]:
	fields = [
		"name",
		"employee_name",
		"company",
		"branch",
		"department",
		"designation",
		"nationality",
		"custom_nationality",
		"custom_identity_type",
		"custom_government_portal",
		"user_id",
		"custom_iqama_number",
		"custom_iqama_issue_date",
		"custom_iqama_expiry_date",
		"custom_passport_number",
		"custom_passport_issue_date",
		"custom_passport_expiry_date",
		"custom_passport_issue_place",
		"custom_current_sponsor",
		"custom_qiwa_balance",
		"custom_is_outside_ksa",
		"custom_last_exit_date",
		"custom_expected_return_date",
		"custom_actual_return_date",
		"iqama_number",
		"passport_number",
		"date_of_issue",
		"valid_upto",
		"place_of_issue",
		"is_outside_ksa",
		"current_sponsor",
	]
	meta = frappe.get_meta("Employee")
	fields = [field for field in fields if field == "name" or meta.has_field(field)]
	return frappe.db.get_value("Employee", employee, fields, as_dict=True) or {}


def get_employee_nationality(employee_doc) -> str | None:
	if not employee_doc:
		return None
	if isinstance(employee_doc, dict):
		return employee_doc.get("custom_nationality") or employee_doc.get("nationality")
	return getattr(employee_doc, "custom_nationality", None) or getattr(employee_doc, "nationality", None)


def get_or_create_government_profile(employee: str):
	profile_name = frappe.db.get_value("Employee Government Profile", {"employee": employee}, "name")
	if profile_name:
		return frappe.get_doc("Employee Government Profile", profile_name)

	employee_doc = get_employee_core_details(employee)
	if not employee_doc:
		frappe.throw(_("Employee {0} was not found.").format(employee))

	doc = frappe.get_doc(
		{
			"doctype": "Employee Government Profile",
			"employee": employee_doc.name,
			"employee_name": employee_doc.employee_name,
			"company": employee_doc.company,
			"branch": employee_doc.branch,
			"department": employee_doc.department,
			"designation": employee_doc.designation,
			"nationality": get_employee_nationality(employee_doc),
			"identity_type": employee_doc.get("custom_identity_type") or "Resident",
			"government_portal": employee_doc.get("custom_government_portal"),
			"iqama_number": get_first_available_value(employee_doc, "custom_iqama_number", "iqama_number"),
			"iqama_issue_date": employee_doc.get("custom_iqama_issue_date"),
			"iqama_expiry_date": employee_doc.custom_iqama_expiry_date,
			"passport_number": get_first_available_value(employee_doc, "custom_passport_number", "passport_number"),
			"passport_issue_date": get_first_available_value(employee_doc, "custom_passport_issue_date", "date_of_issue"),
			"passport_expiry_date": get_first_available_value(employee_doc, "custom_passport_expiry_date", "valid_upto"),
			"passport_issue_place": get_first_available_value(employee_doc, "custom_passport_issue_place", "place_of_issue"),
			"current_sponsor": get_first_available_value(employee_doc, "custom_current_sponsor", "current_sponsor"),
			"qiwa_balance": employee_doc.custom_qiwa_balance or 0,
			"is_outside_ksa": get_first_available_value(employee_doc, "custom_is_outside_ksa", "is_outside_ksa") or 0,
			"last_exit_date": employee_doc.get("custom_last_exit_date"),
			"expected_return_date": employee_doc.get("custom_expected_return_date"),
			"actual_return_date": employee_doc.get("custom_actual_return_date"),
		}
	)
	doc.insert(ignore_permissions=True)
	sync_profile_to_employee(doc)
	return doc


def sync_employee_to_profile(employee_doc):
	settings = get_settings()
	profile_name = frappe.db.get_value("Employee Government Profile", {"employee": employee_doc.name}, "name")
	if not profile_name and settings.auto_create_profile_on_employee_creation:
		profile = get_or_create_government_profile(employee_doc.name)
		profile_name = profile.name
	if not profile_name:
		return None

	values = {
		"employee_name": employee_doc.employee_name,
		"company": employee_doc.company,
		"branch": getattr(employee_doc, "branch", None),
		"department": employee_doc.department,
		"designation": employee_doc.designation,
		"nationality": get_employee_nationality(employee_doc),
		"identity_type": getattr(employee_doc, "custom_identity_type", None) or "Resident",
		"government_portal": getattr(employee_doc, "custom_government_portal", None),
		"iqama_number": get_first_available_value(employee_doc, "custom_iqama_number", "iqama_number"),
		"iqama_issue_date": getattr(employee_doc, "custom_iqama_issue_date", None),
		"iqama_expiry_date": getattr(employee_doc, "custom_iqama_expiry_date", None),
		"passport_number": get_first_available_value(employee_doc, "custom_passport_number", "passport_number"),
		"passport_issue_date": get_first_available_value(employee_doc, "custom_passport_issue_date", "date_of_issue"),
		"passport_expiry_date": get_first_available_value(employee_doc, "custom_passport_expiry_date", "valid_upto"),
		"passport_issue_place": get_first_available_value(employee_doc, "custom_passport_issue_place", "place_of_issue"),
		"current_sponsor": get_first_available_value(employee_doc, "custom_current_sponsor", "current_sponsor"),
		"qiwa_balance": getattr(employee_doc, "custom_qiwa_balance", 0) or 0,
		"is_outside_ksa": get_first_available_value(employee_doc, "custom_is_outside_ksa", "is_outside_ksa") or 0,
		"last_exit_date": getattr(employee_doc, "custom_last_exit_date", None),
		"expected_return_date": getattr(employee_doc, "custom_expected_return_date", None),
		"actual_return_date": getattr(employee_doc, "custom_actual_return_date", None),
	}
	frappe.db.set_value("Employee Government Profile", profile_name, values, update_modified=False)
	frappe.db.set_value("Employee", employee_doc.name, "custom_government_profile", profile_name, update_modified=False)
	profile = frappe.get_doc("Employee Government Profile", profile_name)
	refresh_profile_status(profile)
	frappe.db.set_value(
		"Employee Government Profile",
		profile_name,
		{
			"iqama_status": profile.iqama_status,
			"passport_status": profile.passport_status,
			"visa_status": profile.visa_status,
			"current_exit_reentry_visa": profile.current_exit_reentry_visa,
			"visa_expiry_date": profile.visa_expiry_date,
		},
		update_modified=False,
	)
	sync_profile_to_employee(profile)
	return profile


def sync_profile_to_employee(profile):
	if not profile.employee or not frappe.db.exists("Employee", profile.employee):
		return

	values = {
		"custom_government_profile": profile.name,
		"custom_passport_status": profile.passport_status,
		"custom_visa_status": profile.visa_status,
		"custom_current_exit_reentry_visa": profile.current_exit_reentry_visa,
		"custom_latest_clearance": profile.latest_clearance,
		}
	frappe.db.set_value("Employee", profile.employee, values, update_modified=False)


def get_expiry_status(expiry_date, alert_days: int, missing_status: str = "Missing") -> str:
	if not expiry_date:
		return missing_status
	days = date_diff(expiry_date, today())
	if days < 0:
		return "Expired"
	if days <= alert_days:
		return "Expiring Soon"
	return "Valid"


def get_active_employee_visa(employee: str):
	visa = frappe.get_all(
		"Employee Visa",
		filters={"employee": employee, "status": ["in", ACTIVE_VISA_STATUSES], "visa_type": "Exit Re-entry"},
		fields=["name", "status", "expiry_date"],
		order_by="expiry_date desc",
		limit=1,
	)
	return visa[0] if visa else None


def refresh_profile_status(profile_doc):
	settings = get_settings()
	active_visa = get_active_employee_visa(profile_doc.employee) if profile_doc.employee else None
	values = {
		"iqama_status": get_expiry_status(profile_doc.iqama_expiry_date, settings.minimum_iqama_validity_days_after_return or 30),
		"passport_status": get_expiry_status(profile_doc.passport_expiry_date, settings.minimum_passport_validity_days_after_return or 30),
		"visa_status": "Active" if active_visa else "No Active Visa",
		"current_exit_reentry_visa": active_visa.name if active_visa else None,
		"visa_expiry_date": active_visa.expiry_date if active_visa else None,
	}
	if active_visa and active_visa.expiry_date and getdate(active_visa.expiry_date) < getdate(today()):
		values["visa_status"] = "Expired"
	elif not active_visa and profile_doc.current_exit_reentry_visa:
		values["visa_status"] = "Cancelled"

	for fieldname, value in values.items():
		setattr(profile_doc, fieldname, value)
	if not profile_doc.is_new():
		sync_profile_to_employee(profile_doc)
	return profile_doc


def get_employee_snapshot(employee: str) -> dict[str, Any]:
	profile = get_or_create_government_profile(employee)
	refresh_profile_status(profile)
	profile.reload()
	employee_doc = get_employee_core_details(employee)
	return {
		"employee": employee,
		"employee_name": profile.employee_name or employee_doc.get("employee_name"),
		"company": profile.company or employee_doc.get("company"),
		"branch": profile.branch or employee_doc.get("branch"),
		"department": profile.department or employee_doc.get("department"),
		"designation": profile.designation or employee_doc.get("designation"),
		"nationality": profile.nationality or get_employee_nationality(employee_doc),
		"identity_type": profile.identity_type,
		"government_portal": profile.government_portal,
		"government_profile": profile.name,
		"employee_government_profile": profile.name,
		"iqama_number": profile.iqama_number,
		"iqama_issue_date": profile.iqama_issue_date,
		"iqama_expiry_date": profile.iqama_expiry_date,
		"iqama_status": profile.iqama_status,
		"passport_number": profile.passport_number,
		"passport_issue_date": profile.passport_issue_date,
		"passport_expiry_date": profile.passport_expiry_date,
		"passport_issue_place": profile.passport_issue_place,
		"passport_status": profile.passport_status,
		"current_sponsor": profile.current_sponsor,
		"qiwa_balance": profile.qiwa_balance,
		"is_outside_ksa": profile.is_outside_ksa,
		"current_exit_reentry_visa": profile.current_exit_reentry_visa,
		"visa_status": profile.visa_status,
		"latest_clearance": profile.latest_clearance,
	}


def validate_outside_ksa_leave_requirements(leave_doc) -> list[str]:
	if not leave_doc.employee:
		return [_("Employee is required.")]

	profile = get_or_create_government_profile(leave_doc.employee)
	refresh_profile_status(profile)
	settings = get_settings()
	issues = []
	return_date = leave_doc.custom_expected_return_date or leave_doc.to_date
	travel_date = leave_doc.custom_expected_travel_date or leave_doc.from_date

	if not profile.passport_number:
		issues.append(_("Passport is missing."))
	if settings.block_if_passport_expired and profile.passport_status == "Expired":
		issues.append(_("Passport is expired."))
	if profile.passport_expiry_date and return_date:
		minimum_passport_date = add_days(getdate(return_date), settings.minimum_passport_validity_days_after_return or 30)
		if getdate(profile.passport_expiry_date) < minimum_passport_date:
			issues.append(_("Passport will expire before the required validity period after return."))

	if not profile.iqama_number:
		issues.append(_("Iqama is missing."))
	if settings.block_if_iqama_expired and profile.iqama_status == "Expired":
		issues.append(_("Iqama is expired."))
	if profile.iqama_expiry_date and return_date:
		minimum_iqama_date = add_days(getdate(return_date), settings.minimum_iqama_validity_days_after_return or 30)
		if getdate(profile.iqama_expiry_date) < minimum_iqama_date:
			issues.append(_("Iqama will expire before the required validity period after return."))

	if profile.is_outside_ksa:
		issues.append(_("Employee is already marked as outside KSA."))

	conflicting_visa = get_active_employee_visa(leave_doc.employee)
	if conflicting_visa and travel_date and conflicting_visa.get("expiry_date") and getdate(conflicting_visa.expiry_date) >= getdate(travel_date):
		issues.append(_("Employee already has an active exit re-entry visa that conflicts with this leave."))

	if has_outstanding_custodies(leave_doc.employee):
		issues.append(_("Employee has mandatory custody or asset items pending clearance."))
	if has_outstanding_financials(leave_doc.employee):
		issues.append(_("Employee has open financial liabilities that must be reviewed."))

	return issues


def has_outstanding_custodies(employee: str) -> bool:
	if frappe.db.exists("Employee Custody", {"employee": employee, "status": ["not in", ["Returned", "Written Off"]]}):
		return True
	if frappe.db.exists("Asset", {"custodian": employee, "docstatus": ["!=", 2]}):
		return True
	return False


def has_outstanding_financials(employee: str) -> bool:
	if frappe.db.exists("Employee Advance", {"employee": employee, "docstatus": 1, "status": ["in", ["Paid", "Unpaid", "Claimed", "Partly Claimed and Returned"]]}):
		return True
	if frappe.db.exists("Expense Claim", {"employee": employee, "docstatus": 1, "status": ["in", ["Submitted", "Unpaid"]]}):
		return True
	if frappe.db.exists("DocType", "Loan"):
		loan_fields = {d.fieldname for d in frappe.get_meta("Loan").fields}
		party_field = "applicant" if "applicant" in loan_fields else "employee" if "employee" in loan_fields else None
		if party_field and frappe.db.exists("Loan", {party_field: employee, "docstatus": 1, "status": ["not in", ["Closed", "Cancelled"]]}):
			return True
	return False


def get_employee_daily_rate(employee: str) -> float:
	last_slip = frappe.db.get_value(
		"Salary Slip",
		{"employee": employee, "docstatus": 1},
		["gross_pay", "payment_days"],
		order_by="end_date desc",
		as_dict=True,
	)
	if last_slip and flt(last_slip.payment_days):
		return flt(last_slip.gross_pay) / flt(last_slip.payment_days)

	assignment = frappe.db.get_value(
		"Salary Structure Assignment",
		{"employee": employee, "docstatus": 1},
		["base"],
		order_by="from_date desc",
		as_dict=True,
	)
	if assignment and flt(assignment.base):
		return flt(assignment.base) / 30
	return 0


def get_leave_settlement_rows(employee: str) -> list[dict]:
	rows = []
	if not frappe.db.exists("DocType", "Leave Type"):
		return rows

	try:
		from hrms.api import get_leave_balance_map
	except Exception:
		return rows

	leave_map = get_leave_balance_map(employee) or {}
	daily_rate = get_employee_daily_rate(employee)
	for leave_type, details in leave_map.items():
		meta = frappe.db.get_value(
			"Leave Type",
			leave_type,
			["allow_encashment", "max_encashable_leaves", "non_encashable_leaves"],
			as_dict=True,
		) or {}
		balance = flt(details.get("balance_leaves"))
		if not balance:
			continue

		if meta.get("allow_encashment"):
			encashable = max(balance - flt(meta.get("non_encashable_leaves")), 0)
			max_encashable = flt(meta.get("max_encashable_leaves"))
			if max_encashable:
				encashable = min(encashable, max_encashable)
			if encashable > 0:
				rows.append(
					{
						"department": "HR",
						"item_type": "Leave Encashment",
						"reference_doctype": "Leave Type",
						"reference_name": leave_type,
						"description": _("Leave encashment for {0} ({1} days)").format(leave_type, encashable),
						"amount": flt(encashable) * flt(daily_rate),
						"mandatory": 0,
						"status": "Approved",
					}
				)
		else:
			rows.append(
				{
					"department": "HR",
					"item_type": "Leave Deduction",
					"reference_doctype": "Leave Type",
					"reference_name": leave_type,
					"description": _("Leave balance review for {0} ({1} days)").format(leave_type, balance),
					"amount": flt(balance) * flt(daily_rate),
					"mandatory": 0,
					"status": "Pending",
				}
			)
	return rows


def get_outstanding_clearance_items(employee: str) -> list[dict]:
	items = []
	for custody in frappe.get_all(
		"Employee Custody",
		filters={"employee": employee, "status": ["not in", ["Returned", "Written Off"]]},
		fields=["name", "custody_type", "description", "amount_due", "estimated_value"],
		limit_page_length=0,
	):
		items.append(
			{
				"department": "Assets",
				"item_type": "Custody",
				"reference_doctype": "Employee Custody",
				"reference_name": custody.name,
				"description": custody.description or custody.custody_type,
				"amount": custody.amount_due or custody.estimated_value,
				"mandatory": 1,
				"status": "Pending",
			}
		)

	if frappe.db.exists("DocType", "Asset"):
		for asset in frappe.get_all(
			"Asset",
			filters={"custodian": employee, "docstatus": ["!=", 2]},
			fields=["name", "asset_name", "gross_purchase_amount"],
			limit_page_length=0,
		):
			items.append(
				{
					"department": "Assets",
					"item_type": "Asset",
					"reference_doctype": "Asset",
					"reference_name": asset.name,
					"description": asset.asset_name or asset.name,
					"amount": asset.gross_purchase_amount,
					"mandatory": 1,
					"status": "Pending",
				}
			)

	if frappe.db.exists("DocType", "Employee Advance"):
		for advance in frappe.get_all(
			"Employee Advance",
			filters={"employee": employee, "docstatus": 1, "status": ["in", ["Paid", "Unpaid", "Claimed", "Partly Claimed and Returned"]]},
			fields=["name", "purpose", "advance_amount", "claimed_amount", "return_amount"],
			limit_page_length=0,
		):
			outstanding = max(flt(advance.advance_amount) - flt(advance.claimed_amount) - flt(advance.return_amount), 0)
			if outstanding <= 0:
				continue
			items.append(
				{
					"department": "Finance",
					"item_type": "Employee Advance",
					"reference_doctype": "Employee Advance",
					"reference_name": advance.name,
					"description": advance.purpose or advance.name,
					"amount": outstanding,
					"mandatory": 1,
					"status": "Pending",
				}
			)

	if frappe.db.exists("DocType", "Loan"):
		loan_fields = [d.fieldname for d in frappe.get_meta("Loan").fields]
		party_field = "applicant" if "applicant" in loan_fields else "employee" if "employee" in loan_fields else None
		if party_field:
			for loan in frappe.get_all(
				"Loan",
				filters={party_field: employee, "docstatus": 1},
				fields=["name", "loan_amount", "total_amount_paid", "status"],
				limit_page_length=0,
			):
				if loan.status in ("Closed", "Cancelled"):
					continue
				outstanding = max(flt(loan.loan_amount) - flt(loan.total_amount_paid), 0)
				if outstanding <= 0:
					continue
				items.append(
					{
						"department": "Finance",
						"item_type": "Loan",
						"reference_doctype": "Loan",
						"reference_name": loan.name,
						"description": _("Outstanding loan repayment"),
						"amount": outstanding,
						"mandatory": 1,
						"status": "Pending",
					}
				)

	if frappe.db.exists("DocType", "Expense Claim"):
		for claim in frappe.get_all(
			"Expense Claim",
			filters={"employee": employee, "docstatus": 1, "status": ["in", ["Submitted", "Unpaid"]]},
			fields=["name", "total_claimed_amount", "total_amount_reimbursed", "remark"],
			limit_page_length=0,
		):
			outstanding = max(flt(claim.total_claimed_amount) - flt(claim.total_amount_reimbursed), 0)
			if outstanding <= 0:
				continue
			items.append(
				{
					"department": "Finance",
					"item_type": "Expense Claim",
					"reference_doctype": "Expense Claim",
					"reference_name": claim.name,
					"description": claim.remark or _("Unreimbursed expense claim"),
					"amount": outstanding,
					"mandatory": 0,
					"status": "Pending",
				}
			)

	items.extend(get_leave_settlement_rows(employee))
	return items


def _pick_best_pricing_rule(rows, criteria: list[tuple[str, Any, int]]):
	best_row = None
	best_score = -1

	for row in rows:
		score = 0
		matched = True
		for fieldname, expected, weight in criteria:
			row_value = row.get(fieldname)
			if row_value in (None, ""):
				continue
			if expected in (None, ""):
				matched = False
				break
			if str(row_value) != str(expected):
				matched = False
				break
			score += weight

		if matched and score > best_score:
			best_row = row
			best_score = score

	return best_row


def _pick_with_fallback(rows, strict_criteria: list[tuple[str, Any, int]], fallback_criteria: list[tuple[str, Any, int]]):
	return _pick_best_pricing_rule(rows, strict_criteria) or _pick_best_pricing_rule(rows, fallback_criteria)


def _match_visa_duration_range(row, requested_days):
	requested_days = flt(requested_days) if requested_days else None
	minimum_days = flt(row.get("minimum_days")) if row.get("minimum_days") not in (None, "") else None
	maximum_days = flt(row.get("maximum_days")) if row.get("maximum_days") not in (None, "") else None
	legacy_exact_days = flt(row.get("duration_days")) if row.get("duration_days") not in (None, "") else None

	if minimum_days is not None and minimum_days <= 0:
		minimum_days = None
	if maximum_days is not None and maximum_days <= 0:
		maximum_days = None
	if legacy_exact_days is not None and legacy_exact_days <= 0:
		legacy_exact_days = None

	if requested_days is None:
		return True, 0, 999999

	if minimum_days is not None and maximum_days is not None and minimum_days == maximum_days:
		return requested_days <= maximum_days, 4, maximum_days

	if minimum_days is None and maximum_days is None and legacy_exact_days not in (None, 0):
		return requested_days == legacy_exact_days, 6, 0

	if minimum_days is not None and requested_days < minimum_days:
		return False, -1, 999999
	if maximum_days is not None and requested_days > maximum_days:
		return False, -1, 999999

	range_score = 0
	if minimum_days is not None:
		range_score += 2
	if maximum_days is not None:
		range_score += 2
	range_span = (maximum_days - minimum_days) if minimum_days is not None and maximum_days is not None else 999999
	return True, range_score, range_span


def _pick_best_visa_pricing_rule(rows, criteria: list[tuple[str, Any, int]], requested_days):
	best_row = None
	best_key = None

	for row in rows:
		score = 0
		matched = True
		for fieldname, expected, weight in criteria:
			row_value = row.get(fieldname)
			if row_value in (None, ""):
				continue
			if expected in (None, ""):
				matched = False
				break
			if str(row_value) != str(expected):
				matched = False
				break
			score += weight

		if not matched:
			continue

		duration_matched, duration_score, range_span = _match_visa_duration_range(row, requested_days)
		if not duration_matched:
			continue

		key = (score, duration_score, -range_span)
		if best_key is None or key > best_key:
			best_row = row
			best_key = key

	return best_row


def get_visa_pricing(
	country=None,
	destination_city=None,
	nationality=None,
	departure_airport=None,
	arrival_airport=None,
	visa_type="Exit Re-entry",
	entry_type="Single",
	duration_days=0,
):
	filters = {"active": 1, "visa_type": visa_type, "entry_type": entry_type}
	if country:
		filters["country"] = country
	rows = frappe.get_all(
		"Visa Pricing Rule",
		filters=filters,
		fields=[
			"name",
			"nationality",
			"country",
			"departure_airport",
			"arrival_airport",
			"destination_city",
			"minimum_days",
			"maximum_days",
			"duration_days",
			"amount",
			"account",
			"cost_center",
		],
		limit_page_length=0,
	)
	strict_criteria = [
		("nationality", nationality, 8),
		("country", country, 5),
		("departure_airport", departure_airport, 7),
		("arrival_airport", arrival_airport, 6),
		("destination_city", destination_city, 3),
	]
	fallback_criteria = [
		("nationality", nationality, 8),
		("country", country, 5),
		("departure_airport", departure_airport, 7),
		("arrival_airport", arrival_airport, 6),
	]
	return _pick_best_visa_pricing_rule(rows, strict_criteria, duration_days) or _pick_best_visa_pricing_rule(
		rows, fallback_criteria, duration_days
	)


def get_ticket_pricing(
	country=None,
	destination_city=None,
	nationality=None,
	departure_airport=None,
	arrival_airport=None,
	ticket_class="Economy",
):
	filters = {"active": 1}
	if country:
		filters["country"] = country
	if ticket_class:
		filters["ticket_class"] = ticket_class
	rows = frappe.get_all(
		"Ticket Pricing Rule",
		filters=filters,
		fields=[
			"name",
			"nationality",
			"country",
			"departure_airport",
			"arrival_airport",
			"destination_city",
			"ticket_class",
			"amount",
			"account",
			"cost_center",
		],
		limit_page_length=0,
	)
	return _pick_with_fallback(
		rows,
		[
			("nationality", nationality, 8),
			("country", country, 5),
			("departure_airport", departure_airport, 7),
			("arrival_airport", arrival_airport, 6),
			("destination_city", destination_city, 3),
			("ticket_class", ticket_class, 4),
		],
		[
			("nationality", nationality, 8),
			("country", country, 5),
			("departure_airport", departure_airport, 7),
			("arrival_airport", arrival_airport, 6),
			("ticket_class", ticket_class, 4),
		],
	)


def get_payment_defaults(payment_type: str, company: str | None = None, **pricing_kwargs):
	settings = get_settings()
	account = None
	cost_center = settings.default_cost_center

	pricing_rule = None
	if payment_type == "Exit Re-entry Visa Fee":
		pricing_rule = get_visa_pricing(
			country=pricing_kwargs.get("country"),
			destination_city=pricing_kwargs.get("destination_city"),
			nationality=pricing_kwargs.get("nationality"),
			visa_type=pricing_kwargs.get("visa_type"),
			entry_type=pricing_kwargs.get("entry_type"),
			duration_days=pricing_kwargs.get("duration_days"),
			departure_airport=pricing_kwargs.get("departure_airport"),
			arrival_airport=pricing_kwargs.get("arrival_airport"),
		)
	elif payment_type == "Ticket Fee":
		pricing_rule = get_ticket_pricing(
			country=pricing_kwargs.get("country"),
			destination_city=pricing_kwargs.get("destination_city"),
			nationality=pricing_kwargs.get("nationality"),
			departure_airport=pricing_kwargs.get("departure_airport"),
			arrival_airport=pricing_kwargs.get("arrival_airport"),
			ticket_class=pricing_kwargs.get("ticket_class", "Economy"),
		)
	elif payment_type == "Sponsorship Transfer Fee":
		pricing_rule = None

	if pricing_rule:
		account = pricing_rule.account or account
		cost_center = pricing_rule.cost_center or cost_center

	account_field = PAYMENT_ACCOUNT_FIELD_MAP.get(payment_type)
	if not account and account_field:
		account = getattr(settings, account_field, None)

	return {
		"account": account,
		"payment_account": settings.default_payment_account,
		"cost_center": cost_center or frappe.db.get_value("Company", company or settings.default_company, "cost_center"),
		"pricing_rule": pricing_rule,
	}


def create_government_request_log(parent_doc, action_type: str, status: str, comment: str | None = None):
	parent_doc.append(
		"execution_logs",
		{
			"action_type": action_type,
			"status": status,
			"done_by": frappe.session.user,
			"done_by_name": frappe.db.get_value("User", frappe.session.user, "full_name"),
			"action_datetime": now_datetime(),
			"comment": comment or "",
		},
	)


def resolve_government_request_links(request_doc) -> dict[str, str | None]:
	links = {
		"linked_visa": None,
		"linked_payment_request": None,
		"linked_ticket_request": None,
		"linked_clearance": None,
	}

	if getattr(request_doc, "leave_application", None) and frappe.db.exists("Leave Application", request_doc.leave_application):
		leave_links = frappe.db.get_value(
			"Leave Application",
			request_doc.leave_application,
			[
				"custom_linked_employee_visa",
				"custom_linked_payment_request",
				"custom_linked_ticket_request",
				"custom_linked_clearance",
			],
			as_dict=True,
		) or {}
		links.update(
			{
				"linked_visa": leave_links.get("custom_linked_employee_visa"),
				"linked_payment_request": leave_links.get("custom_linked_payment_request"),
				"linked_ticket_request": leave_links.get("custom_linked_ticket_request"),
				"linked_clearance": leave_links.get("custom_linked_clearance"),
			}
		)

	if request_doc.request_type == "Issue Exit Re-entry Visa":
		payment_name = frappe.db.get_value(
			"Government Payment Request",
			{"employee": request_doc.employee, "visa_request": request_doc.name},
			"name",
			order_by="creation desc",
		)
		ticket_name = frappe.db.get_value(
			"Travel Ticket Request",
			{"employee": request_doc.employee, "visa_request": request_doc.name},
			"name",
			order_by="creation desc",
		)
		if payment_name:
			links["linked_payment_request"] = payment_name
		if ticket_name:
			links["linked_ticket_request"] = ticket_name

	if getattr(request_doc, "parent_request", None):
		parent_request = frappe.db.get_value(
			"Government Request",
			request_doc.parent_request,
			["linked_clearance", "linked_ticket_request", "leave_application"],
			as_dict=True,
		) or {}
		links["linked_clearance"] = links["linked_clearance"] or parent_request.get("linked_clearance")
		links["linked_ticket_request"] = links["linked_ticket_request"] or parent_request.get("linked_ticket_request")
		if not getattr(request_doc, "leave_application", None) and parent_request.get("leave_application"):
			request_doc.leave_application = parent_request.get("leave_application")

	return links


def create_outside_ksa_workflow(leave_doc):
	from ksa_government_relations.ksa_government_relations.doctype.government_request.government_request import (
		sync_request_snapshot,
	)

	settings = get_settings()
	profile = get_or_create_government_profile(leave_doc.employee)
	snapshot = get_employee_snapshot(leave_doc.employee)
	duration_days = max(date_diff(leave_doc.to_date, leave_doc.from_date) + 1, 1)
	destination_country = leave_doc.custom_destination_country
	destination_city = leave_doc.custom_destination_city
	departure_airport = getattr(leave_doc, "custom_departure_airport", None)
	arrival_airport = getattr(leave_doc, "custom_arrival_airport", None)
	nationality = snapshot.get("nationality")
	entry_type = "Multiple" if duration_days > 90 else "Single"
	request_date = leave_doc.from_date if getdate(leave_doc.from_date) < getdate(today()) else today()

	main_request = frappe.get_doc(
		{
			"doctype": "Government Request",
			"request_type": "Outside KSA Leave Processing",
			"employee": leave_doc.employee,
			"employee_name": leave_doc.employee_name,
			"leave_application": leave_doc.name,
			"employee_government_profile": profile.name,
			"company": leave_doc.company,
			"department": leave_doc.department,
			"request_date": request_date,
			"due_date": leave_doc.from_date,
			"status": "Draft",
			"priority": "Medium",
			"amount": 0,
			"remarks": _("Auto-created from Leave Application {0}").format(leave_doc.name),
		}
	)
	create_government_request_log(main_request, "Auto Created", "Submitted", _("Created from leave application"))
	main_request.insert(ignore_permissions=True)
	main_request.submit()

	visa_request = None
	employee_visa = None
	if settings.auto_create_visa_request and leave_doc.custom_exit_reentry_required:
		visa_request = frappe.get_doc(
			{
				"doctype": "Government Request",
				"request_type": "Issue Exit Re-entry Visa",
				"employee": leave_doc.employee,
				"employee_name": leave_doc.employee_name,
				"leave_application": leave_doc.name,
				"employee_government_profile": profile.name,
				"company": leave_doc.company,
				"department": leave_doc.department,
				"request_date": request_date,
				"due_date": leave_doc.from_date,
				"status": "Draft",
				"priority": "High",
				"government_platform": "Muqeem",
				"parent_request": main_request.name,
				"remarks": _("Auto-created visa request for outside KSA leave"),
			}
		)
		create_government_request_log(visa_request, "Auto Created", "Waiting Payment", _("Waiting for visa fee payment"))
		visa_request.insert(ignore_permissions=True)
		visa_request.submit()
		visa_request.db_set("status", "Waiting Payment", update_modified=False)

		employee_visa = frappe.get_doc(
			{
				"doctype": "Employee Visa",
				"employee": leave_doc.employee,
				"employee_name": leave_doc.employee_name,
				"leave_application": leave_doc.name,
				"visa_request": visa_request.name,
				"destination_country": destination_country,
				"destination_city": destination_city,
				"nationality": nationality,
				"departure_airport": departure_airport,
				"arrival_airport": arrival_airport,
				"visa_type": "Exit Re-entry",
				"entry_type": entry_type,
				"duration_days": duration_days,
				"issue_date": leave_doc.from_date,
				"expiry_date": leave_doc.to_date,
				"status": "Requested",
				"notes": _("Auto-created from Leave Application {0}").format(leave_doc.name),
			}
		)
		employee_visa.insert(ignore_permissions=True)
		employee_visa.submit()
		visa_request.db_set("linked_visa", employee_visa.name, update_modified=False)

	clearance = None
	if settings.auto_create_clearance:
		clearance = frappe.get_doc(
			{
				"doctype": "Employee Clearance",
				"employee": leave_doc.employee,
				"employee_name": leave_doc.employee_name,
				"clearance_type": "Temporary Travel Clearance",
				"leave_application": leave_doc.name,
				"government_request": main_request.name,
				"status": "Draft",
				"notes": _("Auto-created from outside KSA leave"),
			}
		)
		clearance.insert(ignore_permissions=True)
		clearance.generate_clearance_items()
		clearance.save(ignore_permissions=True)
		clearance.db_set("status", clear_first_pending_status(clearance), update_modified=False)

	payment_request = None
	if settings.auto_create_payment_request and visa_request:
		payment_defaults = get_payment_defaults(
			"Exit Re-entry Visa Fee",
			company=leave_doc.company,
			country=destination_country,
			destination_city=destination_city,
			nationality=nationality,
			departure_airport=departure_airport,
			arrival_airport=arrival_airport,
			visa_type="Exit Re-entry",
			entry_type=entry_type,
			duration_days=duration_days,
		)
		visa_price = flt(employee_visa.visa_amount) if employee_visa else 0
		if not visa_price and payment_defaults["pricing_rule"]:
			visa_price = flt(payment_defaults["pricing_rule"].amount)
		payment_request = frappe.get_doc(
			{
				"doctype": "Government Payment Request",
				"employee": leave_doc.employee,
				"employee_name": leave_doc.employee_name,
				"leave_application": leave_doc.name,
				"government_request": main_request.name,
				"visa_request": visa_request.name,
				"company": leave_doc.company,
				"payment_type": "Exit Re-entry Visa Fee",
				"nationality": nationality,
				"destination_country": destination_country,
				"destination_city": destination_city,
				"departure_airport": departure_airport,
				"arrival_airport": arrival_airport,
				"visa_duration_days": duration_days,
				"visa_price": visa_price,
				"employee_qiwa_balance": snapshot.get("qiwa_balance") or 0,
				"account": payment_defaults["account"],
				"payment_account": payment_defaults["payment_account"],
				"cost_center": payment_defaults["cost_center"],
				"status": "Draft",
				"notes": _("Auto-created from outside KSA leave"),
			}
		)
		payment_request.insert(ignore_permissions=True)
		payment_request.submit()
		if employee_visa:
			frappe.db.set_value(
				"Employee Visa",
				employee_visa.name,
				{
					"payment_request": payment_request.name,
					"payment_request_status": payment_request.status,
					"status": "Waiting Payment" if payment_request.status == "Waiting Payment" else employee_visa.status,
				},
				update_modified=False,
			)

	ticket_request = None
	if settings.auto_create_ticket_request:
		departure_date, return_date = get_ticket_travel_dates(
			leave_doc.from_date,
			leave_doc.to_date,
			settings.default_departure_after_leave_start_days,
			settings.default_return_before_leave_end_days,
		)
		ticket_request = frappe.get_doc(
			{
				"doctype": "Travel Ticket Request",
				"employee": leave_doc.employee,
				"employee_name": leave_doc.employee_name,
				"leave_application": leave_doc.name,
				"government_request": main_request.name,
				"visa_request": visa_request.name if visa_request else None,
				"nationality": nationality,
				"destination_country": destination_country,
				"destination_city": destination_city,
				"departure_airport": departure_airport,
				"arrival_airport": arrival_airport,
				"departure_date": departure_date,
				"return_date": return_date,
				"account": settings.ticket_expense_account,
				"cost_center": settings.default_cost_center,
				"status": "Draft",
				"notes": _("Auto-created from outside KSA leave"),
			}
		)
		ticket_request.insert(ignore_permissions=True)
		ticket_request.submit()

	link_values = {
		"custom_linked_government_request": main_request.name,
		"custom_linked_visa_request": visa_request.name if visa_request else None,
		"custom_linked_employee_visa": employee_visa.name if employee_visa else None,
		"custom_linked_clearance": clearance.name if clearance else None,
		"custom_linked_payment_request": payment_request.name if payment_request else None,
		"custom_linked_ticket_request": ticket_request.name if ticket_request else None,
		"custom_gro_status": "Pending",
		"custom_finance_status": "Pending" if payment_request else "Not Required",
		"custom_clearance_status": "Pending" if clearance else "Not Required",
		"custom_ticket_status": "Requested" if ticket_request else "Not Required",
		"custom_return_status": "Outside KSA",
		"custom_expected_travel_date": leave_doc.custom_expected_travel_date or add_days(leave_doc.from_date, settings.default_departure_after_leave_start_days or 3),
		"custom_expected_return_date": leave_doc.custom_expected_return_date or leave_doc.to_date,
	}
	frappe.db.set_value("Leave Application", leave_doc.name, link_values, update_modified=False)

	main_request.db_set("linked_visa", employee_visa.name if employee_visa else None, update_modified=False)
	main_request.db_set("linked_payment_request", payment_request.name if payment_request else None, update_modified=False)
	main_request.db_set("linked_ticket_request", ticket_request.name if ticket_request else None, update_modified=False)
	main_request.db_set("linked_clearance", clearance.name if clearance else None, update_modified=False)
	for request_name in [main_request.name, visa_request.name if visa_request else None]:
		sync_request_snapshot(request_name)

	frappe.db.set_value(
		"Employee Government Profile",
		profile.name,
		{
			"is_outside_ksa": 1,
			"expected_return_date": link_values["custom_expected_return_date"],
			"last_exit_date": leave_doc.custom_actual_exit_date or link_values["custom_expected_travel_date"],
			"latest_clearance": clearance.name if clearance else profile.latest_clearance,
		},
		update_modified=False,
	)
	sync_profile_to_employee(frappe.get_doc("Employee Government Profile", profile.name))
	return {
		"government_request": main_request.name,
		"visa_request": visa_request.name if visa_request else None,
		"employee_visa": employee_visa.name if employee_visa else None,
		"clearance": clearance.name if clearance else None,
		"payment_request": payment_request.name if payment_request else None,
		"ticket_request": ticket_request.name if ticket_request else None,
	}


def clear_first_pending_status(clearance_doc) -> str:
	departments = {item.department for item in clearance_doc.clearance_items if item.status == "Pending"}
	if "Finance" in departments:
		return "Pending Finance Clearance"
	if {"Assets", "IT"} & departments:
		return "Pending Asset Clearance"
	if "HR" in departments:
		return "Pending HR Clearance"
	if "Government Relations" in departments:
		return "Pending Government Clearance"
	return "Cleared"


def sync_leave_return_tracking(leave_doc):
	if not getattr(leave_doc, "custom_is_outside_ksa", 0):
		return

	settings = get_settings()
	status = "Outside KSA"
	if leave_doc.custom_actual_return_date:
		status = "Returned"
	else:
		delay = date_diff(today(), leave_doc.to_date) if leave_doc.to_date and getdate(leave_doc.to_date) < getdate(today()) else 0
		if delay >= flt(settings.late_return_stage_3_days):
			status = "Late Return Stage 3"
		elif delay >= flt(settings.late_return_stage_2_days):
			status = "Late Return Stage 2"
		elif delay >= flt(settings.late_return_stage_1_days):
			status = "Late Return Stage 1"

	frappe.db.set_value("Leave Application", leave_doc.name, "custom_return_status", status, update_modified=False)

	profile_name = frappe.db.get_value("Employee Government Profile", {"employee": leave_doc.employee}, "name")
	if not profile_name:
		return
	profile = frappe.get_doc("Employee Government Profile", profile_name)
	profile.expected_return_date = leave_doc.custom_expected_return_date or leave_doc.to_date
	profile.actual_return_date = leave_doc.custom_actual_return_date
	profile.is_outside_ksa = 0 if leave_doc.custom_actual_return_date else 1
	profile.last_exit_date = leave_doc.custom_actual_exit_date or profile.last_exit_date
	profile.save(ignore_permissions=True)


def cancel_outside_ksa_documents(leave_doc):
	for doctype, fieldname in [
		("Travel Ticket Request", "custom_linked_ticket_request"),
		("Government Payment Request", "custom_linked_payment_request"),
		("Employee Clearance", "custom_linked_clearance"),
		("Employee Visa", "custom_linked_employee_visa"),
		("Government Request", "custom_linked_visa_request"),
		("Government Request", "custom_linked_government_request"),
	]:
		name = getattr(leave_doc, fieldname, None)
		if not name or not frappe.db.exists(doctype, name):
			continue
		doc = frappe.get_doc(doctype, name)
		if doc.docstatus == 1:
			doc.cancel()


def create_notification_logs(users: list[str], subject: str, document_type: str | None = None, document_name: str | None = None):
	for user in {u for u in users if u and u != "Guest"}:
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": subject,
					"for_user": user,
					"type": "Alert",
					"document_type": document_type,
					"document_name": document_name,
					"from_user": frappe.session.user if frappe.session.user != "Guest" else "Administrator",
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Government Relations Notification")
