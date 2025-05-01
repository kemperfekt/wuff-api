# tests/test_contract_pact.py
import pytest
import requests
from pact import Consumer, Provider

# Pact mock server configuration
PACT_MOCK_HOST = "localhost"
PACT_MOCK_PORT = 1234

pact = Consumer("DogBotFrontend").has_pact_with(
    Provider("DogBotBackend"),
    host_name=PACT_MOCK_HOST,
    port=PACT_MOCK_PORT,
)

# No atexit cleanup to avoid NoneType terminate error

def test_contract_diagnose_continue():
    """
    Contract-Test für /diagnose_continue.
    Wird übersprungen, falls kein Pact-Mock-Server läuft.
    """
    pact.given("Der Diagnose-Service ist verfügbar") \
        .upon_receiving("Diagnose-Continue Request") \
        .with_request(
            method="POST",
            path="/diagnose_continue",
            headers={"Content-Type": "application/json"},
            body={"session_id": "123", "user_input": "Test"},
        ) \
        .will_respond_with(
            status=200,
            headers={"Content-Type": "application/json"},
            body={"message": "irgendeine Nachricht", "details": {}},
        )

    try:
        with pact:
            resp = requests.post(
                f"http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}/diagnose_continue",
                json={"session_id": "123", "user_input": "Test"},
            )
            assert resp.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("Pact mock server not running, skipping contract test")
