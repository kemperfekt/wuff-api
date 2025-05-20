# src/services/weaviate_service.py
import os
import weaviate
from weaviate.classes.init import Auth
from weaviate.agents.query import QueryAgent
from typing import Dict, Any, Optional, List

class WeaviateQueryAgentService:
    """Service für die Interaktion mit dem Weaviate Query Agent"""
    
    def __init__(self):
        """Initialisiert den Service für den Weaviate Query Agent."""
        # Weaviate-Zugangsdaten
        self.weaviate_url = os.getenv("WEAVIATE_URL")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_APIKEY")
        
        self._client = None
        self._agent = None
        
        print(f"📌 Weaviate Query Agent Service initialisiert")
        print(f"📌 API-Key gesetzt: {'Ja' if self.weaviate_api_key else 'Nein'}")
        print(f"📌 OpenAI API-Key gesetzt: {'Ja' if self.openai_api_key else 'Nein'}")
    
    def _initialize(self):
        """Initialisiert die Verbindung und den Query Agent (lazy loading)"""
        if self._client is None:
            try:
                # Weaviate-Client erstellen
                self._client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.weaviate_url,
                    auth_credentials=Auth.api_key(self.weaviate_api_key),
                    headers={
                        "X-OpenAI-Api-Key": self.openai_api_key
                    } if self.openai_api_key else {}
                )
                
                # Überprüfen, ob die Verbindung funktioniert
                if not self._client.is_ready():
                    print("⚠️ Weaviate-Client ist nicht bereit!")
                    return False
                
                # Verfügbare Collections abrufen
                collections = list(self._client.collections.list_all().keys())
                print(f"📌 Verfügbare Collections: {', '.join(collections)}")
                
                # Query Agent erstellen
                self._agent = QueryAgent(
                    client=self._client,
                    collections=collections  # Alle verfügbaren Collections verwenden
                )
                
                return True
            except Exception as e:
                print(f"⚠️ Fehler bei der Initialisierung des Query Agents: {e}")
                return False
        return True
    
    async def query(self, query: str, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Führt eine Abfrage mit dem Query Agent durch.
        
        Args:
            query: Die Abfrage in natürlicher Sprache
            collection_name: Optional - Name der Collection, falls die Abfrage auf eine bestimmte Collection beschränkt werden soll
            
        Returns:
            Die Antwort des Query Agents
        """
        if not self._initialize():
            return {"data": {}, "error": "Weaviate Query Agent konnte nicht initialisiert werden"}
        
        try:
            print(f"🤖 Query Agent Anfrage: '{query}'")
            if collection_name:
                print(f"📚 Collection: {collection_name}")
                
                # Temporären Agent mit spezifischer Collection erstellen
                temp_agent = QueryAgent(
                    client=self._client,
                    collections=[collection_name]
                )
                
                # Abfrage mit dem temporären Agent durchführen
                response = temp_agent.run(query)
            else:
                # Abfrage mit dem Standard-Agent durchführen (alle Collections)
                response = self._agent.run(query)
            
            # Antwort extrahieren und strukturieren
            result = {
                "data": response.final_answer,
                "error": None
            }
            
            print(f"✅ Query Agent Antwort erhalten")
            return result
        except Exception as e:
            print(f"⚠️ Fehler bei der Anfrage an den Weaviate Query Agent: {e}")
            return {"data": {}, "error": str(e)}
    
    def close(self):
        """Schließt den Client ordnungsgemäß"""
        if self._client:
            self._client.close()
            self._client = None
            self._agent = None

# Singleton-Instanz für einfachen Zugriff
query_agent_service = WeaviateQueryAgentService()