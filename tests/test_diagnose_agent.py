import unittest
from src.agents.diagnose_agent import run_diagnose_agent

class DiagnoseAgentTestCase(unittest.TestCase):
    def test_run_diagnose_agent_with_known_symptom(self):
        """
        Testet, ob run_diagnose_agent bei gültigem Symptom eine Liste von Rückfragen liefert.
        """
        symptom_input = "zieht an der Leine"  # Beispiel für ein bekanntes Symptom
        rückfragen = run_diagnose_agent(symptom_input)
        
        self.assertIsInstance(rückfragen, list)
        self.assertGreater(len(rückfragen), 0)  # Es sollten Rückfragen zurückkommen
        self.assertIsInstance(rückfragen[0], str)  # Rückfragen sollten Strings sein

if __name__ == "__main__":
    unittest.main()
  
