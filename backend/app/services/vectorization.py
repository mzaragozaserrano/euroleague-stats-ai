"""
Servicio de Vectorización para RAG.

Este módulo proporciona funciones para generar embeddings de metadatos de esquema
usando OpenAI text-embedding-3-small y almacenarlos en PostgreSQL con pgvector.

Propósito: Indexar descripciones de tablas, columnas y ejemplos SQL para que el LLM
pueda recuperar el esquema relevante sin cargar todo en la ventana de contexto.
"""

from typing import List, Optional
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Configuración de OpenAI
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


class VectorizationService:
    """
    Servicio para generar y gestionar embeddings de esquema.
    """

    def __init__(self, api_key: str):
        """
        Inicializa el servicio con la clave de API de OpenAI.

        Args:
            api_key: Clave de API de OpenAI.
        """
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Genera un embedding para un texto dado usando OpenAI.

        Args:
            text: Texto a vectorizar.

        Returns:
            Vector de embedding (1536 dimensiones).

        Raises:
            Exception: Si falla la llamada a OpenAI API.
        """
        try:
            response = await self.client.embeddings.create(
                model=EMBEDDING_MODEL, input=text, dimensions=EMBEDDING_DIMENSIONS
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise

    async def vectorize_schema_metadata(
        self, session: AsyncSession, metadata: List[dict]
    ) -> int:
        """
        Vectoriza metadatos de esquema y los almacena en PostgreSQL.

        Args:
            session: Sesión de base de datos asincrónica.
            metadata: Lista de diccionarios con estructura:
                {
                    "content": str (descripción del tabla/columna/ejemplo),
                    "type": str (opcional, para categorizar)
                }

        Returns:
            Número de embeddings insertados exitosamente.

        Raises:
            Exception: Si falla la inserción en la base de datos.
        """
        inserted_count = 0

        for item in metadata:
            try:
                content = item.get("content")
                if not content:
                    logger.warning("Contenido vacío encontrado en metadatos")
                    continue

                # Generar embedding
                embedding = await self.generate_embedding(content)

                # Insertar en base de datos
                await session.execute(
                    text(
                        """
                        INSERT INTO schema_embeddings (content, embedding)
                        VALUES (:content, :embedding)
                        """
                    ),
                    {
                        "content": content,
                        "embedding": embedding,  # pgvector maneja la conversión
                    },
                )
                inserted_count += 1
                logger.info(f"Embedding insertado: {content[:50]}...")

            except Exception as e:
                logger.error(f"Error procesando metadata: {e}")
                raise

        await session.commit()
        logger.info(f"Total de {inserted_count} embeddings insertados exitosamente")
        return inserted_count

    async def retrieve_relevant_schema(
        self, session: AsyncSession, query: str, limit: int = 5
    ) -> List[dict]:
        """
        Recupera metadatos de esquema relevantes para una query usando cosine similarity.

        Args:
            session: Sesión de base de datos asincrónica.
            query: Consulta natural del usuario (ej: "puntos de Larkin vs Micic").
            limit: Número máximo de resultados a retornar.

        Returns:
            Lista de diccionarios con esquema relevante:
                {
                    "id": str (UUID),
                    "content": str (descripción),
                    "similarity": float (puntuación 0-1)
                }

        Raises:
            Exception: Si falla la búsqueda en la base de datos.
        """
        try:
            # Generar embedding de la query
            query_embedding = await self.generate_embedding(query)

            # Buscar embeddings similares en PostgreSQL
            result = await session.execute(
                text(
                    """
                    SELECT id, content, 1 - (embedding <=> :query_embedding) as similarity
                    FROM schema_embeddings
                    ORDER BY embedding <=> :query_embedding
                    LIMIT :limit
                    """
                ),
                {
                    "query_embedding": query_embedding,
                    "limit": limit,
                },
            )

            rows = result.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "content": row[1],
                    "similarity": float(row[2]),
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error recuperando esquema relevante: {e}")
            raise

    async def clear_schema_embeddings(self, session: AsyncSession) -> int:
        """
        Limpia todos los embeddings de esquema (útil para reiniciar).

        Args:
            session: Sesión de base de datos asincrónica.

        Returns:
            Número de filas eliminadas.

        Raises:
            Exception: Si falla la eliminación.
        """
        try:
            result = await session.execute(text("DELETE FROM schema_embeddings"))
            await session.commit()
            deleted_count = result.rowcount
            logger.info(f"Se eliminaron {deleted_count} embeddings de esquema")
            return deleted_count
        except Exception as e:
            logger.error(f"Error limpiando embeddings: {e}")
            raise

