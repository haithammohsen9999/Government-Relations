from frappe.tests.utils import FrappeTestCase

from ksa_government_relations.utils import get_ticket_travel_dates


class TestUtils(FrappeTestCase):
	def test_ticket_dates_stay_inside_short_leave_window(self):
		departure_date, return_date = get_ticket_travel_dates("2026-07-05", "2026-07-08", 3, 1)

		self.assertEqual(departure_date, "2026-07-05")
		self.assertEqual(return_date, "2026-07-08")

	def test_ticket_dates_keep_configured_offsets_when_valid(self):
		departure_date, return_date = get_ticket_travel_dates("2026-07-05", "2026-07-15", 3, 1)

		self.assertEqual(departure_date, "2026-07-08")
		self.assertEqual(return_date, "2026-07-14")
