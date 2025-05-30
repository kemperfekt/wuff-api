# src/v2/services/weaviate_service.py
"""
Weaviate Service for WuffChat V2.

Clean, async-only wrapper around Weaviate vector database with:
- Direct vector search (no Query Agent)
- Generic interface
- No built-in caching
- Proper error handling
- Health checks
"""
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
import weaviate
from weaviate.client import WeaviateClient
from weaviate.classes.init import Auth, AdditionalConfig, Timeout
from weaviate.classes.query import MetadataQuery

from src.core.service_base import BaseService, ServiceConfig
from src.core.exceptions import (
    V2ServiceError,
    ConfigurationError,
    ValidationError
)

logger = logging.getLogger(__name__)


@dataclass
class WeaviateConfig(ServiceConfig):
    """Configuration for Weaviate Service"""
    url: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 30
    additional_headers: Optional[Dict[str, str]] = None


class WeaviateService(BaseService[WeaviateConfig]):
    """
    Async-only Weaviate service for vector operations.
    
    Provides a clean interface for vector searches without the complexity
    of Query Agent, allowing full control over search behavior.
    """
    
    def __init__(self, config: Optional[WeaviateConfig] = None):
        """
        Initialize Weaviate Service.
        
        Args:
            config: Weaviate configuration. If not provided, uses environment variables.
        """
        # Use provided config or create from environment
        if config is None:
            config = WeaviateConfig(
                url=os.getenv("WEAVIATE_URL"),
                api_key=os.getenv("WEAVIATE_API_KEY"),
                additional_headers={
                    "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY", "")
                } if os.getenv("OPENAI_API_KEY") else {}
            )
        
        super().__init__(config, logger)
        self._collections_cache: Optional[List[str]] = None
    
    def _validate_config(self) -> None:
        """Validate Weaviate configuration"""
        super()._validate_config()
        
        if not self.config.url:
            raise ConfigurationError(
                "url",
                "Weaviate URL is required. Set WEAVIATE_URL environment variable."
            )
        
        if not self.config.api_key:
            raise ConfigurationError(
                "api_key",
                "Weaviate API key is required. Set WEAVIATE_API_KEY environment variable."
            )
    
    async def _initialize_client(self) -> WeaviateClient:
        """Initialize the Weaviate client"""
        try:
            # Note: weaviate-client is not async, so we use sync client
            # but wrap our methods to be async for consistency
            self.logger.debug("Starting Weaviate client initialization")
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.config.url,
                auth_credentials=Auth.api_key(self.config.api_key),
                headers=self.config.additional_headers,
                additional_config=AdditionalConfig(
                    timeout=Timeout(
                        init=self.config.timeout,
                        query=self.config.timeout,
                        insert=self.config.timeout * 2
                    )
                )
            )
            
            # Verify connection
            if not client.is_ready():
                raise V2ServiceError(
                    "Weaviate",
                    "Weaviate client is not ready after initialization",
                    "initialize",
                    {"url": self.config.url}
                )
            
            self.logger.info("Weaviate client initialized successfully")
            return client
            
        except Exception as e:
            error_msg = f"Failed to initialize Weaviate client: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            raise V2ServiceError(
                "Weaviate",
                error_msg,
                "initialize",
                {"url": self.config.url, "error": str(e)}
            )
    
    async def search(
        self,
        collection: str,
        query: str,
        limit: int = 5,
        properties: Optional[List[str]] = None,
        where_filter: Optional[Dict[str, Any]] = None,
        return_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for objects in a collection using text similarity.
        
        Args:
            collection: Name of the collection to search
            query: Search query text
            limit: Maximum number of results
            properties: Specific properties to return (None = all)
            where_filter: Optional filter conditions
            return_metadata: Include distance and other metadata
            
        Returns:
            List of matching objects
            
        Raises:
            WeaviateServiceError: If search fails
            ValidationError: If inputs are invalid
        """
        await self.ensure_initialized()
        
        # Validate inputs
        if not collection:
            raise ValidationError(
                "collection",
                "Collection name is required"
            )
        
        if not query or not query.strip():
            raise ValidationError(
                "query",
                "Search query cannot be empty"
            )
        
        if limit < 1 or limit > 100:
            raise ValidationError(
                "limit",
                "Limit must be between 1 and 100"
            )
        
        try:
            self.logger.debug(f"Searching {collection} for: {query[:50]}...")
            
            # Get collection
            collection_obj = self.client.collections.get(collection)
            
            # Build query parameters
            query_params = {
                "query": query,
                "limit": limit
            }

            # Add properties if specified
            if properties:
                query_params["return_properties"] = properties

            # Add metadata if requested
            if return_metadata:
                query_params["return_metadata"] = MetadataQuery(distance=True)

            # Add where filter if provided
            if where_filter:
                query_params["where"] = where_filter

            # Execute query - no chaining!
            results = collection_obj.query.near_text(**query_params)

            # Process results
            items = []
            for item in results.objects:
                item_dict = {
                    "id": str(item.uuid),
                    "properties": item.properties
                }
                
                if return_metadata and hasattr(item, 'metadata'):
                    item_dict["metadata"] = {
                        "distance": item.metadata.distance if hasattr(item.metadata, 'distance') else None
                    }
                
                items.append(item_dict)
            
            self.logger.debug(f"Found {len(items)} results")
            return items
            
        except Exception as e:
            error_msg = f"Search failed in collection '{collection}': {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            raise V2ServiceError(
                "Weaviate",
                error_msg,
                "search",
                {"collection": collection, "query": query}
            )
    
    async def vector_search(
        self,
        collection: str,
        vector: List[float],
        limit: int = 5,
        properties: Optional[List[str]] = None,
        return_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for objects using a vector.
        
        Args:
            collection: Name of the collection to search
            vector: Query vector
            limit: Maximum number of results
            properties: Specific properties to return
            return_metadata: Include distance metadata
            
        Returns:
            List of matching objects
        """
        await self.ensure_initialized()
        
        if not collection:
            raise ValidationError(
                "collection",
                "Collection name is required"
            )
        
        if not vector or not isinstance(vector, list):
            raise ValidationError(
                "vector",
                "Valid vector is required"
            )
        
        try:
            collection_obj = self.client.collections.get(collection)
            
            # Build query
            query_builder = collection_obj.query.near_vector(
                near_vector=vector,
                limit=limit
            )
            
            if properties:
                query_builder = query_builder.select(properties)
            
            if return_metadata:
                query_builder = query_builder.include_metadata(MetadataQuery.full())
            
            # Execute query
            results = query_builder.do()
            
            # Convert to list of dicts
            items = []
            for item in results.objects:
                item_dict = {
                    "id": str(item.uuid),
                    "properties": item.properties
                }
                
                if return_metadata and hasattr(item, 'metadata'):
                    item_dict["metadata"] = {
                        "distance": getattr(item.metadata, 'distance', None),
                        "certainty": getattr(item.metadata, 'certainty', None)
                    }
                
                items.append(item_dict)
            
            return items
            
        except Exception as e:
            error_msg = f"Vector search failed in collection '{collection}': {str(e)}"
            raise V2ServiceError(
                "Weaviate",
                error_msg,
                "vector_search",
                {"collection": collection}
            )
    
    async def get_by_id(
        self,
        collection: str,
        object_id: str,
        properties: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific object by ID.
        
        Args:
            collection: Collection name
            object_id: Object UUID
            properties: Specific properties to return
            
        Returns:
            Object data or None if not found
        """
        await self.ensure_initialized()
        
        try:
            collection_obj = self.client.collections.get(collection)
            
            # Get object
            result = collection_obj.query.fetch_object_by_id(
                uuid=object_id,
                select=properties
            )
            
            if result:
                return {
                    "id": str(result.uuid),
                    "properties": result.properties
                }
            
            return None
            
        except Exception as e:
            # Log but don't raise for not found
            self.logger.debug(f"Object not found or error: {e}")
            return None
    
    async def get_collections(self) -> List[str]:
        """
        Get list of all collections.
        
        Returns:
            List of collection names
        """
        await self.ensure_initialized()
        
        try:
            # Use cached value if available
            if self._collections_cache is not None:
                return self._collections_cache
            
            # Get all collections
            collections = list(self.client.collections.list_all().keys())
            
            # Cache the result
            self._collections_cache = collections
            
            return collections
            
        except Exception as e:
            error_msg = f"Failed to list collections: {str(e)}"
            raise V2ServiceError(
                "Weaviate",
                error_msg,
                "get_collections"
            )
    
    async def collection_exists(self, collection: str) -> bool:
        """
        Check if a collection exists.
        
        Args:
            collection: Collection name
            
        Returns:
            True if collection exists
        """
        collections = await self.get_collections()
        return collection in collections
    
    async def count_objects(self, collection: str) -> int:
        """
        Count objects in a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Number of objects
        """
        await self.ensure_initialized()
        
        try:
            collection_obj = self.client.collections.get(collection)
            aggregate_result = collection_obj.aggregate.over_all(total_count=True)
            return aggregate_result.total_count or 0
            
        except Exception as e:
            self.logger.warning(f"Failed to count objects: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Weaviate service health.
        
        Returns:
            Health status including connection and collection info
        """
        try:
            await self.ensure_initialized()
            
            # Check if client is ready
            is_ready = self.client.is_ready()
            
            # Get collections
            collections = await self.get_collections()
            
            # Count objects in each collection
            collection_counts = {}
            for collection in collections[:5]:  # Limit to first 5 for performance
                count = await self.count_objects(collection)
                collection_counts[collection] = count
            
            return {
                "healthy": is_ready,
                "status": "connected" if is_ready else "not ready",
                "details": {
                    "url": self.config.url,
                    "collections_count": len(collections),
                    "collections": collections[:5],  # First 5 collections
                    "object_counts": collection_counts
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "details": {
                    "error": str(e),
                    "url": self.config.url
                }
            }
    
    async def _cleanup(self) -> None:
        """Clean up Weaviate client connection"""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                self.logger.warning(f"Error closing Weaviate client: {e}")
    
    # Convenience method from retrieval.py
    async def find_symptom_match(self, symptom: str, limit: int = 1) -> Optional[str]:
        """
        Find matching symptom information (replaces get_symptom_info).
        
        Args:
            symptom: The symptom to search for
            limit: Number of matches to return
            
        Returns:
            Matching symptom information or None
        """
        try:
            results = await self.search(
                collection="Symptome",
                query=symptom,
                limit=limit,
                properties=["beschreibung", "schnelldiagnose"],
                return_metadata=True
            )
            
            if results:
                # Return the most relevant match
                return results[0]["properties"].get("schnelldiagnose", "")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find symptom match: {e}")
            return None


# Factory function for convenience
async def create_weaviate_service(
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> WeaviateService:
    """
    Create and initialize a Weaviate service instance.
    
    Args:
        url: Weaviate URL (uses env var if not provided)
        api_key: Weaviate API key (uses env var if not provided)
        **kwargs: Additional config parameters
        
    Returns:
        Initialized WeaviateService
    """
    config = WeaviateConfig(
        url=url,
        api_key=api_key,
        **kwargs
    )
    service = WeaviateService(config)
    await service.initialize()
    return service