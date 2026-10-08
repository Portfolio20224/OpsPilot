import logging
import time
from contextlib import contextmanager
from uuid import uuid4


logger = logging.getLogger("opspilot")


def generate_request_id() -> str:
    return str(uuid4())


@contextmanager
def measure_operation(operation: str, request_id: str):
    start = time.perf_counter()

    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "operation=%s request_id=%s duration_ms=%.2f",
            operation,
            request_id,
            duration_ms,
        )