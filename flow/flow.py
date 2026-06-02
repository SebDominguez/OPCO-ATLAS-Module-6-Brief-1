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

def check_random_failed(task, task_run, state):
    logger.error(f"La task {task.name} a foiré après {task_run.run_count} retries. Raison : {state.message}")

@task(retries=2, retry_delay_seconds=1, on_failure=[check_random_failed])
def check_random(nb: float) -> None:
    logger.info(f"check_random({nb:.3f})")
    if nb < 0.5:
        logger.info("nombre inférieur à 0.5")
        raise ValueError(f"Alerte : nb trop petit : {nb}")   # ça, ça déclenche le hook on_failure apres 2 retries
    else:
        logger.info("nombre supérieur ou égal à 0.5")

@flow
def periodic_check():
    logger.info("periodic_check()")
    check_random(random.uniform(0.0, 1.0))

if __name__ == "__main__":
    periodic_check.serve(
        name="every-10s",
        interval=5
    )
