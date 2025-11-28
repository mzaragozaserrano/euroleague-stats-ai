from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base


class SchemaEmbedding(Base):
    """
    Modelo SQLAlchemy para la tabla 'schema_embeddings'.
    Almacena embeddings vectoriales del esquema para RAG (schema retrieval).

    Propósito: Permite al LLM encontrar las definiciones de tablas y columnas
    relevantes sin cargar todo el esquema en la ventana de contexto.
    """

    __tablename__ = "schema_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    # embedding column será manejado por pgvector
    # En SQLAlchemy, este será representado como un tipo Vector personalizado
    # Por ahora, lo dejamos como referencia en comentarios
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SchemaEmbedding(id={self.id}, content_length={len(self.content) if self.content else 0})>"
