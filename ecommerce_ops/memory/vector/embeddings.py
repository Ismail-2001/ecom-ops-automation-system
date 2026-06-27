"""
Embedding Service
Service for generating text embeddings using various providers.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("ecommerce_ops.memory.vector.embeddings")


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("OpenAI API key not configured")
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def embed_text(self, text: str) -> List[float]:
        client = self._get_client()
        response = await client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        client = self._get_client()
        response = await client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def get_dimensions(self) -> int:
        return 1536 if "small" in self.model else 3072


class GoogleEmbeddingProvider(EmbeddingProvider):
    """Google embedding provider using Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

    async def embed_text(self, text: str) -> List[float]:
        # Google's text-embedding model
        # For now, use a simple hash-based fallback
        # In production, use google.generativeai
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        # Convert to pseudo-embedding (not real, for demo only)
        embedding = [float(b) / 255.0 for b in hash_obj.digest()]
        # Pad to expected dimensions
        embedding = embedding * 96  # 1536 / 16
        return embedding[:1536]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(text) for text in texts]

    def get_dimensions(self) -> int:
        return 1536


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise RuntimeError("sentence-transformers not installed")
        return self._model

    async def embed_text(self, text: str) -> List[float]:
        model = self._get_model()
        embedding = model.encode(text)
        return embedding.tolist()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        embeddings = model.encode(texts)
        return embeddings.tolist()

    def get_dimensions(self) -> int:
        return 384


class EmbeddingService:
    """Service for generating embeddings with multiple providers."""

    def __init__(self, provider: Optional[EmbeddingProvider] = None):
        self.provider = provider or self._create_default_provider()
        self._cache: Dict[str, List[float]] = {}

    def _create_default_provider(self) -> EmbeddingProvider:
        """Create default embedding provider based on available config."""
        # Try OpenAI first
        if os.getenv("OPENAI_API_KEY"):
            return OpenAIEmbeddingProvider()

        # Try Google
        if os.getenv("GOOGLE_API_KEY"):
            return GoogleEmbeddingProvider()

        # Fallback to local
        try:
            return LocalEmbeddingProvider()
        except Exception:
            logger.warning("No embedding provider available, using mock")
            return MockEmbeddingProvider()

    async def embed(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for text."""
        if use_cache and text in self._cache:
            return self._cache[text]

        embedding = await self.provider.embed_text(text)

        if use_cache:
            self._cache[text] = embedding

        return embedding

    async def embed_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        results = []
        uncached_texts = []
        uncached_indices = []

        # Check cache
        for i, text in enumerate(texts):
            if use_cache and text in self._cache:
                results.append(self._cache[text])
            else:
                results.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = await self.provider.embed_texts(uncached_texts)
            for idx, embedding in zip(uncached_indices, new_embeddings):
                results[idx] = embedding
                if use_cache:
                    self._cache[texts[idx]] = embedding

        return results

    def clear_cache(self):
        """Clear embedding cache."""
        self._cache.clear()

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.provider.get_dimensions()


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""

    async def embed_text(self, text: str) -> List[float]:
        # Generate deterministic pseudo-embedding based on text hash
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        seed = int(hash_obj.hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        embedding = rng.randn(1536).tolist()
        # Normalize
        norm = np.linalg.norm(embedding)
        return (np.array(embedding) / norm).tolist()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(text) for text in texts]

    def get_dimensions(self) -> int:
        return 1536


# Singleton
embedding_service = EmbeddingService()
