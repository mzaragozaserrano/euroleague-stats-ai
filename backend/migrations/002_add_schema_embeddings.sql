-- Migración 002: Agregar tabla schema_embeddings para RAG
-- Idempotente: Usa CREATE TABLE IF NOT EXISTS y CREATE EXTENSION IF NOT EXISTS

-- Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla para almacenar embeddings de metadatos de esquema
CREATE TABLE IF NOT EXISTS schema_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small produce vectores de 1536 dimensiones
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índice HNSW para búsqueda eficiente de similitud vectorial
CREATE INDEX IF NOT EXISTS idx_schema_embeddings_vector ON schema_embeddings
    USING hnsw (embedding vector_cosine_ops);

-- Índice adicional para búsquedas por contenido (opcional, útil para debugging)
CREATE INDEX IF NOT EXISTS idx_schema_embeddings_content ON schema_embeddings USING gin(to_tsvector('english', content));

