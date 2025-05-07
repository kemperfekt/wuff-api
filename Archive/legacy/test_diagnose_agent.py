# tests/test_diagnose_agent.py

import os
import unittest
from unittest.mock import patch

from src.agents.diagnose_agent import run_diagnose_agent
from src.models.instinct_models import InstinctClassification
from src.services.diagnose_service import FinalDiagnosisResponse
from src.services.state import State

class DiagnoseAgentTestCase(unittest.TestCase):

    def setUp(self):
        os.environ["OPENAI_APIKEY"] = "testkey"

    def tearDown(self):
        del os.environ["OPENAI_APIKEY"]

    @patch("src.services.state.load_state")
    @patch("src.services.state.save_state")
    @patch("src.agents.diagnose_agent.classify_instincts")
    @patch("src.agents.diagnose_agent.get_symptom_info")
    @patch("src.agents.diagnose_agent.get_final_diagnosis")
    def test_run_diagnose_agent_with_known_symptom(
        self, mock_final, mock_get_symptom_info, mock_classify,
        mock_save_state, mock_load_state
    ):
        # State stub
        state = State()
        mock_load_state.return_value = state

        # 1) Instinkte erkannt, keine Rückfragen
        classification = InstinctClassification(
            known_instincts=["inst1"],
            uncertain_instincts=[]
        )
        mock_classify.return_value = classification

        # 2) Symptom-Info stub
        mock_get_symptom_info.return_value = type("SI", (), {
            "dict": lambda self: {"symptom_name": "inst1", "instinktvarianten": []}
        })()

        # 3) Final-Diagnose stub
        final = FinalDiagnosisResponse(message="Diagnose", details={"test": True})
        mock_final.return_value = final

        # **Hier** muss _beide_ Argumente übergeben werden:
        result = run_diagnose_agent("sess123", "Symptom Beschreibung")

        self.assertIn("message", result)
        self.assertEqual(result["message"], "Diagnose")
        self.assertEqual(result["details"], {"test": True})
