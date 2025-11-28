"""
Unit tests para el servicio TextToSQLService.
Cubre: SQL validation, safety checks, prompt engineering.
"""

import pytest
import logging
from app.services.text_to_sql import TextToSQLService

logger = logging.getLogger(__name__)


class TestTextToSQLSafety:
    """Tests para validación de seguridad SQL."""

    @pytest.fixture
    def service(self):
        """Instancia del servicio con mock key."""
        return TextToSQLService(api_key="test-key-mock")

    def test_validate_sql_safety_accepts_select(self, service):
        """SELECT queries deben ser aceptadas."""
        sql = "SELECT * FROM players WHERE id = 1;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is True
        assert error_msg is None

    def test_validate_sql_safety_rejects_drop(self, service):
        """DROP queries deben ser rechazadas."""
        sql = "DROP TABLE players;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False
        assert "DROP" in error_msg

    def test_validate_sql_safety_rejects_delete(self, service):
        """DELETE queries deben ser rechazadas."""
        sql = "DELETE FROM players WHERE 1=1;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False
        assert "DELETE" in error_msg

    def test_validate_sql_safety_rejects_truncate(self, service):
        """TRUNCATE queries deben ser rechazadas."""
        sql = "TRUNCATE TABLE players;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False
        assert "TRUNCATE" in error_msg

    def test_validate_sql_safety_rejects_alter(self, service):
        """ALTER queries deben ser rechazadas."""
        sql = "ALTER TABLE players ADD COLUMN hack VARCHAR(100);"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False
        assert "ALTER" in error_msg

    def test_validate_sql_safety_rejects_update(self, service):
        """UPDATE queries deben ser rechazadas."""
        sql = "UPDATE players SET name = 'hacked' WHERE 1=1;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False
        assert "UPDATE" in error_msg

    def test_validate_sql_safety_rejects_insert(self, service):
        """INSERT queries deben ser rechazadas."""
        sql = "INSERT INTO players (name) VALUES ('hacked');"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False
        assert "INSERT" in error_msg

    def test_validate_sql_safety_rejects_non_select(self, service):
        """Non-SELECT queries deben ser rechazadas."""
        sql = "CREATE TABLE hack (id INT);"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False
        assert "SELECT" in error_msg

    def test_validate_sql_safety_rejects_unbalanced_parens(self, service):
        """SQL con paréntesis desbalanceados deben ser rechazado."""
        sql = "SELECT * FROM players WHERE (id = 1;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False
        assert "Parentesis" in error_msg

    def test_validate_sql_safety_accepts_joins(self, service):
        """SELECT con JOINs deben ser aceptadas."""
        sql = "SELECT p.name, t.name FROM players p JOIN teams t ON p.team_id = t.id;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is True

    def test_validate_sql_safety_accepts_subqueries(self, service):
        """SELECT con subqueries deben ser aceptadas."""
        sql = "SELECT name FROM players WHERE id IN (SELECT player_id FROM player_stats_games);"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is True

    def test_validate_sql_safety_accepts_aggregations(self, service):
        """SELECT con agregaciones deben ser aceptadas."""
        sql = "SELECT team_id, COUNT(*) as player_count FROM players GROUP BY team_id;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is True

    def test_validate_sql_safety_case_insensitive(self, service):
        """Validación de seguridad debe ser case-insensitive."""
        sql = "select * from players; drop table teams;"
        is_safe, error_msg = service._validate_sql_safety(sql)
        assert is_safe is False


class TestTextToSQLPrompt:
    """Tests para construcción del prompt del sistema."""

    @pytest.fixture
    def service(self):
        """Instancia del servicio."""
        return TextToSQLService(api_key="test-key-mock")

    def test_system_prompt_includes_schema(self, service):
        """System prompt debe incluir el contexto del esquema."""
        schema_context = "Tables: players, teams, games"
        prompt = service._get_system_prompt(schema_context)
        
        assert "players" in prompt or "Tables" in prompt
        assert "SQL" in prompt
        assert "JSON" in prompt

    def test_system_prompt_includes_few_shot_examples(self, service):
        """System prompt debe incluir ejemplos few-shot."""
        schema_context = "Tables: players"
        prompt = service._get_system_prompt(schema_context)
        
        # Verificar que hay ejemplos
        assert "Example" in prompt or "example" in prompt or "puntos" in prompt

    def test_system_prompt_enforces_json_format(self, service):
        """System prompt debe enforcer formato JSON."""
        schema_context = "Tables: players"
        prompt = service._get_system_prompt(schema_context)
        
        assert "JSON" in prompt
        assert "sql" in prompt
        assert "visualization" in prompt.lower()

    def test_system_prompt_warns_against_dangerous_ops(self, service):
        """System prompt debe advertir contra operaciones peligrosas."""
        schema_context = "Tables: players"
        prompt = service._get_system_prompt(schema_context)
        
        assert "DROP" in prompt or "DELETE" in prompt or "NEVER" in prompt


