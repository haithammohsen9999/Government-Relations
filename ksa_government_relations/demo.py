from __future__ import annotations

from typing import Callable

import frappe
from frappe.utils import add_days, flt, getdate, nowdate, today

from ksa_government_relations.api import sync_return_tracking
from ksa_government_relations.install import ensure_saudi_airports
from ksa_government_relations.utils import create_outside_ksa_workflow, get_employee_snapshot, get_or_create_government_profile, get_payment_defaults, get_settings

DEMO_NOTE = "KSA Government Relations Demo Seed 2026"
DEMO_DESTINATIONS = [
	("Egypt", "Cairo"),
	("United Arab Emirates", "Dubai"),
	("India", "Mumbai"),
	("Jordan", "Amman"),
	("Turkey", "Istanbul"),
	("Bahrain", "Manama"),
]
DEMO_SAUDI_AIRPORTS = ("RUH", "JED", "DMM", "MED", "AHB", "TIF")
DEMO_ARRIVAL_AIRPORTS = {
	"Cairo": "CAI",
	"Dubai": "DXB",
	"Mumbai": "BOM",
	"Amman": "AMM",
	"Istanbul": "IST",
	"Manama": "BAH",
}
PASSPORT_EXPIRIES = (-10, 15, 260, 320, 410, 480, 540, 600, 700, 820)
IQAMA_EXPIRIES = (220, 180, -5, 20, 340, 430, 500, 610, 720, 860)
QIWA_BALANCES = (50, 100, 0, 75, 20, 40, 90, 10, 60, 30)


def seed_demo_data(company: str = "Tera") -> dict:
	frappe.set_user("Administrator")
	employee_meta = frappe.get_meta("Employee")
	employee_fields = ["name", "employee_name", "company", "department", "designation"]
	if employee_meta.has_field("nationality"):
		employee_fields.append("nationality")
	employees = frappe.get_all(
		"Employee",
		filters={"company": company, "status": "Active"},
		fields=employee_fields,
		order_by="creation asc",
		limit_page_length=12,
	)
	if not employees:
		frappe.throw(f"No active employees found for company {company}.")

	configure_settings(company)
	ensure_government_profiles(employees)
	fill_missing_profile_nationalities(company)
	ensure_employee_custodies(employees[:6])
	seed_leave_workflows(employees[4:10], company)
	backfill_legacy_outside_ksa_leaves(company)
	seed_sponsorship_transfers(employees[:3], company)
	reprice_existing_requests(company)
	frappe.db.commit()

	return {
		"profiles": frappe.db.count("Employee Government Profile"),
		"leave_applications": frappe.db.count("Leave Application", {"custom_is_outside_ksa": 1}),
		"government_requests": frappe.db.count("Government Request"),
		"visas": frappe.db.count("Employee Visa"),
		"payment_requests": frappe.db.count("Government Payment Request"),
		"ticket_requests": frappe.db.count("Travel Ticket Request"),
		"clearances": frappe.db.count("Employee Clearance"),
		"sponsorship_transfers": frappe.db.count("Sponsorship Transfer Request"),
	}


