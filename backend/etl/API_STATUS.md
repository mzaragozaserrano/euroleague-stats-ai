# Estado de la API de Euroleague

## Problema Actual

La API pública de Euroleague no está disponible o ha cambiado sus endpoints. Los intentos de conexión resultan en errores 404.

### URLs Probadas

1. ❌ `https://api-live.euroleague.net/teams` → 404
2. ❌ `https://live.euroleague.net/api/teams` → 404 (HTML)
3. ✅ `https://live.euroleague.net/api` → 200 (pero endpoints específicos fallan)

## Opciones Disponibles

### Opción 1: Usar Datos de Prueba (ACTUAL)

**Estado:** ✅ Implementado

El proyecto actualmente usa datos de prueba creados por `scripts/populate_test_data.py`:
- 5 equipos
- 6 jugadores
- 3 partidos
- Estadísticas de ejemplo

**Uso:**
```bash
cd backend
poetry run python scripts/populate_test_data.py
```

**Ventajas:**
- Funciona inmediatamente
- No depende de APIs externas
- Ideal para desarrollo y demos

**Desventajas:**
- Datos limitados (solo 6 jugadores)
- No refleja datos reales de temporada actual

### Opción 2: Investigar API Oficial

**Estado:** 🔍 Pendiente de investigación

La Euroleague puede tener una API oficial que requiere:
- Registro/autenticación
- API key
- Documentación privada

**Acciones necesarias:**
1. Contactar con Euroleague para acceso a API
2. Revisar si existe documentación oficial
3. Buscar proyectos open-source que usen la API

### Opción 3: Web Scraping

**Estado:** ⚠️ Alternativa

Si no hay API pública, se puede hacer scraping de:
- `https://www.euroleague.net/`
- Páginas de estadísticas individuales

**Ventajas:**
- Datos reales y actualizados
- No requiere API key

**Desventajas:**
- Más frágil (cambios en HTML rompen el scraper)
- Más lento que una API
- Puede violar términos de servicio

### Opción 4: Usar Dataset Estático

**Estado:** 💡 Recomendado para MVP

Descargar un dataset histórico de Euroleague de fuentes como:
- Kaggle
- Basketball-Reference
- Datasets académicos

**Ventajas:**
- Datos reales y completos
- No depende de APIs externas
- Suficiente para demostrar funcionalidad

**Desventajas:**
- No se actualiza automáticamente
- Puede estar desactualizado

## Recomendación Actual

Para el MVP y desarrollo:

1. **Corto plazo:** Continuar con datos de prueba (`populate_test_data.py`)
2. **Mediano plazo:** Buscar dataset estático de Euroleague en Kaggle/GitHub
3. **Largo plazo:** Investigar API oficial o implementar scraping robusto

## Cómo Agregar Más Datos de Prueba

Si necesitas más datos para testing, edita `backend/scripts/populate_test_data.py`:

```python
# Agregar más jugadores
players_data = [
    {"id": 7, "name": "Nuevo Jugador", "team_id": teams[0].id, "position": "SG"},
    # ... más jugadores
]

# Agregar más partidos
games_data = [
    {
        "id": 4,
        "season": 2024,
        "round": 3,
        # ... más datos
    },
]
```

Luego ejecuta:
```bash
poetry run python scripts/populate_test_data.py
```

## Referencias

- [Euroleague Official Website](https://www.euroleague.net/)
- [Basketball-Reference](https://www.basketball-reference.com/international/)
- [Kaggle Basketball Datasets](https://www.kaggle.com/search?q=euroleague)

