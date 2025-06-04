# tests/v2/services/test_weaviate_service.py
"""
Unit tests for V2 Weaviate Service.

Uses mock-first approach to test without requiring a real Weaviate instance.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from src.services.weaviate_service import (
    WeaviateService, 
    WeaviateConfig, 
    create_weaviate_service
)
from src.core.exceptions import (
    WeaviateServiceError, 
    ConfigurationError, 
    ValidationError
)


@pytest.fixture
def mock_config():
    """Create a test configuration"""
    return WeaviateConfig(
        url="https://test.weaviate.network",
        api_key="test-api-key",
        timeout=30
    )


@pytest.fixture
def mock_weaviate_client():
    """Create a mock Weaviate client"""
    client = Mock()
    client.is_ready.return_value = True
    client.close = Mock()
    
    # Mock collections
    collections = Mock()
    collections.list_all.return_value = {
        "Symptome": {},
        "Instinkte": {},
        "Erziehung": {}
    }
    client.collections = collections
    
    return client


@pytest.fixture
def mock_search_results():
    """Create mock search results"""
    # Create mock objects
    mock_obj1 = Mock()
    mock_obj1.uuid = uuid4()
    mock_obj1.properties = {
        "beschreibung": "Hund bellt häufig",
        "schnelldiagnose": "Aufregung oder Unsicherheit"
    }
    mock_obj1.metadata = Mock(distance=0.15, certainty=0.85)
    
    mock_obj2 = Mock()
    mock_obj2.uuid = uuid4()
    mock_obj2.properties = {
        "beschreibung": "Hund bellt bei Besuch",
        "schnelldiagnose": "Territoriales Verhalten"
    }
    mock_obj2.metadata = Mock(distance=0.25, certainty=0.75)
    
    # Create mock result
    result = Mock()
    result.objects = [mock_obj1, mock_obj2]
    
    return result


@pytest.fixture
async def weaviate_service(mock_config, mock_weaviate_client):
    """Create a Weaviate service with mocked client"""
    service = WeaviateService(mock_config)
    
    # Patch the client initialization
    with patch('src.services.weaviate_service.weaviate.connect_to_weaviate_cloud', 
               return_value=mock_weaviate_client):
        await service.initialize()
    
    return service


class TestWeaviateService:
    """Test Weaviate Service functionality"""
    
    async def test_initialization(self, mock_config):
        """Test service initialization"""
        service = WeaviateService(mock_config)
        
        assert service.config == mock_config
        assert not service.is_initialized
        
        # Mock the client initialization
        with patch('src.services.weaviate_service.weaviate.connect_to_weaviate_cloud') as mock_connect:
            mock_client = Mock()
            mock_client.is_ready.return_value = True
            mock_connect.return_value = mock_client
            
            await service.initialize()
        
        assert service.is_initialized
        mock_connect.assert_called_once()
    
    async def test_initialization_from_env(self):
        """Test initialization from environment variables"""
        with patch.dict('os.environ', {
            'WEAVIATE_URL': 'https://env.weaviate.network',
            'WEAVIATE_API_KEY': 'env-api-key',
            'OPENAI_API_KEY': 'openai-key'
        }):
            service = WeaviateService()
            
            assert service.config.url == 'https://env.weaviate.network'
            assert service.config.api_key == 'env-api-key'
            assert 'X-OpenAI-Api-Key' in service.config.additional_headers
    
    async def test_missing_url(self):
        """Test error when URL is missing"""
        config = WeaviateConfig(url=None, api_key="test-key")
        service = WeaviateService(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            await service.initialize()
        
        assert "Weaviate URL is required" in str(exc_info.value)
    
    async def test_missing_api_key(self):
        """Test error when API key is missing"""
        config = WeaviateConfig(url="https://test.weaviate.network", api_key=None)
        service = WeaviateService(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            await service.initialize()
        
        assert "API key is required" in str(exc_info.value)
    
    async def test_search_success(self, weaviate_service, mock_search_results):
        """Test successful search"""
        # Setup mock collection
        mock_collection = Mock()
        mock_query = Mock()
        mock_query.near_text.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.include_metadata.return_value = mock_query
        mock_query.do.return_value = mock_search_results
        mock_collection.query = mock_query
        
        weaviate_service.client.collections.get.return_value = mock_collection
        
        # Perform search
        results = await weaviate_service.search(
            collection="Symptome",
            query="Hund bellt",
            limit=5,
            return_metadata=True
        )
        
        assert len(results) == 2
        assert "properties" in results[0]
        assert "metadata" in results[0]
        assert results[0]["properties"]["schnelldiagnose"] == "Aufregung oder Unsicherheit"
    
    async def test_search_validation_errors(self, weaviate_service):
        """Test search input validation"""
        # Empty collection
        with pytest.raises(ValidationError) as exc_info:
            await weaviate_service.search("", "query")
        assert "Collection name is required" in str(exc_info.value)
        
        # Empty query
        with pytest.raises(ValidationError) as exc_info:
            await weaviate_service.search("Symptome", "")
        assert "Search query cannot be empty" in str(exc_info.value)
        
        # Invalid limit
        with pytest.raises(ValidationError) as exc_info:
            await weaviate_service.search("Symptome", "query", limit=0)
        assert "Limit must be between" in str(exc_info.value)
    
    async def test_vector_search(self, weaviate_service, mock_search_results):
        """Test vector search"""
        # Setup mock
        mock_collection = Mock()
        mock_query = Mock()
        mock_query.near_vector.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.include_metadata.return_value = mock_query
        mock_query.do.return_value = mock_search_results
        mock_collection.query = mock_query
        
        weaviate_service.client.collections.get.return_value = mock_collection
        
        # Perform vector search
        vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = await weaviate_service.vector_search(
            collection="Symptome",
            vector=vector,
            limit=3
        )
        
        assert len(results) == 2
        mock_query.near_vector.assert_called_once_with(near_vector=vector, limit=3)
    
    async def test_get_by_id(self, weaviate_service):
        """Test getting object by ID"""
        # Setup mock
        mock_collection = Mock()
        mock_result = Mock()
        mock_result.uuid = uuid4()
        mock_result.properties = {"name": "Test"}
        mock_collection.query.fetch_object_by_id.return_value = mock_result
        
        weaviate_service.client.collections.get.return_value = mock_collection
        
        # Get object
        result = await weaviate_service.get_by_id("Symptome", str(mock_result.uuid))
        
        assert result is not None
        assert result["properties"]["name"] == "Test"
    
    async def test_get_by_id_not_found(self, weaviate_service):
        """Test getting non-existent object"""
        # Setup mock
        mock_collection = Mock()
        mock_collection.query.fetch_object_by_id.return_value = None
        
        weaviate_service.client.collections.get.return_value = mock_collection
        
        # Get object
        result = await weaviate_service.get_by_id("Symptome", "non-existent-id")
        
        assert result is None
    
    async def test_get_collections(self, weaviate_service):
        """Test getting list of collections"""
        collections = await weaviate_service.get_collections()
        
        assert len(collections) == 3
        assert "Symptome" in collections
        assert "Instinkte" in collections
        assert "Erziehung" in collections
    
    async def test_collection_exists(self, weaviate_service):
        """Test checking if collection exists"""
        assert await weaviate_service.collection_exists("Symptome") is True
        assert await weaviate_service.collection_exists("NonExistent") is False
    
    async def test_count_objects(self, weaviate_service):
        """Test counting objects in collection"""
        # Setup mock
        mock_collection = Mock()
        mock_aggregate = Mock()
        mock_aggregate_result = Mock(total_count=42)
        mock_aggregate.over_all.return_value = mock_aggregate_result
        mock_collection.aggregate = mock_aggregate
        
        weaviate_service.client.collections.get.return_value = mock_collection
        
        # Count objects
        count = await weaviate_service.count_objects("Symptome")
        
        assert count == 42
    
    async def test_find_symptom_match(self, weaviate_service, mock_search_results):
        """Test finding symptom match (from retrieval.py)"""
        # Setup mock
        mock_collection = Mock()
        mock_query = Mock()
        mock_query.near_text.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.include_metadata.return_value = mock_query
        mock_query.do.return_value = mock_search_results
        mock_collection.query = mock_query
        
        weaviate_service.client.collections.get.return_value = mock_collection
        
        # Find symptom
        result = await weaviate_service.find_symptom_match("Bellen")
        
        assert result == "Aufregung oder Unsicherheit"
    
    async def test_health_check_healthy(self, weaviate_service):
        """Test health check when service is healthy"""
        # Setup mocks for count
        mock_collection = Mock()
        mock_aggregate = Mock()
        mock_aggregate_result = Mock(total_count=10)
        mock_aggregate.over_all.return_value = mock_aggregate_result
        mock_collection.aggregate = mock_aggregate
        
        weaviate_service.client.collections.get.return_value = mock_collection
        
        health = await weaviate_service.health_check()
        
        assert health['healthy'] is True
        assert health['status'] == 'connected'
        assert health['details']['collections_count'] == 3
    
    async def test_health_check_unhealthy(self, weaviate_service):
        """Test health check when service is unhealthy"""
        # Make client not ready
        weaviate_service.client.is_ready.return_value = False
        
        health = await weaviate_service.health_check()
        
        assert health['healthy'] is False
        assert health['status'] == 'connected'  # Still says connected but not ready
    
    async def test_cleanup(self, weaviate_service):
        """Test cleanup closes client"""
        await weaviate_service.shutdown()
        
        weaviate_service.client.close.assert_called_once()
        assert not weaviate_service.is_initialized


class TestWeaviateServiceFactory:
    """Test the factory function"""
    
    async def test_create_weaviate_service(self):
        """Test service creation via factory"""
        with patch('src.services.weaviate_service.weaviate.connect_to_weaviate_cloud') as mock_connect:
            mock_client = Mock()
            mock_client.is_ready.return_value = True
            mock_connect.return_value = mock_client
            
            service = await create_weaviate_service(
                url="https://test.weaviate.network",
                api_key="test-key"
            )
            
            assert isinstance(service, WeaviateService)
            assert service.is_initialized
            assert service.config.url == "https://test.weaviate.network"


# Integration tests (optional, skipped by default)
@pytest.mark.integration
class TestWeaviateServiceIntegration:
    """Integration tests that require a real Weaviate instance"""
    
    @pytest.mark.skipif(
        not os.getenv("RUN_INTEGRATION_TESTS"),
        reason="Integration tests disabled"
    )
    async def test_real_search(self):
        """Test with real Weaviate instance"""
        service = await create_weaviate_service()
        
        # Search for symptoms
        results = await service.search(
            collection="Symptome",
            query="Hund bellt",
            limit=3
        )
        
        assert len(results) > 0
        assert "properties" in results[0]