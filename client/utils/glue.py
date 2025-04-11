import asyncio

async def interruptible_sleep(running_event, duration):
    """
    Custom sleep that checks for shutdown signal and interrupts if necessary.
    """
    step = 1  # Sleep in 1-second intervals
    for _ in range(duration):
        if not running_event.is_set():
            break  # Stop sleeping if shutdown signal received
        await asyncio.sleep(step)