def reprice_existing_requests(company: str = "Tera"):
	leaves = frappe.get_all(
		"Leave Application",
		filters={"company": company, "custom_is_outside_ksa": 1},
		fields=[
			"name",
			"employee",
			"company",
			"from_date",
			"to_date",
			"custom_destination_country",
			"custom_destination_city",
			"custom_departure_airport",
			"custom_arrival_airport",
			"custom_linked_payment_request",
			"custom_linked_ticket_request",
		],
		limit_page_length=0,
	)
	for leave in leaves:
		snapshot = get_employee_snapshot(leave.employee)
		duration_days = max((getdate(leave.to_date) - getdate(leave.from_date)).days + 1, 1)
		entry_type = "Multiple" if duration_days > 90 else "Single"
		common = {
			"nationality": snapshot.get("nationality"),
			"destination_country": leave.custom_destination_country,
			"destination_city": leave.custom_destination_city,
			"departure_airport": leave.custom_departure_airport,
			"arrival_airport": leave.custom_arrival_airport,
		}

		if leave.custom_linked_payment_request and frappe.db.exists("Government Payment Request", leave.custom_linked_payment_request):
			defaults = get_payment_defaults(
				"Exit Re-entry Visa Fee",
				company=leave.company,
				country=leave.custom_destination_country,
				destination_city=leave.custom_destination_city,
				nationality=common["nationality"],
				departure_airport=common["departure_airport"],
				arrival_airport=common["arrival_airport"],
				visa_type="Exit Re-entry",
				entry_type=entry_type,
				duration_days=duration_days,
			)
			values = dict(common)
			if defaults.get("pricing_rule"):
				values["visa_price"] = defaults["pricing_rule"].amount
			if defaults.get("account"):
				values["account"] = defaults["account"]
			if defaults.get("payment_account"):
				values["payment_account"] = defaults["payment_account"]
			if defaults.get("cost_center"):
				values["cost_center"] = defaults["cost_center"]
			frappe.db.set_value("Government Payment Request", leave.custom_linked_payment_request, values, update_modified=False)

		if leave.custom_linked_ticket_request and frappe.db.exists("Travel Ticket Request", leave.custom_linked_ticket_request):
			ticket_defaults = get_payment_defaults(
				"Ticket Fee",
				company=leave.company,
				country=leave.custom_destination_country,
				destination_city=leave.custom_destination_city,
				nationality=common["nationality"],
				departure_airport=common["departure_airport"],
				arrival_airport=common["arrival_airport"],
			)
			values = dict(common)
			if ticket_defaults.get("pricing_rule"):
				values["ticket_amount"] = ticket_defaults["pricing_rule"].amount
			if ticket_defaults.get("account"):
				values["account"] = ticket_defaults["account"]
			if ticket_defaults.get("cost_center"):
				values["cost_center"] = ticket_defaults["cost_center"]
			frappe.db.set_value("Travel Ticket Request", leave.custom_linked_ticket_request, values, update_modified=False)


def get_demo_airport_pair(index: int, country: str, city: str) -> tuple[str, str]:
	departure_airport = DEMO_SAUDI_AIRPORTS[index % len(DEMO_SAUDI_AIRPORTS)]
	arrival_airport = DEMO_ARRIVAL_AIRPORTS.get(city) or (city[:3] or country[:3]).upper()
	return departure_airport, arrival_airport


