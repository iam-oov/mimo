"""
Memory cleanup service for multi-agent conversations.

Automatically removes old conversation data (FAISS indices and metadata)
to prevent filesystem bloat and ensure compliance with data retention policies.
"""

import asyncio
from datetime import datetime, timedelta, UTC
from pathlib import Path

from src.shared.infrastructure.logging.structured_logger import get_logger

logger = get_logger(__name__)


async def cleanup_old_conversations(
    memory_dir: Path | str = Path("memory"),
    max_age_days: int = 7,
) -> dict[str, int]:
    """
    Remove conversation files older than max_age_days.

    Deletes FAISS indices and metadata JSON files for conversations that haven't
    been accessed in the specified number of days. Cleans up empty user directories.

    Args:
        memory_dir: Base directory containing user conversation data
        max_age_days: Maximum age in days before deletion (default: 7)

    Returns:
        Dictionary with cleanup statistics:
        - removed_files: Number of files deleted
        - removed_dirs: Number of empty directories removed
        - total_size_freed_mb: Approximate MB freed

    Example:
        >>> stats = await cleanup_old_conversations(max_age_days=7)
        >>> print(f"Freed {stats['total_size_freed_mb']} MB")
    """
    if isinstance(memory_dir, str):
        memory_dir = Path(memory_dir)

    if not memory_dir.exists():
        logger.info(
            "Memory directory does not exist, skipping cleanup",
            path=str(memory_dir),
        )
        return {"removed_files": 0, "removed_dirs": 0, "total_size_freed_mb": 0.0}

    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    removed_files = 0
    removed_dirs = 0
    total_size_freed = 0

    logger.info(
        "Starting memory cleanup",
        memory_dir=str(memory_dir),
        max_age_days=max_age_days,
        cutoff_date=cutoff.isoformat(),
    )

    # Iterate through user directories
    for user_dir in memory_dir.iterdir():
        if not user_dir.is_dir() or user_dir.name.startswith("."):
            continue

        user_id = user_dir.name
        user_removed_files = 0
        user_size_freed = 0

        # Check all files in user directory
        for file in user_dir.iterdir():
            if file.is_file():
                # Get file modification time
                file_mtime = datetime.fromtimestamp(file.stat().st_mtime, tz=UTC)

                if file_mtime < cutoff:
                    try:
                        file_size = file.stat().st_size
                        file.unlink()
                        removed_files += 1
                        user_removed_files += 1
                        total_size_freed += file_size

                        logger.debug(
                            "Removed old file",
                            user_id=user_id,
                            file_name=file.name,
                            age_days=(datetime.now(UTC) - file_mtime).days,
                            size_bytes=file_size,
                        )
                    except Exception as e:
                        logger.error(
                            "Failed to remove file",
                            user_id=user_id,
                            file_name=file.name,
                            error=str(e),
                        )

        # Log per-user cleanup
        if user_removed_files > 0:
            logger.info(
                "Cleaned up user directory",
                user_id=user_id,
                removed_files=user_removed_files,
                size_freed_kb=round(user_size_freed / 1024, 2),
            )

        # Remove empty directories
        if not any(user_dir.iterdir()):
            try:
                user_dir.rmdir()
                removed_dirs += 1
                logger.debug(
                    "Removed empty user directory",
                    user_id=user_id,
                )
            except Exception as e:
                logger.error(
                    "Failed to remove empty directory",
                    user_id=user_id,
                    error=str(e),
                )

    total_size_freed_mb = round(total_size_freed / (1024 * 1024), 2)

    logger.info(
        "✅ Memory cleanup completed",
        removed_files=removed_files,
        removed_dirs=removed_dirs,
        total_size_freed_mb=total_size_freed_mb,
    )

    return {
        "removed_files": removed_files,
        "removed_dirs": removed_dirs,
        "total_size_freed_mb": total_size_freed_mb,
    }


async def periodic_cleanup(
    memory_dir: Path | str = Path("memory"),
    max_age_days: int = 7,
    interval_hours: int = 24,
) -> None:
    """
    Run cleanup task periodically in background.

    This is a long-running coroutine that should be started as an asyncio task
    in the application lifespan. It will run cleanup at the specified interval.

    Args:
        memory_dir: Base directory containing user conversation data
        max_age_days: Maximum age in days before deletion (default: 7)
        interval_hours: Hours between cleanup runs (default: 24)

    Example:
        >>> @asynccontextmanager
        >>> async def lifespan(app: FastAPI):
        >>>     cleanup_task = asyncio.create_task(periodic_cleanup())
        >>>     yield
        >>>     cleanup_task.cancel()
    """
    logger.info(
        "🧹 Starting periodic memory cleanup task",
        interval_hours=interval_hours,
        max_age_days=max_age_days,
    )

    while True:
        try:
            await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            logger.info("Running scheduled memory cleanup")
            stats = await cleanup_old_conversations(memory_dir, max_age_days)

            if stats["removed_files"] > 0:
                logger.info(
                    "📊 Cleanup stats",
                    removed_files=stats["removed_files"],
                    removed_dirs=stats["removed_dirs"],
                    freed_mb=stats["total_size_freed_mb"],
                )
            else:
                logger.debug("No files to cleanup")

        except asyncio.CancelledError:
            logger.info("🛑 Periodic cleanup task cancelled")
            raise
        except Exception as e:
            logger.error(
                "❌ Error in periodic cleanup",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Continue running even if one cleanup fails
            continue
