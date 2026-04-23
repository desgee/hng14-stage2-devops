import logging
import os
import signal
import time

import redis
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

# Graceful shutdown: flip this flag on SIGTERM / SIGINT so the
# current job can finish before the process exits.
running = True


def handle_signal(sig, frame):
    global running
    logger.info("Shutdown signal received — finishing current job then stopping.")
    running = False


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def process_job(job_id: str) -> None:
    try:
        logger.info(f"Processing job {job_id}")
        time.sleep(2)  # simulate work
        r.hset(f"job:{job_id}", "status", "completed")
        logger.info(f"Completed job {job_id}")
    except Exception as e:
        logger.error(f"Failed to process job {job_id}: {e}")
        # Mark job as failed so clients don't wait indefinitely
        try:
            r.hset(f"job:{job_id}", "status", "failed")
        except Exception as redis_err:
            logger.error(f"Could not update job {job_id} status to failed: {redis_err}")


while running:
    job = r.brpop("job", timeout=5)
    if job:
        _, job_id = job
        process_job(job_id)

logger.info("Worker shut down cleanly.")
