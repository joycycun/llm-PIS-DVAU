import unittest
from unittest.mock import patch

from services.broadcast_service import plan_start_broadcast, plan_stop_broadcast


class BroadcastBusinessRulesTest(unittest.TestCase):
    def setUp(self):
        self.device = {"type": "DACU", "status": "active"}

    def test_missing_device_id(self):
        self.assertEqual(
            plan_start_broadcast(None, "manual", "microphone").code,
            "missing_device_id",
        )

    @patch("services.broadcast_service.get_device_status", return_value=None)
    def test_unknown_device(self, _lookup):
        self.assertEqual(
            plan_start_broadcast("DACU999", "manual", "microphone").code,
            "device_not_found",
        )

    @patch("services.broadcast_service.get_device_status")
    def test_audio_source_required(self, lookup):
        lookup.return_value = self.device
        self.assertEqual(
            plan_start_broadcast("DACU001", "manual", None).code,
            "missing_audio_source",
        )

    @patch("services.broadcast_service.get_device_status")
    def test_valid_request_is_not_executed(self, lookup):
        lookup.return_value = self.device
        decision = plan_start_broadcast("DACU001", "manual", "microphone")
        self.assertEqual(decision.code, "awaiting_sip_setup")

    @patch("services.broadcast_service.get_device_status")
    def test_stop_has_no_active_session(self, lookup):
        lookup.return_value = self.device
        self.assertEqual(plan_stop_broadcast("DACU001").code, "no_active_session")


if __name__ == "__main__":
    unittest.main()
