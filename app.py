import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import Config
from logger import setup_logger
import os

app = FastAPI(title="Polymarket Trading Bot Dashboard")
logger = setup_logger("DASHBOARD")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

config = Config()

bot_states = {
    'BTC': {'running': False, 'connected': False, 'current_price': None, 'closing_price': None, 'contract_price': None, 'gap': None, 'decision': 'WAIT', 'events': []},
    'ETH': {'running': False, 'connected': False, 'current_price': None, 'closing_price': None, 'contract_price': None, 'gap': None, 'decision': 'WAIT', 'events': []}
}

dynamic_config = {
    'BTC_PRICE_GAP': config.BTC_PRICE_GAP,
    'ETH_PRICE_GAP': config.ETH_PRICE_GAP,
    'BTC_BUY_PRICE': config.BTC_BUY_PRICE,
    'ETH_BUY_PRICE': config.ETH_BUY_PRICE,
    'PROXY_URL': config.PROXY_URL,
}

active_connections: List[WebSocket] = []

class ConfigUpdate(BaseModel):
    btc_price_gap: Optional[float] = None
    eth_price_gap: Optional[float] = None
    btc_buy_price: Optional[float] = None
    eth_buy_price: Optional[float] = None
    proxy_url: Optional[str] = None

@app.get("/")
async def root():
    return FileResponse('templates/index.html')

@app.get("/api/status")
async def get_status():
    return {'timestamp': datetime.now().isoformat(), 'btc': bot_states['BTC'], 'eth': bot_states['ETH'], 'config': dynamic_config}

@app.post("/api/config/update")
async def update_config(config_update: ConfigUpdate):
    if config_update.btc_price_gap is not None:
        dynamic_config['BTC_PRICE_GAP'] = config_update.btc_price_gap
    if config_update.eth_price_gap is not None:
        dynamic_config['ETH_PRICE_GAP'] = config_update.eth_price_gap
    if config_update.btc_buy_price is not None:
        dynamic_config['BTC_BUY_PRICE'] = config_update.btc_buy_price
    if config_update.eth_buy_price is not None:
        dynamic_config['ETH_BUY_PRICE'] = config_update.eth_buy_price
    if config_update.proxy_url is not None:
        dynamic_config['PROXY_URL'] = config_update.proxy_url
        logger.info(f"Proxy updated: {config_update.proxy_url}")
    
    return {'status': 'success', 'config': dynamic_config}

@app.post("/api/bots/start")
async def start_bots():
    bot_states['BTC']['running'] = True
    bot_states['ETH']['running'] = True
    return {'status': 'success'}

@app.post("/api/bots/stop")
async def stop_bots():
    bot_states['BTC']['running'] = False
    bot_states['ETH']['running'] = False
    return {'status': 'success'}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    await websocket.send_json({'type': 'initial', 'data': {'btc': bot_states['BTC'], 'eth': bot_states['ETH'], 'config': dynamic_config}})
    try:
        while True:
            data = await websocket.receive_text()
    except:
        active_connections.remove(websocket)

@app.on_event("startup")
async def startup_event():
    logger.info("Dashboard started on http://localhost:8000")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)