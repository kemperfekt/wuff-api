# src/core/service_container.py
from typing import Dict, Any, Type

class ServiceContainer:
    """Einfacher Service-Container für Dependency Injection"""
    
    def __init__(self):
        self.services = {}
        self.instances = {}
    
    def register(self, interface: Type, implementation: Type):
        """Registriert eine Implementierung für ein Interface"""
        self.services[interface] = implementation
    
    def get(self, interface: Type, *args, **kwargs) -> Any:
        """Holt oder erstellt eine Instanz eines Services"""
        if interface not in self.services:
            raise KeyError(f"Service {interface.__name__} nicht registriert")
        
        # Instanz-Key basierend auf Interface und Args
        key = f"{interface.__name__}_{str(args)}_{str(kwargs)}"
        
        # Existierende Instanz zurückgeben, wenn vorhanden
        if key in self.instances:
            return self.instances[key]
        
        # Neue Instanz erstellen
        implementation = self.services[interface]
        instance = implementation(*args, **kwargs)
        
        # Instanz cachen
        self.instances[key] = instance
        
        return instance

# Container als Singleton verfügbar machen
container = ServiceContainer()