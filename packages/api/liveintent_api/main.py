from fastapi import FastAPI
from liveintent_shared.logging import configure_logging
from .routes import advertisers, publishers, creatives, admin

configure_logging()
app = FastAPI(title="LiveIntent Spy API")
app.include_router(advertisers.router)
app.include_router(publishers.router)
app.include_router(creatives.router)
app.include_router(admin.router)

@app.get("/health")
def health():
    return {"ok": True}
