from prefect import flow, task
from prefect.logging import get_run_logger
from loguru import logger
import os
import random

# Marche pô... ne histoire de subprocess avec prefect... la solution est de mettre enqueue=True
# quelque part mais flem.
# logger.add(
#     "/app/logs/app.log", format="{time} | {level} | {message}", level="INFO", rotation="1 MB"
# )

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PREFECT_API_URL","http://127.0.0.1:4200/api")

@task(retries=2, retry_delay_seconds=1)
def check_random(nb):
    logger.info(f"check_random()")
    if nb < 2:
        logger.info(f"nombre inferieur a 0.5")
    else:
        logger.info(f"nombre superieur a 0.5")

@flow
def periodic_check():
    logger.info(f"test()")
    logger.info(f"preiodic_check()")
    check_random(random.uniform(0.0, 5.0))

if __name__ == "__main__":
	periodic_check.serve(
	name="every-10s",
	interval=5
)
