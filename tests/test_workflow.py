import unittest
from urllib.parse import urlencode
from uuid import uuid4

from app import database
from app.main import app
from app.assessment_schema import AIAssessment, CATEGORIES, PRIORITIES
from app.mock_assessment import assess_ticket


class MockAssessmentTests(unittest.TestCase):
    def test_categories_priorities_and_determinism(self):
        examples = (
            ("VPN outage for all users", "Network", "Critical"),
            ("Broken printer", "Hardware", "Medium"),
            ("Install software", "Software", "Medium"),
            ("Password locked out", "Account Access", "Medium"),
            ("Suspicious phishing email", "Security", "High"),
            ("How to request help", "Other", "Low"),
        )
        for title, category, priority in examples:
            with self.subTest(title=title):
                result = assess_ticket(title, "Please help")
                self.assertIsInstance(result, AIAssessment)
                self.assertEqual(result, assess_ticket(title, "Please help"))
                self.assertEqual(result.category, category)
                self.assertEqual(result.priority, priority)
                self.assertTrue(result.requires_human_review)
                self.assertTrue(result.recommended_team)

    def test_precedence_and_summary(self):
        result = assess_ticket("RANSOMWARE on laptop with VPN", "word\n" * 100)
        self.assertEqual(result.category, "Security")
        self.assertEqual(result.priority, "High")
        self.assertLessEqual(len(result.summary), 240)
        self.assertNotIn("\n", result.summary)
        self.assertEqual(assess_ticket("Help", "Please advise").priority, "Medium")

    def test_client_meeting_example_is_network_high(self):
        sentence = "My laptop keeps losing Wi-Fi and I have a client meeting in 20 minutes"
        for title, description in (
            (sentence, ""),
            ("Wi-Fi problem", sentence),
            ("My laptop keeps losing Wi-Fi", "I have a client meeting in 20 minutes"),
            ("MY LAPTOP KEEPS LOSING WI-FI", "Client meeting in 20\nminutes"),
        ):
            with self.subTest(title=title, description=description):
                result = assess_ticket(title, description)
                self.assertEqual((result.category, result.priority), ("Network", "High"))
                self.assertEqual(result, assess_ticket(title, description))

    def test_priorities_follow_business_impact(self):
        examples = (
            ("Software request", "Planned software request for later.", "Low"),
            ("Install software", "Please install it next month; no rush.", "Low"),
            ("Client software request", "Planned for next week, not urgent.", "Low"),
            ("Minor cosmetic issue", "One icon has the wrong color.", "Low"),
            ("Wi-Fi drops on my laptop", "Only I am affected; I can continue working.", "Medium"),
            ("Cannot print", "One user is affected and can use another printer.", "Medium"),
            ("Local internet outage", "Only my laptop is offline; I can use another device.", "Medium"),
            ("Software request for all users", "Please install it next month.", "Low"),
            ("Password locked out", "I cannot work until access is restored.", "High"),
            ("Software crash", "I cannot complete the customer report.", "High"),
            ("Wi-Fi problem", "Client presentation in 2 hours.", "High"),
            ("Printer problem", "Customer report due today.", "High"),
            ("Suspicious email", "One user received a phishing link.", "High"),
            ("Ransomware on one laptop", "The device has been isolated.", "High"),
            ("VPN outage", "All users cannot connect.", "Critical"),
            ("Widespread outage", "Several offices are affected.", "Critical"),
            ("Major business-wide interruption", "Operations have stopped.", "Critical"),
            ("Ransomware incident", "Multiple services are unavailable.", "Critical"),
        )
        for title, description, expected in examples:
            with self.subTest(title=title):
                self.assertEqual(assess_ticket(title, description).priority, expected)

    def test_higher_impact_overrides_low_priority_signals(self):
        examples = (
            ("Planned software request for later", "I cannot work without it.", "High"),
            ("Minor Wi-Fi issue", "Client meeting in 20 minutes.", "High"),
            ("Suspicious email", "No rush; please review next week.", "High"),
            ("Planned network maintenance", "Now all users cannot connect; outage.", "Critical"),
        )
        for title, description, expected in examples:
            with self.subTest(title=title):
                self.assertEqual(assess_ticket(title, description).priority, expected)


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original_path = database.DATABASE_PATH
        self.test_path = self.original_path.parent / f"test-tickets-{uuid4().hex}.db"
        database.DATABASE_PATH = self.test_path
        self.lifespan = app.router.lifespan_context(app)
        await self.lifespan.__aenter__()
        self.ticket_id = database.create_ticket("VPN outage", "All users cannot connect.")
        self.path = f"/tickets/{self.ticket_id}"

    async def asyncTearDown(self):
        try:
            await self.lifespan.__aexit__(None, None, None)
        finally:
            database.DATABASE_PATH = self.original_path
            self.test_path.unlink(missing_ok=True)

    async def request(self, method, path, fields=None):
        """Send an HTML form request through FastAPI without a test dependency."""
        messages = []
        body = urlencode(fields or {}).encode()
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": method, "scheme": "http", "path": path,
            "raw_path": path.encode(), "query_string": b"", "root_path": "",
            "headers": [(b"host", b"localhost"),
                        (b"content-type", b"application/x-www-form-urlencoded")],
            "server": ("localhost", 8000), "client": ("127.0.0.1", 12345),
        }

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        await app(scope, receive, send)
        status = next(m["status"] for m in messages if m["type"] == "http.response.start")
        html = b"".join(m.get("body", b"") for m in messages).decode()
        return status, html

    async def analyze(self):
        status, _ = await self.request("POST", self.path + "/analyze")
        self.assertEqual(status, 303)
        return dict(database.get_assessment(self.ticket_id))

    async def test_approve_copies_original_and_shows_both_records(self):
        status, html = await self.request("GET", self.path)
        self.assertEqual(status, 200)
        self.assertIn("Analyze ticket", html)
        original = await self.analyze()
        status, html = await self.request("GET", self.path)
        self.assertIn("Approve unchanged", html)
        self.assertIn("Network Support", html)
        # Browser-supplied edits must not change an unchanged approval.
        status, _ = await self.request("POST", self.path + "/review", {
            "action": "approve", "category": "Other", "priority": "Low", "team": "Wrong team",
        })
        self.assertEqual(status, 303)
        review = database.get_review(original["id"])
        self.assertEqual(review["decision"], "approved")
        self.assertEqual(review["category"], original["category"])
        self.assertEqual(review["priority"], original["priority"])
        self.assertEqual(review["team"], original["recommended_team"])
        self.assertEqual(dict(database.get_assessment(self.ticket_id)), original)
        status, html = await self.request("GET", self.path)
        self.assertEqual(status, 200)
        self.assertIn("AI recommendation (mock)", html)
        self.assertIn("Final human decision", html)
        self.assertIn("Approved unchanged", html)
        self.assertNotIn("Save final decision", html)

    async def test_modify_preserves_original_and_survives_restart(self):
        original = await self.analyze()
        team = "Desk'); DROP TABLE tickets; -- <script>alert(1)</script>"
        status, _ = await self.request("POST", self.path + "/review", {
            "action": "modify", "category": "Hardware", "priority": "Low", "team": " " + team + " ",
        })
        self.assertEqual(status, 303)
        review = dict(database.get_review(original["id"]))
        self.assertEqual((review["decision"], review["category"], review["priority"], review["team"]),
                         ("modified", "Hardware", "Low", team))
        await self.lifespan.__aexit__(None, None, None)
        self.lifespan = app.router.lifespan_context(app)
        await self.lifespan.__aenter__()
        self.assertIsNotNone(database.get_ticket(self.ticket_id))
        self.assertEqual(dict(database.get_assessment(self.ticket_id)), original)
        self.assertEqual(dict(database.get_review(original["id"])), review)
        status, html = await self.request("GET", self.path)
        self.assertEqual(status, 200)
        for value in ("Network Support", "Hardware", "Low", "Modified by analyst", "&lt;script&gt;"):
            self.assertIn(value, html)
        self.assertNotIn("<script>", html)

    async def test_repeated_actions_keep_first_records(self):
        original = await self.analyze()
        database.save_assessment(self.ticket_id, assess_ticket("Broken printer", "Please help"))
        self.assertEqual(await self.analyze(), original)
        await self.request("POST", self.path + "/review", {"action": "approve"})
        review = dict(database.get_review(original["id"]))
        # Exercise the database constraint as well as the route's duplicate check.
        database.save_review(original["id"], "modified", "Other", "Low", "Another team")
        status, _ = await self.request("POST", self.path + "/review", {
            "action": "modify", "category": "Other", "priority": "Low", "team": "Another team",
        })
        self.assertEqual(status, 303)
        self.assertEqual(await self.analyze(), original)
        self.assertEqual(dict(database.get_review(original["id"])), review)

    async def test_review_validation_and_missing_tickets(self):
        status, html = await self.request("POST", self.path + "/review", {"action": "approve"})
        self.assertEqual(status, 400)
        self.assertIn("Analyze this ticket before reviewing it.", html)
        for method, suffix in (("GET", ""), ("POST", "/analyze"), ("POST", "/review")):
            status, _ = await self.request(method, "/tickets/99999" + suffix)
            self.assertEqual(status, 404)
        original = await self.analyze()
        invalid_forms = (
            {}, {"action": "unknown"}, {"action": "modify"},
            {"action": "modify", "category": "Invalid", "priority": "High", "team": "Desk"},
            {"action": "modify", "category": "Other", "priority": "Invalid", "team": "Desk"},
            {"action": "modify", "category": "Other", "priority": "Low", "team": " \t\n"},
        )
        for fields in invalid_forms:
            status, html = await self.request("POST", self.path + "/review", fields)
            self.assertEqual(status, 400, fields)
            self.assertIsNone(database.get_review(original["id"]))
            if fields.get("team") == "Desk":
                self.assertIn('value="Desk"', html)
        self.assertEqual(dict(database.get_assessment(self.ticket_id)), original)

    async def test_all_allowed_choices_and_unchanged_edit(self):
        for index, category in enumerate(CATEGORIES):
            ticket_id = database.create_ticket("Test", "Test description")
            path = f"/tickets/{ticket_id}"
            await self.request("POST", path + "/analyze")
            status, _ = await self.request("POST", path + "/review", {
                "action": "modify", "category": category,
                "priority": PRIORITIES[index % len(PRIORITIES)], "team": "Chosen team",
            })
            self.assertEqual(status, 303)
        original = await self.analyze()
        await self.request("POST", self.path + "/review", {
            "action": "modify", "category": original["category"],
            "priority": original["priority"], "team": original["recommended_team"],
        })
        self.assertEqual(database.get_review(original["id"])["decision"], "approved")


if __name__ == "__main__":
    unittest.main()
