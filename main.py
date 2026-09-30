from fastapi import FastAPI
from routers.devices import router as devices_router
from routers.chat import router as chat_router
app=FastAPI(
    title="PIS AI Assistant",
    version="0.1.0"
)

app.include_router(devices_router)
app.include_router(chat_router)

@app.get("/")
async def health():
    return {
        "status": "healthy"
    }