def configure_settings(company: str):
	ensure_saudi_airports()
	settings = get_settings()
	company_doc = frappe.get_doc("Company", company)
	account_rows = frappe.get_all(
		"Account",
		filters={"company": company, "is_group": 0},
		fields=["name", "account_type", "root_type"],
		limit_page_length=0,
	)

	def pick(predicate: Callable[[dict], bool], fallback: str | None = None) -> str | None:
		for row in account_rows:
			if predicate(row):
				return row.name
		return fallback

	expense_account = pick(lambda row: row.root_type == "Expense")
	cash_account = pick(lambda row: row.account_type == "Cash") or expense_account
	receivable_account = pick(lambda row: row.account_type == "Receivable") or expense_account
	liability_account = pick(lambda row: row.root_type == "Liability") or cash_account

	settings.default_company = company
	settings.default_cost_center = company_doc.cost_center
	settings.default_currency = company_doc.default_currency or "EGP"
	settings.visa_expense_account = expense_account
	settings.qiwa_balance_account = receivable_account
	settings.ticket_expense_account = expense_account
	settings.sponsorship_transfer_expense_account = expense_account
	settings.government_fees_payable_account = liability_account
	settings.employee_receivable_account = receivable_account
	settings.default_payment_account = cash_account
	settings.auto_create_profile_on_employee_creation = 1
	settings.auto_create_visa_request = 1
	settings.auto_create_clearance = 1
	settings.auto_create_payment_request = 1
	settings.auto_create_ticket_request = 1
	settings.default_departure_after_leave_start_days = 3
	settings.default_return_before_leave_end_days = 1
	settings.minimum_passport_validity_days_after_return = 30
	settings.minimum_iqama_validity_days_after_return = 30

	settings.set("visa_pricing_rules", [])
	for nationality, country, city, departure_airport, arrival_airport, entry_type, duration_days, amount in [
		("Egypt", "Egypt", "Cairo", "RUH", "CAI", "Single", 0, 250),
		("United Arab Emirates", "United Arab Emirates", "Dubai", "JED", "DXB", "Single", 0, 320),
		("India", "India", "Mumbai", "DMM", "BOM", "Single", 0, 280),
		("Jordan", "Jordan", "Amman", "MED", "AMM", "Multiple", 0, 700),
		("Turkey", "Turkey", "Istanbul", "AHB", "IST", "Single", 0, 410),
		("Bahrain", "Bahrain", "Manama", "TIF", "BAH", "Single", 0, 230),
	]:
		settings.append(
			"visa_pricing_rules",
			{
				"nationality": nationality,
				"country": country,
				"departure_airport": departure_airport,
				"arrival_airport": arrival_airport,
				"destination_city": city,
				"visa_type": "Exit Re-entry",
				"entry_type": entry_type,
				"duration_days": duration_days,
				"amount": amount,
				"account": expense_account,
				"cost_center": company_doc.cost_center,
				"active": 1,
			},
		)

	settings.set("ticket_pricing_rules", [])
	for nationality, country, city, departure_airport, arrival_airport, ticket_class, amount in [
		("Egypt", "Egypt", "Cairo", "RUH", "CAI", "Economy", 950),
		("United Arab Emirates", "United Arab Emirates", "Dubai", "JED", "DXB", "Economy", 1250),
		("India", "India", "Mumbai", "DMM", "BOM", "Economy", 1180),
		("Jordan", "Jordan", "Amman", "MED", "AMM", "Economy", 1100),
		("Turkey", "Turkey", "Istanbul", "AHB", "IST", "Economy", 1320),
		("Bahrain", "Bahrain", "Manama", "TIF", "BAH", "Economy", 990),
	]:
		settings.append(
			"ticket_pricing_rules",
			{
				"nationality": nationality,
				"country": country,
				"departure_airport": departure_airport,
				"arrival_airport": arrival_airport,
				"destination_city": city,
				"ticket_class": ticket_class,
				"amount": amount,
				"account": expense_account,
				"cost_center": company_doc.cost_center,
				"active": 1,
			},
		)

	settings.set("sponsorship_transfer_pricing_rules", [])
	for direction, nationality, amount in [
		("Into Company", "Egypt", 2200),
		("Out of Company", "Egypt", 2500),
		("Between Companies", "India", 1800),
	]:
		settings.append(
			"sponsorship_transfer_pricing_rules",
			{
				"transfer_direction": direction,
				"nationality": nationality,
				"amount": amount,
				"account": expense_account,
				"cost_center": company_doc.cost_center,
				"active": 1,
			},
		)
	settings.save(ignore_permissions=True)


def ensure_government_profiles(employees: list[dict]):
	for idx, employee in enumerate(employees):
		nationality = getattr(employee, "nationality", None) or DEMO_DESTINATIONS[idx % len(DEMO_DESTINATIONS)][0]
		profile = get_or_create_government_profile(employee.name)
		profile.employee_name = employee.employee_name
		profile.company = employee.company
		profile.department = employee.department
		profile.designation = employee.designation
		profile.nationality = profile.nationality or nationality
		profile.identity_type = "Resident"
		profile.current_sponsor = "Tera Establishment"
		profile.qiwa_balance = QIWA_BALANCES[idx % len(QIWA_BALANCES)]
		profile.passport_number = profile.passport_number or f"P{20260000 + idx:08d}"
		profile.passport_issue_date = add_days(today(), -900 + idx * 7)
		profile.passport_expiry_date = add_days(today(), PASSPORT_EXPIRIES[idx % len(PASSPORT_EXPIRIES)])
		profile.passport_issue_place = "Riyadh"
		profile.iqama_number = profile.iqama_number or f"IQ{20260000 + idx:08d}"
		profile.iqama_issue_date = add_days(today(), -700 + idx * 11)
		profile.iqama_expiry_date = add_days(today(), IQAMA_EXPIRIES[idx % len(IQAMA_EXPIRIES)])
		profile.notes = DEMO_NOTE
		profile.save(ignore_permissions=True)


def fill_missing_profile_nationalities(company: str):
	profiles = frappe.get_all(
		"Employee Government Profile",
		filters={"company": company},
		fields=["name", "employee", "nationality"],
		limit_page_length=0,
	)
	for idx, profile in enumerate(profiles):
		if profile.nationality:
			continue
		leave_country = frappe.db.get_value(
			"Leave Application",
			{"employee": profile.employee, "custom_is_outside_ksa": 1},
			"custom_destination_country",
		)
		nationality = leave_country or DEMO_DESTINATIONS[idx % len(DEMO_DESTINATIONS)][0]
		frappe.db.set_value("Employee Government Profile", profile.name, "nationality", nationality, update_modified=False)


