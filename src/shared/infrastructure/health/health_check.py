"""
Health check service.
Provides detailed health checks for all system components.
"""

# Standard library
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Local application
from src.shared.infrastructure.config.settings import Settings
from src.shared.infrastructure.logging.structured_logger import get_logger

logger = get_logger(__name__)


class HealthCheckService:
    """Service for checking health of application components"""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def check_all(self) -> dict[str, Any]:
        """
        Run all health checks and return status.

        Returns:
            dict with overall status and individual component checks
        """
        checks = {
            "database": self._check_database(),
            "ai_providers": await self._check_ai_providers(),
            "disk_space": self._check_disk_space(),
            "memory_store": self._check_memory_store(),
        }

        all_healthy = all(check["healthy"] for check in checks.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "service": "mimo",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": checks,
        }

    def _check_database(self) -> dict[str, Any]:
        """Check database connectivity (PostgreSQL or SQLite with fallback)"""
        try:
            if self.settings.is_postgres:
                # Try PostgreSQL first (lazy import)
                try:
                    import psycopg2

                    conn = psycopg2.connect(self.settings.database_url)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM recommendation_usage")
                    count = cursor.fetchone()[0]
                    conn.close()

                    return {
                        "healthy": True,
                        "message": f"PostgreSQL OK ({count} usage records)",
                    }
                except ImportError:
                    # Fallback to SQLite when psycopg2 not available
                    db_path = Path("/tmp/recommendations.db")

                    if not db_path.exists():
                        return {
                            "healthy": False,
                            "message": "SQLite fallback file does not exist",
                        }

                    conn = sqlite3.connect(str(db_path), timeout=5.0)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM recommendation_usage")
                    count = cursor.fetchone()[0]
                    conn.close()

                    return {
                        "healthy": True,
                        "message": f"SQLite OK (fallback, {count} usage records)",
                    }
            else:
                # SQLite check
                db_path = Path(self.settings.database_url.replace("sqlite:///", ""))

                if not db_path.exists():
                    return {
                        "healthy": False,
                        "message": "Database file does not exist",
                    }

                conn = sqlite3.connect(str(db_path), timeout=5.0)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM recommendation_usage")
                count = cursor.fetchone()[0]
                conn.close()

                return {
                    "healthy": True,
                    "message": f"SQLite OK ({count} usage records)",
                }
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "healthy": False,
                "message": f"Database error: {str(e)}",
            }

    async def _check_ai_providers(self) -> dict[str, Any]:
        """Check AI provider availability"""
        providers = {}

        if self.settings.has_anthropic_configured():
            providers["anthropic"] = "configured"

        if self.settings.has_deepseek_configured():
            providers["deepseek"] = "configured"

        if self.settings.has_gemini_configured():
            providers["gemini"] = "configured"

        if self.settings.has_openai_configured():
            providers["openai"] = "configured"

        has_providers = len(providers) > 0

        return {
            "healthy": has_providers,
            "message": f"{len(providers)} AI provider(s) configured",
            "providers": providers,
        }

    def _check_disk_space(self) -> dict[str, Any]:
        """Check available disk space"""
        try:
            import shutil

            # Check workspace directory
            total, used, free = shutil.disk_usage(".")

            free_gb = free / (1024**3)
            used_percent = (used / total) * 100

            # Warn if less than 1GB free or more than 90% used
            healthy = free_gb > 1.0 and used_percent < 90

            return {
                "healthy": healthy,
                "message": f"{free_gb:.2f} GB free ({used_percent:.1f}% used)",
                "free_gb": round(free_gb, 2),
                "used_percent": round(used_percent, 1),
            }
        except Exception as e:
            logger.error("Disk space check failed", error=str(e))
            return {
                "healthy": False,
                "message": f"Disk check error: {str(e)}",
            }

    def _check_memory_store(self) -> dict[str, Any]:
        """Check memory store directory health"""
        try:
            memory_dir = Path("memory")

            if not memory_dir.exists():
                return {
                    "healthy": True,
                    "message": "Memory store not yet initialized",
                }

            # Count user directories and files
            user_dirs = [d for d in memory_dir.iterdir() if d.is_dir()]
            total_files = sum(1 for d in user_dirs for _ in d.iterdir())

            return {
                "healthy": True,
                "message": f"{len(user_dirs)} users, {total_files} files",
                "user_count": len(user_dirs),
                "file_count": total_files,
            }
        except Exception as e:
            logger.error("Memory store check failed", error=str(e))
            return {
                "healthy": False,
                "message": f"Memory store error: {str(e)}",
            }