class TestTextToSQLIntegration:
    """Tests de integración sin mocking."""

    @pytest.fixture
    def service(self):
        """Instancia del servicio."""
        return TextToSQLService(api_key="test-key-mock")

    def test_service_instantiation(self, service):
        """Service debe instanciarse correctamente."""
        assert service is not None
        assert service.model is not None

    def test_validate_sql_safety_with_real_queries(self, service):
        """Validar SQL safety con queries reales."""
        # Query segura
        sql_safe = "SELECT p.name FROM players p WHERE p.team_id = 'real-madrid' ORDER BY p.name DESC LIMIT 10;"
        is_safe, error = service._validate_sql_safety(sql_safe)
        assert is_safe is True
        
        # Query insegura
        sql_unsafe = "DELETE FROM players WHERE 1=1;"
        is_safe, error = service._validate_sql_safety(sql_unsafe)
        assert is_safe is False


class TestTextToSQLComplexQueries:
    """Tests para queries SQL complejas."""

    @pytest.fixture
    def service(self):
        """Instancia del servicio."""
        return TextToSQLService(api_key="test-key-mock")

    def test_validate_complex_join_query(self, service):
        """Validar SELECT con múltiples JOINs."""
        sql = """
            SELECT p.name, t.name as team, g.id as game_id, ps.points
            FROM players p
            JOIN teams t ON p.team_id = t.id
            JOIN player_stats_games ps ON p.id = ps.player_id
            JOIN games g ON ps.game_id = g.id
            WHERE p.name ILIKE 'Larkin'
            ORDER BY ps.points DESC
            LIMIT 10;
        """
        is_safe, error = service._validate_sql_safety(sql)
        assert is_safe is True

    def test_validate_aggregation_query(self, service):
        """Validar SELECT con agregaciones."""
        sql = """
            SELECT t.name, COUNT(p.id) as player_count, AVG(ps.points) as avg_points
            FROM teams t
            LEFT JOIN players p ON t.id = p.team_id
            LEFT JOIN player_stats_games ps ON p.id = ps.player_id
            GROUP BY t.id, t.name
            HAVING COUNT(p.id) > 5
            ORDER BY avg_points DESC;
        """
        is_safe, error = service._validate_sql_safety(sql)
        assert is_safe is True

    def test_validate_subquery(self, service):
        """Validar SELECT con subqueries."""
        sql = """
            SELECT name, team_id
            FROM players
            WHERE team_id IN (
                SELECT id FROM teams WHERE code IN ('RMA', 'BCN', 'AX')
            );
        """
        is_safe, error = service._validate_sql_safety(sql)
        assert is_safe is True

    def test_validate_with_cte(self, service):
        """Validar que CTEs no son permitidas (deben empezar con SELECT)."""
        sql = """
            WITH top_scorers AS (
                SELECT player_id, SUM(points) as total_points
                FROM player_stats_games
                GROUP BY player_id
                ORDER BY total_points DESC
                LIMIT 10
            )
            SELECT p.name, ts.total_points
            FROM top_scorers ts
            JOIN players p ON ts.player_id = p.id;
        """
        is_safe, error = service._validate_sql_safety(sql)
        # CTEs no son permitidas porque no empiezan con SELECT directamente
        assert is_safe is False

    def test_validate_rejects_grant(self, service):
        """GRANT queries deben ser rechazadas."""
        sql = "GRANT SELECT ON players TO public;"
        is_safe, error = service._validate_sql_safety(sql)
        assert is_safe is False

    def test_validate_rejects_revoke(self, service):
        """REVOKE queries deben ser rechazadas."""
        sql = "REVOKE SELECT ON players FROM public;"
        is_safe, error = service._validate_sql_safety(sql)
        assert is_safe is False

    def test_validate_accepts_case_expression(self, service):
        """CASE expressions dentro de SELECT deben ser aceptadas."""
        sql = """
            SELECT name,
                   CASE
                       WHEN team_id = 'RMA' THEN 'Real Madrid'
                       WHEN team_id = 'BCN' THEN 'Barcelona'
                       ELSE 'Otro'
                   END as team_name
            FROM players;
        """
        is_safe, error = service._validate_sql_safety(sql)
        assert is_safe is True

    def test_validate_accepts_window_functions(self, service):
        """Window functions dentro de SELECT deben ser aceptadas."""
        sql = """
            SELECT name, points,
                   ROW_NUMBER() OVER (ORDER BY points DESC) as rank
            FROM players;
        """
        is_safe, error = service._validate_sql_safety(sql)
        assert is_safe is True

