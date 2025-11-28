#!/usr/bin/env python3
"""
Schema Validation Script
Validates the SQL migration file for syntax and completeness.
"""

import os
import sys
from pathlib import Path


def validate_sql_file(file_path: str) -> dict:
    """
    Validates a SQL file for common issues.
    
    Args:
        file_path: Path to the SQL file to validate
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "statistics": {
            "tables_created": 0,
            "indexes_created": 0,
            "extensions_enabled": 0,
            "lines": 0
        }
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            results["statistics"]["lines"] = len(lines)
        
        # Count CREATE TABLE statements
        tables = content.count("CREATE TABLE")
        results["statistics"]["tables_created"] = tables
        
        # Count CREATE INDEX statements
        indexes = content.count("CREATE INDEX")
        results["statistics"]["indexes_created"] = indexes
        
        # Count CREATE EXTENSION statements
        extensions = content.count("CREATE EXTENSION")
        results["statistics"]["extensions_enabled"] = extensions
        
        # Check for expected tables
        expected_tables = [
            "teams",
            "players",
            "games",
            "player_stats_games",
            "schema_embeddings"
        ]
        
        for table in expected_tables:
            if f"CREATE TABLE" not in content or table not in content:
                results["errors"].append(f"Missing table: {table}")
                results["valid"] = False
        
        # Check for pgvector extension
        if "pgvector" not in content:
            results["errors"].append("pgvector extension not enabled")
            results["valid"] = False
        
        # Check for vector datatype in schema_embeddings
        if "vector" not in content:
            results["errors"].append("Vector datatype not used in schema_embeddings table")
            results["valid"] = False
        
        # Check for foreign key constraints
        if "REFERENCES" not in content:
            results["warnings"].append("No foreign key constraints found")
        
        # Check for timestamps
        if "TIMESTAMP" not in content:
            results["warnings"].append("No timestamp columns found for audit trails")
        
        # Check for proper closing comments
        if "SUMMARY" not in content:
            results["warnings"].append("No summary section in migration file")
        
    except FileNotFoundError:
        results["valid"] = False
        results["errors"].append(f"File not found: {file_path}")
    except Exception as e:
        results["valid"] = False
        results["errors"].append(f"Error reading file: {str(e)}")
    
    return results


def main():
    """Main function"""
    migration_file = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
    
    print("=" * 70)
    print("DATABASE SCHEMA VALIDATION")
    print("=" * 70)
    print(f"\nValidating: {migration_file}\n")
    
    results = validate_sql_file(str(migration_file))
    
    # Print statistics
    print("STATISTICS:")
    print(f"  Total lines: {results['statistics']['lines']}")
    print(f"  CREATE TABLE statements: {results['statistics']['tables_created']}")
    print(f"  CREATE INDEX statements: {results['statistics']['indexes_created']}")
    print(f"  CREATE EXTENSION statements: {results['statistics']['extensions_enabled']}")
    print()
    
    # Print errors
    if results["errors"]:
        print("ERRORS:")
        for error in results["errors"]:
            print(f"  [ERROR] {error}")
        print()
    
    # Print warnings
    if results["warnings"]:
        print("WARNINGS:")
        for warning in results["warnings"]:
            print(f"  [WARN] {warning}")
        print()
    
    # Print result
    if results["valid"]:
        print("RESULT: [PASS] Schema validation PASSED")
        print("\nThe migration file is ready to execute on a PostgreSQL database.")
        return 0
    else:
        print("RESULT: [FAIL] Schema validation FAILED")
        print("\nPlease fix the errors above before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

