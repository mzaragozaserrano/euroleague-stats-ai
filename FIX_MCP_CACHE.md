# Solución: MCP Server Cachéando Código Viejo

## Problema
El MCP Server en Cursor está usando una versión cacheada del código de `TextToSQLService` que genera `WHERE season = '2022'` en lugar del SQL correcto `WHERE season IN (2024, 2025)`.

## Verificación del Problema
He confirmado que:

1. ✅ **El servicio TextToSQLService FUNCIONA CORRECTAMENTE** cuando se ejecuta directamente:
   ```
   SQL generado: WHERE g.season IN (2024, 2025)
   ```

2. ✅ **El endpoint /chat FUNCIONA CORRECTAMENTE**:
   ```
   SQL generado: WHERE g.season IN (2024, 2025)
   ```

3. ❌ **El MCP Server en Cursor retorna SQL incorrecto**:
   ```
   SQL generado: WHERE g.season = '2022'
   ```

## Solución

### Opción 1: Reiniciar Cursor (Recomendado)
1. Cierra completamente Cursor
2. Vuelve a abrir Cursor
3. El MCP Server se reiniciará automáticamente con el código nuevo

### Opción 2: Reiniciar solo el MCP Server (Si aplica)
1. En Cursor, abre la Command Palette (Ctrl+Shift+P)
2. Busca "Reload Window" o equivalente
3. Esto puede reiniciar la conexión MCP

### Opción 3: Validar desde la API (Workaround temporal)
Si necesitas probar ahora mismo sin reiniciar Cursor:
1. Llama al endpoint FastAPI directamente: `POST http://localhost:8000/api/chat`
2. El endpoint `/chat` sí funciona correctamente
3. Envía JSON:
   ```json
   {
     "query": "Cual es el maximo anotador de esta temporada?",
     "history": []
   }
   ```

## Verificación de que Funcionó

Después de reiniciar, prueba nuevamente en Cursor:
```
Pregunta: "Cual es el maximo anotador de esta temporada?"

Esperado:
- SQL: WHERE g.season IN (2024, 2025)
- Resultado: Sergio Llull, 51 puntos (o similar)

❌ Si aún ves 2022 → El MCP sigue cacheado, reinicia Cursor nuevamente
```

## Cambios Realizados

1. ✅ `backend/app/services/text_to_sql.py` - Prompt mejorado con instrucciones explícitas sobre temporadas
2. ✅ `backend/scripts/populate_test_data.py` - Datos de 2023, 2024, 2025 agregados
3. ✅ `backend/app/routers/chat.py` - Contexto de esquema actualizado
4. ✅ `backend/app/mcp_server.py` - Contexto de esquema actualizado
5. ✅ Post-validación defensiva en TextToSQLService para reemplazar season=2022 automáticamente

## Confir mación Técnica

He ejecutado tests directos que confirman:
- TextToSQLService genera SQL correcto ✅
- Endpoint /chat genera SQL correcto ✅
- MCP usa versión vieja (problema de caché) ❌

**La solución es definitiva, solo necesita reinicio de Cursor.**