def ensure_employee_custodies(employees: list[dict]):
	custody_templates = [
		("Laptop", "Demo Laptop Lenovo ThinkPad", 4200),
		("Mobile", "Demo iPhone device", 2800),
		("SIM Card", "Demo corporate SIM", 250),
		("Access Card", "Demo access badge", 150),
	]
	for employee, template in zip(employees, custody_templates):
		custody_type, description, value = template
		existing = frappe.db.get_value(
			"Employee Custody",
			{"employee": employee.name, "description": description},
			"name",
		)
		if existing:
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Employee Custody",
				"employee": employee.name,
				"employee_name": employee.employee_name,
				"custody_type": custody_type,
				"description": description,
				"issue_date": add_days(today(), -90),
				"expected_return_date": add_days(today(), 30),
				"status": "Issued",
				"estimated_value": value,
				"amount_due": value,
				"notes": DEMO_NOTE,
			}
		)
		doc.insert(ignore_permissions=True)
		doc.submit()


def seed_leave_workflows(employees: list[dict], company: str):
	scenarios = [
		{"from_offset": 6, "to_offset": 14, "return_status": "Not Travelled", "payment_status": "Waiting Payment", "ticket_status": "Requested", "visa_status": "Requested", "request_status": "Waiting Payment", "clearance_status": "Pending Finance Clearance"},
		{"from_offset": -3, "to_offset": 6, "return_status": "Outside KSA", "payment_status": "Paid", "ticket_status": "Booked", "visa_status": "Active", "request_status": "Government Processing", "clearance_status": "Cleared"},
		{"from_offset": -15, "to_offset": -5, "return_status": "Late Return Stage 1", "payment_status": "Paid", "ticket_status": "Booked", "visa_status": "Used", "request_status": "Completed", "clearance_status": "Cleared"},
		{"from_offset": -75, "to_offset": -65, "return_status": "Late Return Stage 2", "payment_status": "Paid", "ticket_status": "Booked", "visa_status": "Expired", "request_status": "Completed", "clearance_status": "Cleared"},
		{"from_offset": -140, "to_offset": -130, "return_status": "Late Return Stage 3", "payment_status": "Paid", "ticket_status": "Booked", "visa_status": "Expired", "request_status": "Completed", "clearance_status": "Cleared"},
		{"from_offset": 18, "to_offset": 26, "return_status": "Not Travelled", "payment_status": "Waiting Payment", "ticket_status": "Waiting Approval", "visa_status": "Requested", "request_status": "Under Review", "clearance_status": "Pending Asset Clearance"},
	]

	for idx, employee in enumerate(employees[: len(scenarios)]):
		scenario = scenarios[idx]
		country, city = DEMO_DESTINATIONS[idx % len(DEMO_DESTINATIONS)]
		departure_airport, arrival_airport = get_demo_airport_pair(idx, country, city)
		leave = get_or_create_demo_leave(
			employee,
			company,
			add_days(today(), scenario["from_offset"]),
			add_days(today(), scenario["to_offset"]),
			country,
			city,
			departure_airport,
			arrival_airport,
		)
		doc_links = ensure_leave_workflow_documents(leave)
		apply_leave_scenario(leave, doc_links, scenario)


def get_or_create_demo_leave(employee: dict, company: str, from_date: str, to_date: str, country: str, city: str, departure_airport: str, arrival_airport: str):
	existing = frappe.db.get_value(
		"Leave Application",
		{"employee": employee.name, "from_date": from_date, "to_date": to_date, "custom_is_outside_ksa": 1},
		"name",
	)
	if existing:
		frappe.db.set_value(
			"Leave Application",
			existing,
			{
				"custom_destination_country": country,
				"custom_destination_city": city,
				"custom_departure_airport": departure_airport,
				"custom_arrival_airport": arrival_airport,
			},
			update_modified=False,
		)
		return frappe.get_doc("Leave Application", existing)

	leave = frappe.get_doc(
		{
			"doctype": "Leave Application",
			"employee": employee.name,
			"employee_name": employee.employee_name,
			"company": company,
			"department": employee.department,
			"leave_type": "Leave Without Pay",
			"from_date": from_date,
			"to_date": to_date,
			"posting_date": nowdate(),
			"status": "Approved",
			"leave_approver": "Administrator",
			"description": DEMO_NOTE,
		}
	)
	leave.set_new_name()
	leave.db_insert(ignore_if_duplicate=True)
	frappe.db.set_value(
		"Leave Application",
		leave.name,
		{
			"docstatus": 1,
			"status": "Approved",
				"custom_is_outside_ksa": 1,
				"custom_destination_country": country,
				"custom_destination_city": city,
				"custom_departure_airport": departure_airport,
				"custom_arrival_airport": arrival_airport,
				"custom_exit_reentry_required": 1,
			"custom_expected_travel_date": add_days(from_date, 3),
			"custom_expected_return_date": to_date,
		},
		update_modified=False,
	)
	return frappe.get_doc("Leave Application", leave.name)


