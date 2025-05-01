# tests/test_contract_pact.py

import atexit
import requests
from pact import Consumer, Provider

PACT_MOCK_HOST = "localhost"
PACT_MOCK_PORT = 1234

# Consumer-Provider-Definition
pact = Consumer("DogBotFrontend").has_pact_with(
    Provider("DogBotBackend"),
    host_name=PACT_MOCK_HOST,
    port=PACT_MOCK_PORT,
)

# Damit der Mock-Server sauber beendet wird
atexit.register(lambda: pact.stop_service())

def test_contract_diagnose_continue():
    # Erwartete Interaction
    pact.given("Der Diagnose-Service ist verfügbar") \
        .upon_receiving("Diagnose-Continue Request") \
        .with_request(
            method="POST",
            path="/diagnose_continue",
            headers={"Content-Type": "application/json"},
            body={"session_id": "123", "user_input": "Test"}
        ) \
        .will_respond_with(
            status=200,
            headers={"Content-Type": "application/json"},
            body={"message": "irgendeine Nachricht", "details": {}}
        )

    with pact:
        # Hier wird gegen den Pact-Mock-Server getestet
        response = requests.post(
            f"http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}/diagnose_continue",
            json={"session_id": "123", "user_input": "Test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "details" in data
