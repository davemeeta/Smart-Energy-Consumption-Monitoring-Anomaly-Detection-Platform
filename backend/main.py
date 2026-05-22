from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio, threading, json
from mqtt_listener import start_listener, latest_events

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    t = threading.Thread(target=start_listener, daemon=True)
    t.start()
    yield
    # Shutdown (add cleanup here if needed)

app = FastAPI(title="Energy Anomaly API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/events")
def get_events(limit: int = 50):
    return latest_events[-limit:]

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    last_len = 0
    try:
        while True:
            if len(latest_events) > last_len:
                for event in latest_events[last_len:]:
                    await ws.send_text(json.dumps(event))
                last_len = len(latest_events)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass