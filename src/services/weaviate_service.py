# src/services/weaviate_service.py
# Angepasste Version, die deine bestehenden Weaviate-Zugangsdaten nutzt

import os
import aiohttp
from typing import Dict, List, Any, Optional

class WeaviateQueryAgentService:
    """Service für die Interaktion mit dem Weaviate Query Agent"""
    
    def __init__(self):
        """
        Initialisiert den Service für den Weaviate Query Agent.
        Verwendet die bestehenden Weaviate-Zugangsdaten.
        """
        # Bestehende Weaviate-Zugangsdaten verwenden
        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        
        if not weaviate_url:
            print("⚠️ WEAVIATE_URL nicht gesetzt!")
            weaviate_url = "https://your-default-instance.weaviate.cloud"
            
        # Pfad zum Query Agent hinzufügen (falls nicht bereits enthalten)
        if "/v1/query-agent" not in weaviate_url:
            # Entferne etwaigen Trailing Slash
            if weaviate_url.endswith("/"):
                weaviate_url = weaviate_url[:-1]
            # Füge den Pfad zum Query Agent hinzu
            self.api_url = f"{weaviate_url}/v1/query-agent"
        else:
            self.api_url = weaviate_url
            
        self.api_key = weaviate_api_key
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            
        # OpenAI API Key als Header (falls konfiguriert)
        openai_api_key = os.getenv("OPENAI_APIKEY")
        if openai_api_key:
            self.headers["X-Openai-Api-Key"] = openai_api_key
        
        print(f"📌 Weaviate Query Agent URL: {self.api_url}")
        print(f"📌 API-Key gesetzt: {'Ja' if self.api_key else 'Nein'}")
        print(f"📌 OpenAI API-Key gesetzt: {'Ja' if openai_api_key else 'Nein'}")
    
    async def query(self, query: str, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Sendet eine natürlichsprachliche Anfrage an den Weaviate Query Agent
        
        Args:
            query: Die Anfrage in natürlicher Sprache
            collection_name: Optional - Name der Collection, falls die Anfrage auf eine bestimmte Collection beschränkt werden soll
            
        Returns:
            Die Antwort des Query Agents
        """
        if not self.api_url or "your-default-instance" in self.api_url:
            print("⚠️ Weaviate Query Agent URL nicht korrekt konfiguriert!")
            return {"data": {}, "error": "Weaviate Query Agent URL nicht konfiguriert"}
        
        payload = {
            "query": query
        }
        
        if collection_name:
            payload["collection"] = collection_name
        
        print(f"🤖 Weaviate Query Agent Anfrage: '{query}'")
        if collection_name:
            print(f"📚 Collection: {collection_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, 
                    headers=self.headers,
                    json=payload,
                    timeout=30  # 30 Sekunden Timeout
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        print(f"⚠️ Fehler bei der Anfrage an den Weaviate Query Agent: {response.status} - {text}")
                        return {"data": {}, "error": f"HTTP-Fehler {response.status}: {text}"}
                    
                    result = await response.json()
                    print(f"✅ Query Agent Antwort erhalten")
                    return result
        except Exception as e:
            print(f"⚠️ Fehler bei der Anfrage an den Weaviate Query Agent: {e}")
            return {"data": {}, "error": str(e)}


# Singleton-Instanz für einfachen Zugriff
query_agent_service = WeaviateQueryAgentService()