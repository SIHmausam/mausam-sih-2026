from fastapi import FastAPI

app = FastAPI(
    title="Mausam SIH 2026 API",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "Mausam backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}