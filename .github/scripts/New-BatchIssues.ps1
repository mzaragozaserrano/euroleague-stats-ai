<#
.SYNOPSIS
    Crea issues en GitHub en lote basándose en una lista definida.
    Este script es modificado automáticamente por el Agente de Cursor antes de su ejecución.
#>

# 1. CARGA LA CONFIGURACIÓN UTF-8 (Para que veas bien los logs)
# $PSScriptRoot es la carpeta donde está este script.
# Si el fichero Enable-Utf8.ps1 no existe, ignoramos el error para no romper nada.
if (Test-Path "$PSScriptRoot/Enable-Utf8.ps1") {
    . "$PSScriptRoot/Enable-Utf8.ps1"
}

# --- ZONA EDITABLE POR EL AGENTE ---
# El agente rellenará este array basándose en el Roadmap.
# IMPORTANTE AGENTE: 
# 1. Usa codificación Hex para caracteres especiales. Ej: "Configuraci$([char]0x00F3)n"
# 2. Consulta .github/docs/labels_convention.md para asignar labels correctamente.
#    Formato: "tipo,tecnologia,fase-X" (ej: "task,backend,fase-2")
$issues = @(
    @{ 
        Title = "2.1 Vectorizaci$([char]0x00F3)n: Script para generar embeddings de metadatos"; 
        Body = "Crear un script que genere embeddings para descripciones de tablas y columnas usando el modelo text-embedding-3-small de OpenAI.`n`n## Tareas:`n- Implementar services/vectorization.py con funci$([char]0x00F3)n vectorize_schema_metadata().`n- Almacenar embeddings en tabla schema_embeddings (modelo ya existe).`n- Probar con las 5 tablas principales: teams, players, games, player_stats, schema_embeddings.`n`n## Criterios de Aceptaci$([char]0x00F3)n:`n- Los embeddings se generan sin errores.`n- Se pueden recuperar usando cosine similarity en PostgreSQL.`n- Documentar el proceso en README."; 
        Labels = "task,backend,fase-2" 
    },
    @{ 
        Title = "2.2 RAG Service: Implementar retrieve_relevant_schema()"; 
        Body = "Crear el servicio que recupera metadatos relevantes del esquema basandose en la consulta del usuario usando busqueda de similaridad vectorial.`n`n## Tareas:`n- Implementar services/rag.py con funci$([char]0x00F3)n retrieve_relevant_schema(query: str).`n- Usar pgvector para buscar los K embeddings mas similares (K=3-5).`n- Retornar nombres de tablas, columnas y ejemplos de SQL.`n- Integrar con la BD mediante database.py y sesiones async.`n`n## Criterios de Aceptaci$([char]0x00F3)n:`n- La consulta 'Mejor equipo por victorias' retorna tablas relevantes.`n- El promedio de latencia es menor a 500ms.`n- Documentar en docs/architecture.md."; 
        Labels = "task,backend,fase-2" 
    },
    @{ 
        Title = "2.3 Text-to-SQL Service: Ingenieria de prompts e integraci$([char]0x00F3)n con LLM"; 
        Body = "Implementar el servicio que convierte consultas en SQL usando LLM (OpenRouter).`n`n## Tareas:`n- Crear services/text_to_sql.py con funci$([char]0x00F3)n generate_sql(query: str, schema_context: str).`n- Disenar prompt engineering: System + Few-Shot examples.`n- Llamar a OpenRouter API con modelo de bajo costo.`n- Validar SQL generado (no DROP/DELETE).`n- Capturar errores y devolver respuesta JSON estructurada.`n`n## Criterios de Aceptaci$([char]0x00F3)n:`n- 'Top 5 jugadores por puntos' genera SQL correcto.`n- El LLM rechaza consultas maliciosas.`n- Latencia incluida en respuesta JSON."; 
        Labels = "task,backend,fase-2" 
    },
    @{ 
        Title = "2.4 Chat Endpoint: Conectar /api/chat al motor de IA"; 
        Body = "Implementar el endpoint final que orquesta vectorizaci$([char]0x00F3)n -> RAG -> SQL -> ejecuci$([char]0x00F3)n.`n`n## Tareas:`n- Implementar POST /api/chat en routers/chat.py.`n- Recibir JSON con query e history opcionales.`n- Retornar JSON con sql, data, visualization, y error opcional.`n- Ejecutar el SQL generado contra la BD.`n- Enviar logs de RAG retrieval a stdout.`n- Manejar errores de BD y LLM sin crashear el backend.`n`n## Criterios de Aceptaci$([char]0x00F3)n:`n- El endpoint responde en menos a 5 segundos.`n- El campo visualization indica tipo de gr$([char]0x00E1)fico.`n- Todos los errores retornan status 200 con campo error en JSON."; 
        Labels = "task,backend,fase-2" 
    },
    @{ 
        Title = "2.5 Testing: Escenarios BDD para precisi$([char]0x00F3)n SQL"; 
        Body = "Escribir tests BDD (pytest-bdd) para validar la calidad del SQL generado.`n`n## Tareas:`n- Crear tests/features/rag_sql_generation.feature con escenarios.`n- Dado una consulta sobre mejores equipos, cuando genero SQL, entonces incluye TOP/ORDER BY.`n- Dado entrada maliciosa, cuando intento Drop Table, entonces rechazo.`n- Dado historial de chat, cuando uso contexto previo, entonces recupero schema relevante.`n- Implementar step definitions en tests/step_defs/test_rag_steps.py.`n- Ejecutar contra BD real (no mocks).`n`n## Criterios de Aceptaci$([char]0x00F3)n:`n- Todos los escenarios pasan (target: 10+ scenarios).`n- Coverage mayor o igual a 85% en services/.`n- Tests ejecutan en CI sin fallo."; 
        Labels = "testing,backend,fase-2" 
    }
)
# -----------------------------------

Write-Host "`n[Iniciando creaci$([char]0x00F3)n de lote de issues...]" -ForegroundColor Cyan

# Verificación de seguridad básica
if ($issues.Count -eq 0) {
    Write-Warning "La lista de issues está vacía. No hay nada que crear."
    exit
}

foreach ($issue in $issues) {
    # Mostramos en pantalla el título
    Write-Host "Creando: $($issue.Title)..." -NoNewline
    
    # Ejecutamos el comando de GitHub CLI
    $result = gh issue create --title $issue.Title --body $issue.Body --label $issue.Labels 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " ERROR" -ForegroundColor Red
        Write-Host $result -ForegroundColor Yellow
    }
    
    # Pequeña pausa de 500ms
    Start-Sleep -Milliseconds 500 
}

Write-Host "`n[Proceso finalizado.]" -ForegroundColor Cyan
