from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from datetime import datetime, timezone
import psutil

from src.infra.database import get_db
from src.infra.orm.FuncionarioModel import FuncionarioDB

router = APIRouter()


# =========================
# HEALTH BÁSICO
# =========================
@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "comandas-api",
        "version": "1.0.0"
    }


# =========================
# DATABASE
# =========================
@router.get("/health/database", tags=["Health"])
async def database_health():
    db = None
    try:
        db = next(get_db())

        result = db.execute(text("SELECT 1")).fetchone()

        if result and result[0] == 1:
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database query failed"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}"
        )

    finally:
        if db:
            db.close()


# =========================
# DATABASE TABLES
# =========================
@router.get("/health/database/tables", tags=["Health"])
async def database_tables_health():
    db = None
    try:
        db = next(get_db())

        checks = {}

        # Funcionários
        try:
            count = db.query(FuncionarioDB).count()
            checks["funcionarios"] = {
                "status": "healthy",
                "count": count
            }
        except Exception as e:
            checks["funcionarios"] = {
                "status": "error",
                "error": str(e)
            }

        all_healthy = all(c["status"] == "healthy" for c in checks.values())

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "tables": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database tables check failed: {str(e)}"
        )

    finally:
        if db:
            db.close()


# =========================
# SYSTEM
# =========================
@router.get("/health/system", tags=["Health"])
async def system_health():
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        cpu_percent = psutil.cpu_percent(interval=1)

        memory_info = {
            "percent": memory.percent,
            "status": "healthy" if memory.percent < 90 else "warning"
        }

        disk_percent = (disk.used / disk.total) * 100
        disk_info = {
            "percent": disk_percent,
            "status": "healthy" if disk_percent < 90 else "warning"
        }

        cpu_info = {
            "percent": cpu_percent,
            "status": "healthy" if cpu_percent < 80 else "warning"
        }

        all_healthy = all([
            memory_info["status"] == "healthy",
            disk_info["status"] == "healthy",
            cpu_info["status"] == "healthy"
        ])

        return {
            "status": "healthy" if all_healthy else "warning",
            "memory": memory_info,
            "disk": disk_info,
            "cpu": cpu_info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"System health check failed: {str(e)}"
        )


# =========================
# FULL HEALTH
# =========================
@router.get("/health/full", tags=["Health"])
async def full_health_check():
    checks = {}

    # API
    checks["api"] = {"status": "healthy"}

    # DATABASE
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # SYSTEM
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        cpu = psutil.cpu_percent(interval=1)

        system_ok = (
            memory.percent < 90 and
            (disk.used / disk.total) * 100 < 90 and
            cpu < 80
        )

        checks["system"] = {
            "status": "healthy" if system_ok else "warning",
            "memory": memory.percent,
            "disk": (disk.used / disk.total) * 100,
            "cpu": cpu
        }

    except Exception as e:
        checks["system"] = {"status": "error", "error": str(e)}

    # STATUS GERAL
    overall = "healthy"
    for c in checks.values():
        if c["status"] in ["unhealthy", "error"]:
            overall = "unhealthy"
            break
        elif c["status"] == "warning":
            overall = "warning"

    return {
        "status": overall,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# =========================
# READINESS
# =========================
@router.get("/ready", tags=["Health"])
async def readiness_check():
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()

        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


# =========================
# LIVENESS
# =========================
@router.get("/live", tags=["Health"])
async def liveness_check():
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }