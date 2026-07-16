# ──────────────────────────────────────────────────────────────────────────────
# di_container.py - Dependency Injection Container
# Centralized service/dependency management for the application
# ──────────────────────────────────────────────────────────────────────────────

import logging
from typing import Callable, Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Simple dependency injection container for managing services."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_service(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self._services[name] = service
        logger.debug(f"Registered service: {name}")
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function."""
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")
    
    def register_singleton(self, name: str, factory: Callable) -> None:
        """Register a singleton (lazy-initialized)."""
        self._factories[name] = factory
        logger.debug(f"Registered singleton: {name}")
    
    def get(self, name: str) -> Any:
        """Get a service instance."""
        # Check if already registered as service
        if name in self._services:
            return self._services[name]
        
        # Check if it's a singleton that's been initialized
        if name in self._singletons:
            return self._singletons[name]
        
        # Check if it's a factory
        if name in self._factories:
            factory = self._factories[name]
            # If registered as singleton, cache the result
            if name in self._singletons or self._is_singleton_factory(name):
                instance = factory()
                self._singletons[name] = instance
                return instance
            else:
                return factory()
        
        raise KeyError(f"Service not found: {name}")
    
    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services or name in self._factories or name in self._singletons
    
    def _is_singleton_factory(self, name: str) -> bool:
        """Check if factory should create singleton (heuristic)."""
        singleton_keywords = ["database", "cache", "redis", "logger", "config"]
        return any(keyword in name.lower() for keyword in singleton_keywords)
    
    def clear(self) -> None:
        """Clear all services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.debug("Container cleared")


class Repository(ABC):
    """Base repository for data access patterns."""
    
    @abstractmethod
    async def get_by_id(self, id: int):
        """Get single item by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100):
        """Get all items with pagination."""
        pass
    
    @abstractmethod
    async def create(self, data: dict):
        """Create new item."""
        pass
    
    @abstractmethod
    async def update(self, id: int, data: dict):
        """Update item."""
        pass
    
    @abstractmethod
    async def delete(self, id: int):
        """Delete item."""
        pass


class UnitOfWork:
    """Unit of Work pattern for managing transactions."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._repositories: Dict[str, Repository] = {}
        self._is_active = False
    
    def __enter__(self):
        """Start transaction."""
        self._is_active = True
        logger.debug("Transaction started")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback."""
        if exc_type:
            self.rollback()
            logger.error(f"Transaction rolled back: {exc_val}")
        else:
            self.commit()
            logger.debug("Transaction committed")
        self._is_active = False
    
    def commit(self) -> None:
        """Commit changes."""
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            raise
    
    def rollback(self) -> None:
        """Rollback changes."""
        try:
            self.db.rollback()
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
    
    def register_repository(self, name: str, repository: Repository) -> None:
        """Register a repository."""
        self._repositories[name] = repository
    
    def get_repository(self, name: str) -> Repository:
        """Get a repository."""
        if name not in self._repositories:
            raise KeyError(f"Repository not found: {name}")
        return self._repositories[name]


class ServiceLocator:
    """Service locator pattern for dependency injection."""
    
    _container: Optional[ServiceContainer] = None
    
    @classmethod
    def initialize(cls, container: ServiceContainer) -> None:
        """Initialize the service locator."""
        cls._container = container
    
    @classmethod
    def get_service(cls, name: str) -> Any:
        """Get a service."""
        if cls._container is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._container.get(name)
    
    @classmethod
    def get_container(cls) -> ServiceContainer:
        """Get the container."""
        if cls._container is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._container
    
    @classmethod
    def reset(cls) -> None:
        """Reset the service locator."""
        if cls._container:
            cls._container.clear()
        cls._container = None


# Global container instance
container = ServiceContainer()


def setup_container():
    """Setup the default services container."""
    # This is called from app_v2.py during initialization
    logger.info("Service container initialized")
    return container


def get_container() -> ServiceContainer:
    """Get the global container."""
    return container
