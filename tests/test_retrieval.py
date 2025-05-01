import pytest
import src.services.retrieval as retrieval
from src.models.instinct_models import InstinktVeranlagung

def test_get_instinkt_profile(monkeypatch):
    # Stub für die Backend-Funktion
    class DummyProfile:
        def __init__(self):
            self.gruppen_code = "X"
            self.gruppe = "Grp"
            self.untergruppe = "U"
            self.funktion = "F"
            self.merkmale = "M"
            self.anforderungen = "A"
            self.instinkte = {"jagd": 5}

    monkeypatch.setattr(retrieval, "get_instinkt_profile", lambda code: DummyProfile())

    profile = retrieval.get_instinkt_profile("X")
    assert isinstance(profile, DummyProfile)
    assert profile.gruppe == "Grp"