def ensure_leave_workflow_documents(leave):
	links = {
		"government_request": leave.custom_linked_government_request,
		"visa_request": leave.custom_linked_visa_request,
		"employee_visa": leave.custom_linked_employee_visa,
		"clearance": leave.custom_linked_clearance,
		"payment_request": leave.custom_linked_payment_request,
		"ticket_request": leave.custom_linked_ticket_request,
	}
	if all(links.values()):
		return links

	result = create_outside_ksa_workflow(leave)
	return {
		"government_request": result.get("government_request"),
		"visa_request": result.get("visa_request"),
		"employee_visa": result.get("employee_visa"),
		"clearance": result.get("clearance"),
		"payment_request": result.get("payment_request"),
		"ticket_request": result.get("ticket_request"),
	}


def apply_leave_scenario(leave, links: dict, scenario: dict):
	snapshot = get_employee_snapshot(leave.employee)
	duration_days = max((getdate(leave.to_date) - getdate(leave.from_date)).days + 1, 1)
	entry_type = "Multiple" if duration_days > 90 else "Single"
	common_updates = {
		"nationality": snapshot.get("nationality"),
		"destination_country": leave.custom_destination_country,
		"destination_city": leave.custom_destination_city,
		"departure_airport": getattr(leave, "custom_departure_airport", None),
		"arrival_airport": getattr(leave, "custom_arrival_airport", None),
	}
	visa_defaults = get_payment_defaults(
		"Exit Re-entry Visa Fee",
		company=leave.company,
		country=leave.custom_destination_country,
		destination_city=leave.custom_destination_city,
		nationality=common_updates["nationality"],
		departure_airport=common_updates["departure_airport"],
		arrival_airport=common_updates["arrival_airport"],
		visa_type="Exit Re-entry",
		entry_type=entry_type,
		duration_days=duration_days,
	)
	ticket_defaults = get_payment_defaults(
		"Ticket Fee",
		company=leave.company,
		country=leave.custom_destination_country,
		destination_city=leave.custom_destination_city,
		nationality=common_updates["nationality"],
		departure_airport=common_updates["departure_airport"],
		arrival_airport=common_updates["arrival_airport"],
	)

	if links.get("ticket_request"):
		ticket_amount = flt(ticket_defaults["pricing_rule"].amount) if ticket_defaults.get("pricing_rule") else 950 + abs((getdate(leave.to_date) - getdate(leave.from_date)).days) * 15
		frappe.db.set_value(
			"Travel Ticket Request",
			links["ticket_request"],
			{
				**common_updates,
				"ticket_amount": ticket_amount,
				"airline": "Saudi Airlines",
				"booking_reference": f"PNR-{leave.employee[-4:]}",
				"ticket_number": f"TKT-{leave.employee[-4:]}",
				"status": scenario["ticket_status"],
			},
			update_modified=False,
		)

	if links.get("payment_request"):
		payment = frappe.get_doc("Government Payment Request", links["payment_request"])
		frappe.db.set_value(
			"Government Payment Request",
			payment.name,
			{
				**common_updates,
				"visa_price": flt(visa_defaults["pricing_rule"].amount) if visa_defaults.get("pricing_rule") else payment.visa_price,
				"account": visa_defaults.get("account") or payment.account,
				"payment_account": visa_defaults.get("payment_account") or payment.payment_account,
				"cost_center": visa_defaults.get("cost_center") or payment.cost_center,
			},
			update_modified=False,
		)
	if links.get("payment_request") and scenario["payment_status"] == "Paid":
		if payment.status not in ("Paid", "Posted to GL"):
			payment.flags.ignore_validate_update_after_submit = True
			payment.status = "Paid"
			payment.payment_date = today()
			payment.payment_reference = f"PAY-{leave.employee[-4:]}"
			payment.save(ignore_permissions=True)

	if links.get("visa_request"):
		frappe.db.set_value("Government Request", links["visa_request"], "status", scenario["request_status"], update_modified=False)
	if links.get("government_request"):
		frappe.db.set_value("Government Request", links["government_request"], "status", scenario["request_status"], update_modified=False)
	if links.get("employee_visa"):
		frappe.db.set_value(
			"Employee Visa",
			links["employee_visa"],
			{
				**common_updates,
				"status": scenario["visa_status"],
			},
			update_modified=False,
		)

	if links.get("clearance"):
		apply_clearance_scenario(links["clearance"], scenario["clearance_status"])

	leave_updates = {
		"custom_ticket_status": scenario["ticket_status"],
		"custom_finance_status": "Paid" if scenario["payment_status"] == "Paid" else "Pending",
		"custom_gro_status": "Approved" if scenario["payment_status"] == "Paid" else "Pending",
		"custom_clearance_status": "Cleared" if scenario["clearance_status"] == "Cleared" else "Pending",
	}
	frappe.db.set_value("Leave Application", leave.name, leave_updates, update_modified=False)

	if scenario["return_status"].startswith("Late Return"):
		frappe.db.set_value("Leave Application", leave.name, "custom_actual_return_date", None, update_modified=False)
		sync_return_tracking(frappe.get_doc("Leave Application", leave.name))
	elif scenario["return_status"] == "Outside KSA":
		sync_return_tracking(frappe.get_doc("Leave Application", leave.name))


