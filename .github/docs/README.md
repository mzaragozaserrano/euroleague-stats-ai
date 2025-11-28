# Documentación de Git y GitHub

Este directorio contiene toda la documentación relacionada con el flujo de trabajo de Git, GitHub, creación de issues y manejo de caracteres especiales en Windows.

---

## Documento Maestro

### [GIT_GITHUB_RULES.md](./GIT_GITHUB_RULES.md)

**Documento central que consolida todas las reglas de Git y GitHub.**

Contiene:
- Reglas de commits (completos, gerundio, UTF-8)
- Normas de issues (números reales, enlaces, labels)
- Reglas sobre scripts temporales
- Configuración de Git para UTF-8

**Lee este documento primero antes de trabajar con Git o GitHub en este proyecto.**

---

## Guías Específicas

### [WINDOWS_UTF8_SETUP.md](./WINDOWS_UTF8_SETUP.md)

**Guía técnica sobre configuración UTF-8 y manejo de caracteres Unicode en Windows.**

Contiene:
- Configuración de PowerShell para UTF-8
- Tabla completa de códigos Unicode para caracteres españoles
- Sintaxis correcta: `$([char]0x00XX)` dentro de strings
- Ejemplos para commits, issues y archivos

**Consulta este documento cuando necesites usar tildes o caracteres especiales.**

### [CREAR_ISSUES.md](./CREAR_ISSUES.md)

**Guía completa para crear issues correctamente.**

Contiene:
- Resumen de normas obligatorias
- Estructura de una issue
- Proceso de creación individual
- Proceso de creación en lote (dos pasos)
- Scripts de ejemplo
- Verificación de issues

**Consulta este documento cuando necesites crear issues nuevas.**

### [EDITAR_ISSUES.md](./EDITAR_ISSUES.md)

**Guía completa para editar issues existentes.**

Contiene:
- Resumen de normas obligatorias
- Proceso de edición (obtener, modificar, guardar)
- Ejemplos completos con Unicode
- Actualización de referencias entre issues

**Consulta este documento cuando necesites editar issues existentes.**

---

## Flujo de Trabajo Recomendado

1. **Lee primero:** [GIT_GITHUB_RULES.md](./GIT_GITHUB_RULES.md) para entender las reglas generales
2. **Si vas a usar caracteres especiales:** Consulta [WINDOWS_UTF8_SETUP.md](./WINDOWS_UTF8_SETUP.md)
3. **Si vas a crear issues:** Sigue [CREAR_ISSUES.md](./CREAR_ISSUES.md)
4. **Si vas a editar issues:** Sigue [EDITAR_ISSUES.md](./EDITAR_ISSUES.md)

---

## Referencias Adicionales

- [../ISSUE_TEMPLATE/implementation_task.md](../ISSUE_TEMPLATE/implementation_task.md) - Template oficial de issues
- [../../.cursorrules](../../.cursorrules) - Reglas del proyecto para Cursor
- [../../.cursor/workflows/](../../.cursor/workflows/) - Workflows de implementación

