#!/usr/bin/env python3
"""
Script de verificación del setup de la Fase 0
"""
import os
import sys
from pathlib import Path

def check_exists(path, description):
    """Verifica si existe un archivo o directorio"""
    exists = Path(path).exists()
    status = "[OK]" if exists else "[FALTA]"
    print(f"{status} {description}: {path}")
    return exists

def main():
    print("=" * 60)
    print("VERIFICACIÓN DEL SETUP - FASE 0")
    print("=" * 60)
    print()
    
    all_good = True
    
    # Backend
    print("BACKEND:")
    all_good &= check_exists("backend/pyproject.toml", "Poetry config")
    all_good &= check_exists("backend/poetry.lock", "Poetry lock")
    all_good &= check_exists("backend/app/main.py", "FastAPI main")
    all_good &= check_exists("backend/app/config.py", "Config")
    all_good &= check_exists("backend/app/database.py", "Database")
    all_good &= check_exists("backend/app/routers/health.py", "Health router")
    all_good &= check_exists("backend/app/routers/chat.py", "Chat router")
    all_good &= check_exists("backend/tests/conftest.py", "Pytest config")
    all_good &= check_exists("backend/.env.example", "Env example")
    print()
    
    # Frontend
    print("FRONTEND:")
    all_good &= check_exists("frontend/package.json", "Package.json")
    all_good &= check_exists("frontend/tsconfig.json", "TypeScript config")
    all_good &= check_exists("frontend/next.config.js", "Next.js config")
    all_good &= check_exists("frontend/tailwind.config.ts", "Tailwind config")
    all_good &= check_exists("frontend/app/layout.tsx", "Layout")
    all_good &= check_exists("frontend/app/page.tsx", "Home page")
    all_good &= check_exists("frontend/lib/utils.ts", "Utils")
    all_good &= check_exists("frontend/.env.local.example", "Env example")
    print()
    
    # GitHub Actions
    print("GITHUB ACTIONS:")
    all_good &= check_exists(".github/workflows/ci.yml", "CI workflow")
    all_good &= check_exists(".github/workflows/etl_daily.yml", "ETL workflow")
    print()
    
    # Otros
    print("OTROS:")
    all_good &= check_exists(".gitignore", "Gitignore")
    all_good &= check_exists("data/.gitkeep", "Data directory")
    all_good &= check_exists("SETUP_STATUS.md", "Setup status")
    print()
    
    print("=" * 60)
    if all_good:
        print("[OK] TODOS LOS ARCHIVOS VERIFICADOS CORRECTAMENTE")
        print()
        print("PROXIMOS PASOS:")
        print("1. Instalar Node.js 18+ desde https://nodejs.org/")
        print("2. cd frontend && npm install")
        print("3. Configurar .env en backend/ con DATABASE_URL y OPENAI_API_KEY")
        print("4. cd backend && poetry run uvicorn app.main:app --reload")
        return 0
    else:
        print("[ERROR] ALGUNOS ARCHIVOS FALTAN")
        return 1

if __name__ == "__main__":
    sys.exit(main())