def apply_clearance_scenario(clearance_name: str, target_status: str):
	clearance = frappe.get_doc("Employee Clearance", clearance_name)
	if target_status == "Cleared":
		for item in clearance.clearance_items:
			updates = {"comment": DEMO_NOTE}
			if item.item_type in ("Asset", "Custody"):
				updates["status"] = "Approved to Travel With Employee"
				updates["allow_travel_with_employee"] = 1
			elif item.item_type in ("Employee Advance", "Loan", "Expense Claim", "Government Payment"):
				updates["status"] = "Paid"
			else:
				updates["status"] = "Approved"
			frappe.db.set_value("Employee Clearance Item", item.name, updates, update_modified=False)
		frappe.db.set_value("Employee Clearance", clearance_name, "status", "Cleared", update_modified=False)
		if clearance.leave_application:
			frappe.db.set_value("Leave Application", clearance.leave_application, "custom_clearance_status", "Cleared", update_modified=False)
		if clearance.government_request:
			frappe.db.set_value("Government Request", clearance.government_request, "linked_clearance", clearance.name, update_modified=False)
		frappe.db.set_value("Employee", clearance.employee, "custom_latest_clearance", clearance.name, update_modified=False)
		return

	for item in clearance.clearance_items:
		updates = {"comment": DEMO_NOTE}
		if target_status == "Pending Asset Clearance" and item.department == "Finance":
			updates["status"] = "Paid"
		elif target_status == "Pending Finance Clearance" and item.department in ("Assets", "IT"):
			updates["status"] = "Approved to Travel With Employee"
			updates["allow_travel_with_employee"] = 1
		frappe.db.set_value("Employee Clearance Item", item.name, updates, update_modified=False)
	frappe.db.set_value("Employee Clearance", clearance_name, "status", target_status, update_modified=False)


