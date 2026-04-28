from fastapi import FastAPI
from liveintent_shared.logging import configure_logging

configure_logging()
app = FastAPI(title="LiveIntent Spy API")

@app.get("/health")
def health():
    return {"ok": True}
