# Workflow de Merge y Cierre de Tarea (Cleanup)

Este documento es una lista de control ejecutable para cerrar el ciclo de una tarea. Úsalo cuando la PR haya sido aprobada y esté lista para integrarse.

## 0. Pre-condiciones
- [ ] Identifica el número de Issue (ID) asociado a la tarea actual (ej: #4).
- [ ] Asegúrate de estar situado en la rama de la feature que quieres mergear.
- [ ] Verifica que la PR ha sido aprobada (si es un requisito del repo).

## 1. Fusión de la Pull Request (Remote)
- [ ] **Merge y Borrado Remoto:** Fusiona la PR actual y elimina la rama en GitHub automáticamente:
    * Ejecuta: `gh pr merge --merge --delete-branch`
    * *Nota:* Si pregunta confirmación, acepta.

## 2. Actualización de la Issue Actual
- [ ] **Etiquetado:** Actualiza el estado visual de la issue:
    * Ejecuta: `gh issue edit <NUMERO_ISSUE> --remove-label "needs review" --add-label "done"`
    * Adapta los nombres de los labels según tu proyecto (ej: "in-progress", "completed", etc.)
- [ ] **Cierre:** Cierra la issue de la tarea actual formalmente:
    * Ejecuta: `gh issue close <NUMERO_ISSUE>`
    * *Nota:* SOLO se cierra la issue de la tarea actual, NO las issues referenciadas en la PR.
    * Si la PR usó "Closes #<NUMERO_ISSUE>", la issue se cerrará automáticamente.

## 3. Limpieza Local (Local Cleanup)
- [ ] **Capturar nombre de rama:** Guarda el nombre de la rama actual (la que acabamos de mergear) para borrarla después.
- [ ] **Vuelta a Base:** Cambia a la rama principal de tu proyecto:
    * Ejecuta: `git checkout <RAMA_BASE>`
    * Común: `main`, `master`, `develop`
- [ ] **Sincronización:** Descarga los cambios recién mergeados:
    * Ejecuta: `git pull`
- [ ] **Borrado Local:** Elimina la rama de feature localmente (ya que ya no existe en remoto):
    * Ejecuta: `git branch -d <NOMBRE_RAMA_ANTERIOR>`
    * *Nota:* Si git se queja de que no está mergeada (a veces pasa por latencia), usa `-D` forzado, ya que sabemos que se mergeó en el paso 1.

## 4. Actualización de Documentación

- [ ] **Crear Documento de Historial:**
    * Ubicación común: `docs/`, `docs/history/`, `CHANGELOG.md`, etc.
    * Formato de nombre sugerido: `YYYY-MM-DD_<descripcion>.md`
    * **Contenido mínimo recomendado:**
      - Título y fecha de finalización
      - Número de issue y PR
      - Resumen de cambios implementados
      - Archivos creados/modificados
      - Criterios de aceptación verificados
      - Enlaces a issue y PR cerradas
- [ ] **Actualizar Roadmap/Changelog:**
    * **OBLIGATORIO:** Actualizar el historial del roadmap con los nuevos cambios:
      - Ubicación: `docs/history/<fecha>_<descripcion>.md`
      - Marcar la tarea como completada
      - Incluir resumen de cambios implementados
      - Incluir archivos creados/modificados
      - Incluir criterios de aceptación verificados
      - Añadir referencias a issue y PR cerradas
    * Si tu proyecto tiene un `CHANGELOG.md` o roadmap principal:
      - Actualizar versión o progreso
      - Añadir referencia a la issue/PR/historial
- [ ] **Commit de Documentación:**
    * Ejecuta: `git add <archivos-de-documentacion>`
    * Ejemplo de mensaje de commit:
      ```bash
      git commit -m "docs: Update documentation for #<NUMERO_ISSUE>"
      git push
      ```
    * **Nota para Windows con PowerShell:** Si usas caracteres especiales (tildes, ñ), consulta la guía de UTF-8 de tu proyecto.

## 5. Verificación Final
- [ ] Comprueba que estás en la rama base (ej: `main`, `master`, `develop`).
- [ ] Comprueba que `git status` está limpio.
- [ ] Verifica que la documentación fue actualizada y pusheada.
- [ ] Confirma al usuario que la tarea <NUMERO_ISSUE> ha sido completada y archivada.
