# src/services/redis_service.py
import os
import json
import redis
from typing import Optional, Any, List

class RedisService:
    """Service für die Interaktion mit Redis speziell für Clever Cloud"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Singleton-Instanz zurückgeben"""
        if cls._instance is None:
            cls._instance = RedisService()
        return cls._instance
    
    def __init__(self):
        """Redis-Client initialisieren mit Clever Cloud-spezifischen Einstellungen"""
        # Prioritätsreihenfolge für Redis-URLs für Clever Cloud
        # REDIS_DIRECT_URI hat Priorität (für Add-on innerhalb Clever Cloud)
        redis_url = None
        url_source = None
        
        url_env_vars = [
            "REDIS_DIRECT_URI",      # Direkte Verbindung innerhalb Clever Cloud (bevorzugt)
            "REDIS_DIRECT_URL",      # Öffentliche URL über Proxy
            "REDIS_URL",             # Standard
            "REDIS_CLI_DIRECT_URI",  # Alternative für CLI
            "REDIS_CLI_URL"          # Alternative für CLI
        ]
        
        # Erste verfügbare URL verwenden
        for var in url_env_vars:
            if os.environ.get(var):
                redis_url = os.environ.get(var)
                url_source = var
                break
        
        if not redis_url:
            print("⚠️ Keine Redis-URL gefunden - Redis-Funktionalität deaktiviert")
            self.client = None
            return
        
        print(f"🔌 Verbinde zu Redis mit {url_source}: {redis_url[:15]}...{redis_url[-15:] if len(redis_url) > 30 else redis_url[15:]}")
        
        # Redis-Client erstellen
        try:
            # Bei Verbindungsproblemen kann ein längeres Socket-Timeout helfen
            self.client = redis.from_url(redis_url, socket_timeout=5.0)
            
            # Verbindung testen
            self.client.ping()
            print("✅ Redis-Verbindung erfolgreich")
        except Exception as e:
            print(f"❌ Redis-Verbindungsfehler: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Prüft, ob Redis verbunden ist"""
        if self.client is None:
            return False
            
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Speichert einen Wert in Redis.
        
        Args:
            key: Der Schlüssel
            value: Der zu speichernde Wert (wird automatisch als JSON serialisiert, wenn es kein String ist)
            expire: Optional - Zeit in Sekunden, nach der der Schlüssel abläuft
            
        Returns:
            bool: True wenn erfolgreich, sonst False
        """
        if not self.is_connected():
            return False
            
        try:
            # Wert serialisieren, wenn es kein String ist
            if not isinstance(value, str):
                value = json.dumps(value)
            
            # In Redis speichern
            self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            print(f"❌ Redis-Fehler beim Speichern: {e}")
            return False
    
    def get(self, key: str, as_json: bool = True) -> Any:
        """
        Holt einen Wert aus Redis.
        
        Args:
            key: Der Schlüssel
            as_json: Ob der Wert als JSON deserialisiert werden soll
            
        Returns:
            Der gespeicherte Wert oder None, wenn der Schlüssel nicht existiert
        """
        if not self.is_connected():
            return None
            
        try:
            # Wert aus Redis holen
            value = self.client.get(key)
            
            if value is None:
                return None
            
            # Wert dekodieren
            value_str = value.decode('utf-8')
            
            if as_json and value_str:
                try:
                    return json.loads(value_str)
                except json.JSONDecodeError:
                    # Wenn keine gültige JSON-Zeichenfolge, als String zurückgeben
                    return value_str
            else:
                return value_str
        except Exception as e:
            print(f"❌ Redis-Fehler beim Abrufen: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Löscht einen Schlüssel"""
        if not self.is_connected():
            return False
            
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Redis-Fehler beim Löschen: {e}")
            return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Gibt alle Schlüssel zurück, die dem Muster entsprechen"""
        if not self.is_connected():
            return []
            
        try:
            keys = self.client.keys(pattern)
            return [k.decode('utf-8') for k in keys]
        except Exception as e:
            print(f"❌ Redis-Fehler bei der Schlüsselsuche: {e}")
            return []