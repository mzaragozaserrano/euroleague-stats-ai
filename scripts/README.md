# Scripts del Proyecto

Esta carpeta contiene scripts de utilidad para el proyecto.

## Scripts Disponibles

### `verify_setup.py`

Script de verificación del setup de la Fase 0. Verifica que todos los archivos y configuraciones necesarios estén en su lugar.

**Uso:**
```powershell
python scripts/verify_setup.py
```

**Qué verifica:**
- Archivos del backend (Poetry, FastAPI, routers, tests)
- Archivos del frontend (Next.js, TypeScript, Tailwind)
- GitHub Actions workflows
- Archivos de configuración (.gitignore, .env.example)

**Salida:**
- `[OK]` - Archivo encontrado y correcto
- `[FALTA]` - Archivo no encontrado

**Código de salida:**
- `0` - Todos los archivos verificados correctamente
- `1` - Algunos archivos faltan

## Agregar Nuevos Scripts

Cuando agregues nuevos scripts a esta carpeta:

1. Añade una descripción en este README
2. Incluye comentarios en el código explicando su propósito
3. Asegúrate de que sean ejecutables desde la raíz del proyecto
4. Usa rutas relativas a la raíz del proyecto (ej: `backend/`, `frontend/`)

