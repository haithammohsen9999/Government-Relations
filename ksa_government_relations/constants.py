ROLE_GRO_MANAGER = "Government Relations Manager"
ROLE_GRO_OFFICER = "Government Relations Officer"
ROLE_FINANCE = "Finance Clearance Officer"
ROLE_ASSET = "Asset Clearance Officer"
ROLE_VIEWER = "HR Government Viewer"
ROLE_SELF_SERVICE = "Employee Self Service Government"

APP_ROLES = [
	ROLE_GRO_MANAGER,
	ROLE_GRO_OFFICER,
	ROLE_FINANCE,
	ROLE_ASSET,
	ROLE_VIEWER,
	ROLE_SELF_SERVICE,
]

WORKFLOW_STATES = [
	("Draft", "Inverse"),
	("Submitted", "Primary"),
	("Under Review", "Primary"),
	("Government Processing", "Primary"),
	("Waiting Payment", "Warning"),
	("Paid", "Success"),
	("Issued", "Success"),
	("Completed", "Success"),
	("Rejected", "Danger"),
	("Cancelled", "Danger"),
	("On Hold", "Warning"),
	("Requested", "Primary"),
	("Waiting Approval", "Warning"),
	("Booked", "Primary"),
	("Posted to GL", "Success"),
	("Pending Finance Clearance", "Warning"),
	("Pending Asset Clearance", "Warning"),
	("Pending HR Clearance", "Warning"),
	("Pending Government Clearance", "Warning"),
	("Cleared", "Success"),
	("Sent to Qiwa", "Primary"),
	("Approved", "Success"),
]

WORKFLOW_ACTIONS = [
	"Submit",
	"Review",
	"Process",
	"Request Payment",
	"Mark Paid",
	"Issue",
	"Complete",
	"Reject",
	"Cancel",
	"Hold",
	"Resume",
	"Approve",
	"Book",
	"Post to GL",
]

ACTIVE_VISA_STATUSES = ("Requested", "Waiting Payment", "Paid", "Issued", "Active")
FINAL_REQUEST_STATUSES = ("Completed", "Rejected", "Cancelled")
LATE_RETURN_STATUSES = (
	"Late Return Stage 1",
	"Late Return Stage 2",
	"Late Return Stage 3",
)

PAYMENT_ACCOUNT_FIELD_MAP = {
	"Exit Re-entry Visa Fee": "visa_expense_account",
	"Ticket Fee": "ticket_expense_account",
	"Sponsorship Transfer Fee": "sponsorship_transfer_expense_account",
	"Iqama Fee": "government_fees_payable_account",
	"Work Permit Fee": "government_fees_payable_account",
	"Other": "government_fees_payable_account",
}

SAUDI_AIRPORTS = [
	("AHB", "Abha International Airport", "Abha"),
	("AJF", "Al Jouf Airport", "Sakaka"),
	("AQI", "Qaisumah International Airport", "Qaisumah"),
	("BHH", "Bisha Domestic Airport", "Bisha"),
	("DMM", "King Fahd International Airport", "Dammam"),
	("DWD", "Dawadmi Domestic Airport", "Dawadmi"),
	("EAM", "Najran Domestic Airport", "Najran"),
	("EJH", "Al Wajh Domestic Airport", "Al Wajh"),
	("ELQ", "Prince Naif bin Abdulaziz International Airport", "Qassim"),
	("GIZ", "King Abdullah bin Abdulaziz Airport", "Jizan"),
	("HAS", "Hail International Airport", "Hail"),
	("JED", "King Abdulaziz International Airport", "Jeddah"),
	("MED", "Prince Mohammad bin Abdulaziz International Airport", "Madinah"),
	("NUM", "Neom Bay Airport", "Neom"),
	("RAE", "Arar Domestic Airport", "Arar"),
	("RAH", "Rafha Domestic Airport", "Rafha"),
	("RUH", "King Khalid International Airport", "Riyadh"),
	("SHW", "Sharurah Domestic Airport", "Sharurah"),
	("TIF", "Taif International Airport", "Taif"),
	("TUU", "Tabuk Regional Airport", "Tabuk"),
	("ULH", "Prince Abdul Majeed bin Abdulaziz International Airport", "Al Ula"),
	("URY", "Gurayat Domestic Airport", "Gurayat"),
	("WAE", "Wadi Al Dawasir Airport", "Wadi Al Dawasir"),
	("YNB", "Prince Abdul Mohsin bin Abdulaziz International Airport", "Yanbu"),
]
