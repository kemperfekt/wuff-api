# src/services/weaviate_service.py

import os
import aiohttp
from typing import Dict, List, Any, Optional

class WeaviateQueryAgentService:
    """Service für die Interaktion mit dem Weaviate Query Agent"""
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialisiert den Service für den Weaviate Query Agent.
        
        Args:
            api_url: Die URL zum Query Agent Endpoint. Falls None, wird WEAVIATE_QUERY_AGENT_URL aus den Umgebungsvariablen verwendet.
            api_key: Der API-Key für den Query Agent. Falls None, wird WEAVIATE_QUERY_AGENT_KEY aus den Umgebungsvariablen verwendet.
        """
        self.api_url = api_url or os.getenv("WEAVIATE_QUERY_AGENT_URL")
        self.api_key = api_key or os.getenv("WEAVIATE_QUERY_AGENT_KEY")
        
        if not self.api_url:
            raise RuntimeError("WEAVIATE_QUERY_AGENT_URL nicht gesetzt")
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def query(self, query: str, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Sendet eine natürlichsprachliche Anfrage an den Weaviate Query Agent
        
        Args:
            query: Die Anfrage in natürlicher Sprache
            collection_name: Optional - Name der Collection, falls die Anfrage auf eine bestimmte Collection beschränkt werden soll
            
        Returns:
            Die Antwort des Query Agents
        """
        payload = {
            "query": query
        }
        
        if collection_name:
            payload["collection"] = collection_name
        
        print(f"🤖 Weaviate Query Agent Anfrage: '{query}'")
        
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
                        raise Exception(f"Fehler bei der Anfrage an den Weaviate Query Agent: {response.status} - {text}")
                    
                    result = await response.json()
                    print(f"✅ Query Agent Antwort erhalten")
                    return result
        except Exception as e:
            print(f"⚠️ Fehler bei der Anfrage an den Weaviate Query Agent: {e}")
            raise


# Singleton-Instanz für einfachen Zugriff
query_agent_service = WeaviateQueryAgentService()