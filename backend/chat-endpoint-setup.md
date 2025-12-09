# Chat Endpoint - Guía de Configuración

## Descripción

El endpoint `POST /api/chat` implementa la orquestación completa del pipeline de IA:

1. **Vectorización de Query**: Genera embedding de la consulta del usuario
2. **RAG Retrieval**: Recupera metadatos de esquema relevantes
3. **SQL Generation**: LLM (OpenRouter) convierte query natural a SQL
4. **SQL Validation**: Verifica que SQL sea seguro (no DROP/DELETE)
5. **BD Execution**: Ejecuta SQL contra Neon
6. **Response**: Retorna `{sql, data, visualization, error?}`

## Configuración Requerida

### 1. Variables de Entorno

Agregar a `.env`:

```env
# Neon Database (ya configurada)
DATABASE_URL=postgresql+asyncpg://...

# OpenAI Embeddings API (para RAG)
OPENAI_API_KEY=sk-...

# OpenRouter API (para SQL Generation)
OPENROUTER_API_KEY=sk-or-...
```

### 2. Instalar Dependencias

```powershell
cd backend;
poetry install;
```

Las dependencias ya están en `pyproject.toml`:
- `openai` (para embeddings y OpenRouter)
- `langchain` (orquestación)
- `asyncpg` (driver PostgreSQL)

## Uso

### Request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "puntos de Larkin en la temporada",
    "history": []
  }'
```

### Response

```json
{
  "sql": "SELECT p.name, SUM(ps.points) as total_points FROM players p JOIN player_stats_games ps ON p.id = ps.player_id WHERE p.name ILIKE '%Larkin%' GROUP BY p.id, p.name ORDER BY total_points DESC;",
  "data": [
    {"name": "Larkin", "total_points": 1250}
  ],
  "visualization": "table"
}
```

### Error Handling

Todos los errores retornan status 200 con campo `error`:

```json
{
  "sql": null,
  "data": null,
  "visualization": null,
  "error": "OpenRouter tardo demasiado en responder"
}
```

## Criterios de Aceptación

- [x] Endpoint responde en < 5 segundos
- [x] Campo `visualization` indica tipo de gráfico ('table', 'bar', 'line')
- [x] Todos los errores retornan status 200 con campo `error`
- [x] SQL se ejecuta contra BD Neon
- [x] Logs de RAG retrieval en stdout
- [x] No DROP/DELETE statements
- [x] Manejo robusto sin crashes

## Testing

### Ejecutar Tests BDD

```powershell
cd backend;
poetry run pytest tests/features/chat_endpoint.feature -v;
```

### Tests Específicos

```powershell
# Test de respuesta válida
poetry run pytest tests/step_defs/test_chat_endpoint_steps.py::test_check_status_200 -v;

# Test de SQL peligroso
poetry run pytest tests/step_defs/test_chat_endpoint_steps.py::test_check_dangerous_query_error -v;

# Test de error handling
poetry run pytest tests/step_defs/test_chat_endpoint_steps.py::test_backend_alive -v;
```

## Logging

El endpoint registra:

```
INFO: Chat request recibido: 'puntos de Larkin' con 0 mensajes de historial
INFO: Paso 1: Recuperando contexto de esquema...
INFO: RAG retrieval: 5 documentos encontrados con similarity scores
INFO: Paso 2: Generando SQL con OpenRouter...
INFO: SQL generado: SELECT p.name, SUM(ps.points)...
INFO: Paso 3: Ejecutando SQL contra la BD...
INFO: Ejecución exitosa: 1 registros
INFO: Chat endpoint completado en 1234.56ms
```

## Optimizaciones Futuras

1. **Caché de Embeddings**: Almacenar embeddings de queries frecuentes
2. **Rate Limiting**: Implementar límite de requests por usuario
3. **Modelo Específico**: Fine-tuning del modelo para Euroleague
4. **Validación JSON**: Parser estricto para respuesta del LLM
5. **Metrics**: Prometheus para latencia y accuracy

## Troubleshooting

### "Servicio de IA no está disponible"
- Verificar `OPENROUTER_API_KEY` en `.env`
- Conectarse a https://openrouter.ai y confirmar saldo

### "OpenRouter tardo demasiado en responder"
- Aumentar `timeout` en `text_to_sql.py` (línea ~50)
- Verificar conexión a internet

### "Error ejecutando consulta"
- Revisar logs de la BD
- Verificar permisos del usuario PostgreSQL
- Confirmar que tablas existen en Neon

### "El LLM retornó un formato inválido"
- LLM no retornó JSON válido
- Aumentar `temperature` en `text_to_sql.py` para más creatividad
- Revisar system prompt en `_get_system_prompt()`

## Arquitectura

```
ChatRequest (query, history)
    ↓
1. _get_schema_context()
    ↓ (SQLAlchemy AsyncSession)
    ├→ SELECT FROM schema_embeddings (20 filas)
    └→ Schema markdown para LLM
    ↓
2. TextToSQLService.generate_sql_with_fallback()
    ↓ (OpenRouter API)
    ├→ System Prompt + Few-Shot Examples
    ├→ History de conversacion
    └→ User Query
    ↓ (retry up to 2x)
    ├→ Validar SQL safety
    └→ Retornar (sql, visualization_type, error)
    ↓
3. _execute_sql()
    ↓ (Neon PostgreSQL)
    ├→ Execute SELECT query
    └→ Convert rows to dict list
    ↓
ChatResponse (sql, data, visualization, error?)
```

## Monitoreo

### KPIs a Rastrear

- **Latencia p50/p95/p99**: Bajo 2s idealmente
- **Accuracy**: % de queries que retornan resultados válidos
- **Error Rate**: Errores de LLM / Total de requests
- **Cost**: Tokens consumidos en OpenRouter

### Dashboard Recomendado

Implementar endpoint `GET /api/metrics` que retorne:
```json
{
  "chat_requests_total": 1234,
  "chat_latency_ms_p95": 1250,
  "chat_errors": {
    "llm_timeout": 5,
    "sql_generation_failed": 3,
    "db_connection": 1
  },
  "openrouter_tokens_used": 45230
}
```

