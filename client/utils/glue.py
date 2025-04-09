import asyncio

async def interruptible_sleep(running, duration):
    """
    Custom sleep that checks for shutdown signal and interrupts if necessary.
    """
    step = 1  # Sleep in 1-second intervals
    for _ in range(duration):
        if not running:
            break  # Stop sleeping if shutdown signal received
        await asyncio.sleep(step)