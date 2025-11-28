# Guía de Creación de Issues

Esta guía define las normas y herramientas para crear tareas en el proyecto.

## ⚠️ Normas Críticas (Obligatorio)

1.  **Codificación UTF-8:**
    * **Referencia:** Ver `.github/docs/WINDOWS_UTF8_SETUP.md`.
    * **Acción:** Los scripts de creación ya manejan la codificación, pero si escribes texto manual, usa códigos Unicode `$([char]0x00XX)` para tildes/ñ.

2.  **Números de Issue Reales:**
    * En "Dependencias" y "Bloquea a", usa SIEMPRE el ID real (ej: `#17`), NUNCA el número de fase (ej: `#1.2`).
    * Si la issue dependiente no existe, pon "Por determinar" y actualízala después.

3.  **Enlaces a Documentación:**
    * Usa rutas relativas desde la raíz.
    * Formato: `[NOMBRE_ARCHIVO.md](../../docs/ruta/archivo.md)`.
    * **Prohibido:** Poner la ruta completa en el texto visible del enlace.

---

## Herramientas de Creación (Scripts)

No ejecutes comandos manuales de GitHub CLI. Usa los scripts automatizados que manejan UTF-8 y plantillas correctamente.

### A. Creación Individual
Para crear una única tarea:
1. Abre y edita las variables `$Title` y `$Body` en:
   `.github/scripts/New-Issue.ps1`
2. Ejecuta el script:
   ```powershell
   .\.github\scripts\New-Issue.ps1