def seed_sponsorship_transfers(employees: list[dict], company: str):
	scenarios = [
		("Into Company", "Tera Establishment", "Tera Manufacturing", "Approved"),
		("Out of Company", "Tera Establishment", "External Sponsor Co.", "Waiting Payment"),
		("Between Companies", "Tera Establishment", "Tera Logistics", "Completed"),
	]
	for employee, scenario in zip(employees, scenarios):
		transfer_direction, current_sponsor, new_sponsor, status = scenario
		existing = frappe.db.get_value(
			"Sponsorship Transfer Request",
			{"employee": employee.name, "transfer_direction": transfer_direction, "new_sponsor": new_sponsor},
			"name",
		)
		if existing:
			transfer = frappe.get_doc("Sponsorship Transfer Request", existing)
		else:
			transfer = frappe.get_doc(
				{
					"doctype": "Sponsorship Transfer Request",
					"employee": employee.name,
					"transfer_direction": transfer_direction,
					"current_sponsor": current_sponsor,
					"new_sponsor": new_sponsor,
					"status": "Draft",
					"qiwa_request_no": f"QIWA-{employee.name[-4:]}",
					"notes": DEMO_NOTE,
				}
			)
			transfer.insert(ignore_permissions=True)
			transfer.submit()

		frappe.db.set_value("Sponsorship Transfer Request", transfer.name, "status", status, update_modified=False)
		if status == "Completed" and transfer.employee:
			profile = get_or_create_government_profile(transfer.employee)
			frappe.db.set_value("Employee Government Profile", profile.name, "current_sponsor", new_sponsor, update_modified=False)

		if transfer.payment_request and status in ("Approved", "Completed"):
			payment = frappe.get_doc("Government Payment Request", transfer.payment_request)
			if payment.status not in ("Paid", "Posted to GL"):
				payment.flags.ignore_validate_update_after_submit = True
				payment.status = "Paid"
				payment.payment_date = today()
				payment.payment_reference = f"STRPAY-{employee.name[-4:]}"
				payment.save(ignore_permissions=True)


