import asyncio
import structlog
from liveintent_shared.config import get_settings
from liveintent_shared.db import session_scope
from liveintent_shared.logging import configure_logging
from .jobs import classify_pending_advertisers, ocr_pending_creatives, retry_unresolved_creatives

log = structlog.get_logger(__name__)

async def run_forever():
    settings = get_settings()
    while True:
        try:
            with session_scope() as s:
                n_class = classify_pending_advertisers(s, limit=20)
                n_ocr = ocr_pending_creatives(s, limit=50)
                n_retry = retry_unresolved_creatives(s, limit=50)
            if n_class or n_ocr or n_retry:
                log.info("enrichment.iteration", classified=n_class, ocred=n_ocr, retried=n_retry)
        except Exception as e:
            log.exception("enrichment.iteration_failed", error=str(e))
        await asyncio.sleep(settings.enrichment_poll_interval_seconds)

def main():
    configure_logging()
    asyncio.run(run_forever())

if __name__ == "__main__":
    main()
