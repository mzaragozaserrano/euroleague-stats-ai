# Guía de Edición de Issues

Utiliza esta guía para actualizar dependencias, corregir textos o modificar el estado de bloqueo de las tareas.

## ⚠️ Normas de Edición

1.  **Integridad de Referencias:**
    * **Bloquea a:** Issues que no pueden empezar hasta que esta termine.
    * **Dependencias:** Issues que deben terminar antes de empezar esta.
    * *Regla:* Si A bloquea a B -> B depende de A. Mantén esta coherencia.

2.  **UTF-8 Strict:**
    * Al igual que en la creación, cualquier texto nuevo con caracteres especiales debe respetar las normas de `.github/docs/WINDOWS_UTF8_SETUP.md`.

---

## Herramienta de Edición (Script)

No uses `gh issue edit` manualmente para evitar corromper la codificación de caracteres en Windows.

### Uso del Script
El script descarga el cuerpo actual, permite modificaciones seguras y actualiza la issue.

1.  Abre el script `.github/scripts/Edit-Issue.ps1`.
2.  En la sección "MODIFICACIONES", define qué quieres cambiar (ej: actualizar un ID de dependencia usando `-replace`).
3.  Ejecuta el script indicando el número de issue:

```powershell
.\.github\scripts\Edit-Issue.ps1 -IssueNumber 40