def backfill_legacy_outside_ksa_leaves(company: str):
	legacy_leaves = frappe.get_all(
		"Leave Application",
		filters={
			"company": company,
			"custom_is_outside_ksa": 1,
			"custom_linked_government_request": ["is", "set"],
			"custom_linked_visa_request": ["is", "not set"],
		},
		fields=["name", "employee", "employee_name", "company", "department", "from_date", "to_date", "custom_destination_country", "custom_destination_city", "custom_linked_government_request", "custom_linked_clearance"],
		limit_page_length=0,
	)
	for row in legacy_leaves:
		leave = frappe.get_doc("Leave Application", row.name)
		profile = get_or_create_government_profile(leave.employee)
		snapshot = get_employee_snapshot(leave.employee)
		duration_days = max((getdate(leave.to_date) - getdate(leave.from_date)).days + 1, 1)
		entry_type = "Multiple" if duration_days > 90 else "Single"
		request_date = leave.from_date if getdate(leave.from_date) < getdate(today()) else today()
		destination_country = leave.custom_destination_country or "Egypt"
		destination_city = leave.custom_destination_city or "Cairo"
		departure_airport, arrival_airport = get_demo_airport_pair(0, destination_country, destination_city)
		frappe.db.set_value(
			"Leave Application",
			leave.name,
			{
				"custom_departure_airport": leave.custom_departure_airport or departure_airport,
				"custom_arrival_airport": leave.custom_arrival_airport or arrival_airport,
			},
			update_modified=False,
		)
		if not profile.passport_expiry_date or getdate(profile.passport_expiry_date) <= getdate(leave.to_date):
			frappe.db.set_value("Employee Government Profile", profile.name, "passport_expiry_date", add_days(leave.to_date, 180), update_modified=False)
		if not profile.iqama_expiry_date or getdate(profile.iqama_expiry_date) <= getdate(leave.to_date):
			frappe.db.set_value("Employee Government Profile", profile.name, "iqama_expiry_date", add_days(leave.to_date, 120), update_modified=False)
		profile.reload()
		snapshot = get_employee_snapshot(leave.employee)
		main_request_name = leave.custom_linked_government_request if leave.custom_linked_government_request and frappe.db.exists("Government Request", leave.custom_linked_government_request) else None
		if not main_request_name:
			main_request = frappe.get_doc(
				{
					"doctype": "Government Request",
					"request_type": "Outside KSA Leave Processing",
					"employee": leave.employee,
					"employee_name": leave.employee_name,
					"leave_application": leave.name,
					"employee_government_profile": profile.name,
					"company": leave.company,
					"department": leave.department,
					"request_date": request_date,
					"due_date": leave.from_date,
					"status": "Draft",
					"priority": "Medium",
					"remarks": DEMO_NOTE,
				}
			)
			main_request.insert(ignore_permissions=True)
			main_request.submit()
			main_request_name = main_request.name

		visa_request = frappe.get_doc(
			{
				"doctype": "Government Request",
				"request_type": "Issue Exit Re-entry Visa",
				"employee": leave.employee,
				"employee_name": leave.employee_name,
				"leave_application": leave.name,
				"employee_government_profile": profile.name,
				"company": leave.company,
				"department": leave.department,
				"request_date": request_date,
				"due_date": leave.from_date,
				"status": "Draft",
				"priority": "High",
				"government_platform": "Muqeem",
				"parent_request": main_request_name,
				"remarks": DEMO_NOTE,
			}
		)
		visa_request.insert(ignore_permissions=True)
		visa_request.submit()
		visa_request.db_set("status", "Waiting Payment", update_modified=False)

		employee_visa = frappe.get_doc(
			{
				"doctype": "Employee Visa",
				"employee": leave.employee,
				"employee_name": leave.employee_name,
				"leave_application": leave.name,
				"visa_request": visa_request.name,
				"destination_country": destination_country,
				"destination_city": destination_city,
				"visa_type": "Exit Re-entry",
				"entry_type": entry_type,
				"duration_days": duration_days,
				"issue_date": leave.from_date,
				"expiry_date": leave.to_date,
				"status": "Requested",
				"notes": DEMO_NOTE,
			}
		)
		employee_visa.insert(ignore_permissions=True)
		employee_visa.submit()

		payment_defaults = get_payment_defaults(
			"Exit Re-entry Visa Fee",
			company=leave.company,
			country=destination_country,
			destination_city=destination_city,
			visa_type="Exit Re-entry",
			entry_type=entry_type,
			duration_days=duration_days,
		)
		visa_price = flt(payment_defaults["pricing_rule"].amount) if payment_defaults["pricing_rule"] else 0
		payment_request = frappe.get_doc(
			{
				"doctype": "Government Payment Request",
				"employee": leave.employee,
				"employee_name": leave.employee_name,
				"leave_application": leave.name,
				"government_request": main_request_name,
				"visa_request": visa_request.name,
				"company": leave.company,
				"payment_type": "Exit Re-entry Visa Fee",
				"destination_country": destination_country,
				"destination_city": destination_city,
				"visa_duration_days": duration_days,
				"visa_price": visa_price,
				"employee_qiwa_balance": snapshot.get("qiwa_balance") or 0,
				"account": payment_defaults["account"],
				"payment_account": payment_defaults["payment_account"],
				"cost_center": payment_defaults["cost_center"],
				"status": "Draft",
				"notes": DEMO_NOTE,
			}
		)
		payment_request.insert(ignore_permissions=True)
		payment_request.submit()

		ticket_request = frappe.get_doc(
			{
				"doctype": "Travel Ticket Request",
				"employee": leave.employee,
				"employee_name": leave.employee_name,
				"leave_application": leave.name,
				"government_request": main_request_name,
				"visa_request": visa_request.name,
				"destination_country": destination_country,
				"destination_city": destination_city,
				"departure_date": add_days(leave.from_date, 3),
				"return_date": add_days(leave.to_date, -1),
				"ticket_amount": 990,
				"airline": "Saudi Airlines",
				"booking_reference": f"LEG-{leave.employee[-4:]}",
				"ticket_number": f"LTKT-{leave.employee[-4:]}",
				"account": get_settings().ticket_expense_account,
				"cost_center": get_settings().default_cost_center,
				"status": "Draft",
				"notes": DEMO_NOTE,
			}
		)
		ticket_request.insert(ignore_permissions=True)
		ticket_request.submit()

		frappe.db.set_value(
			"Leave Application",
			leave.name,
			{
				"custom_linked_visa_request": visa_request.name,
				"custom_linked_employee_visa": employee_visa.name,
				"custom_linked_payment_request": payment_request.name,
				"custom_linked_ticket_request": ticket_request.name,
				"custom_linked_government_request": main_request_name,
				"custom_gro_status": "Pending",
				"custom_finance_status": "Pending",
				"custom_clearance_status": "Pending",
				"custom_ticket_status": "Requested",
			},
			update_modified=False,
		)
		frappe.db.set_value(
			"Government Request",
			main_request_name,
			{
				"linked_visa": employee_visa.name,
				"linked_payment_request": payment_request.name,
				"linked_ticket_request": ticket_request.name,
				"linked_clearance": leave.custom_linked_clearance,
			},
			update_modified=False,
		)
