import time
import asyncio
from src.utils.logger import get_logger

log = get_logger("throttler")

async def quota_cooldown():
    """Mandatory pause to reset Groq Tokens Per Minute (TPM)."""
    wait_time = 65
    log.warning(f"Quota safety triggered. Cooling down for {wait_time}s...")
    await asyncio.sleep(wait_time)
    log.info("Cooldown complete. Resuming pipeline.")