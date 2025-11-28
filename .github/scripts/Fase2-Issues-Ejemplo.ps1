<#
.SYNOPSIS
    EJEMPLO: Cómo quedarían los 5 issues de Fase 2 con sintaxis correcta y tildes.
    Este archivo es SOLO referencia - NO se ejecuta automáticamente.
    
    Para crear los issues, copia el contenido de $issues al New-BatchIssues.ps1 y ejecuta.
#>

# Cargar UTF-8
. "$PSScriptRoot/Enable-Utf8.ps1"

$issues = @(
    @{ 
        Title = "2.1 Vectorización: Script para generar embeddings de metadatos"; 
        Body = @"
Crear un script que genere embeddings para descripciones de tablas y columnas usando el modelo text-embedding-3-small de OpenAI.

## Tareas:
- Implementar services/vectorization.py con función vectorize_schema_metadata().
- Almacenar embeddings en tabla schema_embeddings (modelo ya existe).
- Probar con las 5 tablas principales: teams, players, games, player_stats, schema_embeddings.

## Criterios de Aceptación:
- Los embeddings se generan sin errores.
- Se pueden recuperar usando cosine similarity en PostgreSQL.
- Documentar el proceso en README.
"@; 
        Labels = "task,backend,fase-2" 
    },
    @{ 
        Title = "2.2 RAG Service: Implementar retrieve_relevant_schema()"; 
        Body = @"
Crear el servicio que recupera metadatos relevantes del esquema basándose en la consulta del usuario usando búsqueda de similaridad vectorial.

## Tareas:
- Implementar services/rag.py con función retrieve_relevant_schema(query: str).
- Usar pgvector para buscar los K embeddings más similares (K=3-5).
- Retornar nombres de tablas, columnas y ejemplos de SQL.
- Integrar con la BD mediante database.py y sesiones async.

## Criterios de Aceptación:
- La consulta 'Mejor equipo por victorias' retorna tablas relevantes.
- El promedio de latencia es menor a 500ms.
- Documentar en docs/architecture.md.
"@; 
        Labels = "task,backend,fase-2" 
    },
    @{ 
        Title = "2.3 Text-to-SQL Service: Ingeniería de prompts e integración con LLM"; 
        Body = @"
Implementar el servicio que convierte consultas en SQL usando LLM (OpenRouter).

## Tareas:
- Crear services/text_to_sql.py con función generate_sql(query: str, schema_context: str).
- Diseñar prompt engineering: System + Few-Shot examples.
- Llamar a OpenRouter API con modelo de bajo costo.
- Validar SQL generado (no DROP/DELETE).
- Capturar errores y devolver respuesta JSON estructurada.

## Criterios de Aceptación:
- 'Top 5 jugadores por puntos' genera SQL correcto.
- El LLM rechaza consultas maliciosas.
- Latencia incluida en respuesta JSON.
"@; 
        Labels = "task,backend,fase-2" 
    },
    @{ 
        Title = "2.4 Chat Endpoint: Conectar /api/chat al motor de IA"; 
        Body = @"
Implementar el endpoint final que orquesta vectorización -> RAG -> SQL -> ejecución.

## Tareas:
- Implementar POST /api/chat en routers/chat.py.
- Recibir JSON con query e history opcionales.
- Retornar JSON con sql, data, visualization, y error opcional.
- Ejecutar el SQL generado contra la BD.
- Enviar logs de RAG retrieval a stdout.
- Manejar errores de BD y LLM sin crashear el backend.

## Criterios de Aceptación:
- El endpoint responde en menos a 5 segundos.
- El campo visualization indica tipo de gráfico.
- Todos los errores retornan status 200 con campo error en JSON.
"@; 
        Labels = "task,backend,fase-2" 
    },
    @{ 
        Title = "2.5 Testing: Escenarios BDD para precisión SQL"; 
        Body = @"
Escribir tests BDD (pytest-bdd) para validar la calidad del SQL generado.

## Tareas:
- Crear tests/features/rag_sql_generation.feature con escenarios.
- Dado una consulta sobre mejores equipos, cuando genero SQL, entonces incluye TOP/ORDER BY.
- Dado entrada maliciosa, cuando intento Drop Table, entonces rechazo.
- Dado historial de chat, cuando uso contexto previo, entonces recupero schema relevante.
- Implementar step definitions en tests/step_defs/test_rag_steps.py.
- Ejecutar contra BD real (no mocks).

## Criterios de Aceptación:
- Todos los escenarios pasan (target: 10+ scenarios).
- Coverage mayor o igual a 85% en services/.
- Tests ejecutan en CI sin fallo.
"@; 
        Labels = "testing,backend,fase-2" 
    }
)

Write-Host "`nEjemplo: Los 5 issues de Fase 2 CON TILDES CORRECTAS" -ForegroundColor Cyan
Write-Host "Este archivo es solo referencia. Para usar, copia el contenido al New-BatchIssues.ps1" -ForegroundColor Yellow
Write-Host "`nIssues a crear:`n" -ForegroundColor Cyan

foreach ($issue in $issues) {
    Write-Host "- $($issue.Title)" -ForegroundColor Green
}

Write-Host "`nPara crear estos issues, copia el contenido de `$issues al New-BatchIssues.ps1 y ejecuta." -ForegroundColor Yellow

