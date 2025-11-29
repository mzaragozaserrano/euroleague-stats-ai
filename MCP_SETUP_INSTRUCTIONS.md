# Configuración de MCP - Próximos Pasos

## Estado Actual

Se ha completado la instalación y configuración del servidor MCP de PostgreSQL para Cursor. El sistema está listo para ejecutar consultas en lenguaje natural.

## Lo que se hizo

1. ✅ Limpieza de la configuración anterior (eliminadas secciones `tools` y `settings` innecesarias)
2. ✅ Instalación global del servidor MCP: `@modelcontextprotocol/server-postgres`
3. ✅ Creación de script wrapper PowerShell (`.cursor/start-mcp.ps1`)
4. ✅ Actualización de `.cursor/mcp.json` con configuración correcta

## Requisito: Configurar DATABASE_URL

**IMPORTANTE:** Necesitas proporcionar tu URL de conexión a Neon en el archivo `backend/.env`.

### Cómo hacerlo:

1. **Abre o crea el archivo** `backend/.env`:
   - Si no existe, créalo en la carpeta `backend/`

2. **Añade tu DATABASE_URL** (puedes obtenerla desde el dashboard de Neon):
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@ep-xxxxx.neon.tech/dbname?ssl=require
   OPENROUTER_API_KEY=tu_api_key_aqui
   OPENAI_API_KEY=tu_api_key_aqui
   ```

3. **Guardar el archivo**

## Pasos para usar MCP

1. **Reinicia Cursor completamente** (cierra y abre de nuevo)
   - Esto permite que Cursor detecte la nueva configuración de MCP

2. **Verifica que MCP está disponible:**
   - Abre el chat de Cursor
   - Si MCP está conectado correctamente, deberías ver opciones relacionadas con la base de datos

3. **Prueba con una consulta natural:**
   - Escribe en el chat de Cursor: "Puntos por partido de Shane Larkin"
   - O: "Dame el promedio de puntos de todos los jugadores"
   - Cursor debería ejecutar la consulta SQL automáticamente

## Funcionamiento

El flujo es el siguiente:

```
Tu pregunta (lenguaje natural)
        ↓
Cursor interpreta la pregunta
        ↓
MCP accede al servidor PostgreSQL (.cursor/start-mcp.ps1)
        ↓
start-mcp.ps1 carga DATABASE_URL desde backend/.env
        ↓
@modelcontextprotocol/server-postgres se conecta a Neon
        ↓
Cursor ejecuta la consulta SQL
        ↓
Resultados mostrados en el chat
```

## Solución de problemas

### "MCP no aparece en Cursor"
- Verifica que `.cursor/mcp.json` existe
- Reinicia Cursor completamente
- Abre la Developer Console (Ctrl+Shift+P → "Developer: Toggle Developer Tools")

### "Database connection failed"
- Verifica que `backend/.env` tiene `DATABASE_URL` correcto
- Verifica que la URL usa formato `postgresql+asyncpg://` (no `postgresql://`)
- Verifica que incluye `?ssl=require` al final

### "Script start-mcp.ps1 no se ejecuta"
- Ejecuta en PowerShell como admin:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

## Archivos modificados

- `.cursor/mcp.json` - Configuración limpia y correcta del servidor MCP
- `.cursor/start-mcp.ps1` - Script wrapper que carga DATABASE_URL desde backend/.env

## Siguiente paso

Proporciona tu URL de Neon y confirma que `backend/.env` está configurado. Luego, reinicia Cursor para que puedas comenzar a usar MCP.

