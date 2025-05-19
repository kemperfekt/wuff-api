# test_redis.py
import os
import asyncio
import json
from datetime import datetime

# Stellen sicher, dass wir die Services importieren können
import sys
sys.path.append('.')  # Fügt das aktuelle Verzeichnis zum Pfad hinzu

from src.services.redis_service import RedisService

async def test_redis():
    print("Redis-Verbindungstest für Clever Cloud")
    print("-" * 50)
    
    # Vorhandene Redis-Umgebungsvariablen anzeigen
    redis_vars = [
        "REDIS_DIRECT_URI", "REDIS_DIRECT_URL", "REDIS_URL", 
        "REDIS_CLI_DIRECT_URI", "REDIS_CLI_URL"
    ]
    
    print("Verfügbare Redis-Umgebungsvariablen:")
    for var in redis_vars:
        if os.environ.get(var):
            # URL maskieren, aber Host anzeigen
            value = os.environ.get(var)
            parts = value.split("@")
            if len(parts) > 1:
                auth_part = parts[0].split(":")
                if len(auth_part) > 2:  # Hat ein Passwort
                    masked_url = f"{auth_part[0]}:{auth_part[1]}:***@{parts[1]}"
                else:
                    masked_url = f"{auth_part[0]}:***@{parts[1]}"
                value = masked_url
            print(f"  - {var}: {value}")
    
    print("\nRedis-Service initialisieren...")
    redis = RedisService.get_instance()
    
    if not redis.is_connected():
        print("❌ Keine Verbindung zu Redis!")
        return
    
    # Testdaten speichern
    test_key = f"test:key:{datetime.now().isoformat()}"
    test_value = {
        "name": "Redis Test",
        "timestamp": datetime.now().isoformat(),
        "value": 42,
        "nested": {
            "array": [1, 2, 3],
            "text": "Hallo Welt!"
        }
    }
    
    print(f"\nSpeichere Testdaten unter Schlüssel '{test_key}':")
    print(json.dumps(test_value, indent=2))
    
    success = redis.set(test_key, test_value)
    
    if not success:
        print("❌ Fehler beim Speichern!")
        return
    
    print("\nVersuche Testdaten zu lesen...")
    result = redis.get(test_key)
    
    print("\nGelesene Daten:")
    print(json.dumps(result, indent=2) if result else "Keine Daten gefunden")
    
    if result == test_value:
        print("\n✅ Test erfolgreich! Daten stimmen überein.")
    else:
        print("\n❌ Test fehlgeschlagen: Daten stimmen nicht überein!")
    
    # Testschlüssel löschen
    print(f"\nLösche Testschlüssel '{test_key}'...")
    if redis.delete(test_key):
        print("✅ Schlüssel erfolgreich gelöscht")
    else:
        print("❌ Fehler beim Löschen des Schlüssels")
    
    # Aktuelle Schlüssel anzeigen
    print("\nAlle verfügbaren Schlüssel (Max. 20):")
    all_keys = redis.keys()[:20]
    if all_keys:
        for key in all_keys:
            print(f"  - {key}")
    else:
        print("  (keine Schlüssel gefunden)")
    
    print("\nTest abgeschlossen.")

if __name__ == "__main__":
    asyncio.run(test_redis())