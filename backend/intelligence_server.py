from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import os
import json
import asyncio
import aiohttp
import uuid
from datetime import datetime
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]

# Lifespan event handler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    asyncio.create_task(intelligence_monitor())
    print("[START] FastAPI Intelligence Dashboard started")
    print("[CONNECT] WebSocket endpoint: ws://localhost:8001/ws")
    print("[COMM] Connected to scraping service on port 5001")
    
    yield
    
    # Shutdown
    client.close()
    print("[SECURE] FastAPI server shutting down")

# FastAPI app with lifespan
app = FastAPI(title="Omerta Intelligence Dashboard API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.scraping_service_url = "http://localhost:5001"

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn)

manager = ConnectionManager()

# Pydantic Models
class PlayerUpdate(BaseModel):
    player_id: str
    username: str
    data: Dict[str, Any]

class FamilyTargets(BaseModel):
    families: List[str]

class DetectiveTargets(BaseModel):
    usernames: List[str]

class UserPreferences(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    favorite_families: List[str] = []
    detective_targets: List[str] = []
    notification_settings: Dict[str, bool] = {
        "kills": True,
        "shots": True,
        "plating_drops": True,
        "profile_changes": True
    }
    ui_settings: Dict[str, Any] = {
        "theme": "dark",
        "auto_refresh": True,
        "show_dead_players": False
    }

# --- SCRAPING SERVICE COMMUNICATION ---
async def call_scraping_service(endpoint: str, method: str = "GET", data: dict = None):
    """Communicate with Flask scraping service"""
    url = f"{manager.scraping_service_url}{endpoint}"
    try:
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url) as response:
                    return await response.json()
            elif method == "POST":
                async with session.post(url, json=data) as response:
                    return await response.json()
    except Exception as e:
        print(f"Error calling scraping service: {e}")
        return {"error": str(e)}

# --- API ENDPOINTS ---
@api_router.get("/")
async def root():
    return {"message": "Omerta Intelligence Dashboard API", "status": "active"}

@api_router.get("/players")
async def get_all_players():
    """Get all players from scraping service"""
    result = await call_scraping_service("/api/scraping/players")
    if "error" in result:
        raise HTTPException(status_code=503, detail="Scraping service unavailable")
    return result

@api_router.get("/players/{player_id}")
async def get_player_details(player_id: str):
    """Get detailed player information"""
    result = await call_scraping_service(f"/api/scraping/player/{player_id}")
    if "error" in result:
        raise HTTPException(status_code=404, detail="Player data not found")
    return result

@api_router.get("/intelligence/notifications")
async def get_notifications():
    """Get recent intelligence notifications"""
    result = await call_scraping_service("/api/scraping/notifications")
    return result

@api_router.get("/intelligence/tracked-players")
async def get_tracked_players():
    """Get all tracked players with their intelligence data"""
    try:
        # This would normally come from your scraping service
        # For now, let's return mock data that matches the detective targets
        result = await call_scraping_service("/api/scraping/detective/targets")
        if "error" not in result:
            return {"tracked_players": result.get("tracked_players", [])}
        
        # Fallback: get from MongoDB if we have stored tracked players
        tracked = await db.tracked_players.find({"is_active": True}).to_list(length=100)
        tracked_players = []
        
        for player in tracked:
            tracked_players.append({
                "player_id": player.get("player_id"),
                "username": player.get("username"),
                "priority": player.get("priority", 1),
                "kills": player.get("kills", 0),
                "shots": player.get("shots", 0),
                "wealth_level": player.get("wealth_level", 0),
                "plating": player.get("plating", "Unknown")
            })
        
        return {"tracked_players": tracked_players}
    except Exception as e:
        print(f"Error getting tracked players: {e}")
        return {"tracked_players": []}

@api_router.post("/intelligence/detective/add")
async def add_detective_targets(targets: DetectiveTargets):
    """Add players to detective tracking"""
    result = await call_scraping_service("/api/scraping/detective/add", "POST", {"usernames": targets.usernames})
    
    # Broadcast update to connected clients
    await manager.broadcast({
        "type": "detective_targets_updated",
        "data": {
            "added_targets": targets.usernames,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    return result

@api_router.post("/families/set-targets")
async def set_family_targets(targets: FamilyTargets):
    """Set target families for tracking"""
    result = await call_scraping_service("/api/scraping/families/set", "POST", {"families": targets.families})
    
    # Save to MongoDB for persistence
    await db.app_settings.update_one(
        {"setting_type": "family_targets"},
        {"$set": {"families": targets.families, "updated_at": datetime.now()}},
        upsert=True
    )
    
    # Broadcast update
    await manager.broadcast({
        "type": "family_targets_updated",
        "data": {
            "families": targets.families,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    return result

@api_router.get("/families/targets")
async def get_family_targets():
    """Get current family targets"""
    settings = await db.app_settings.find_one({"setting_type": "family_targets"})
    if settings:
        return {"families": settings.get("families", [])}
    return {"families": []}

@api_router.get("/status")
async def get_system_status():
    """Get system-wide status"""
    scraping_status = await call_scraping_service("/api/scraping/status")
    
    # Get MongoDB stats
    mongo_stats = {
        "connected": True,
        "preferences_count": await db.user_preferences.count_documents({})
    }
    
    return {
        "scraping_service": scraping_status,
        "database": mongo_stats,
        "websocket_connections": len(manager.active_connections),
        "api_status": "active"
    }

@api_router.post("/preferences")
async def save_user_preferences(preferences: UserPreferences):
    """Save user preferences"""
    await db.user_preferences.update_one(
        {"user_id": preferences.user_id},
        {"$set": preferences.dict()},
        upsert=True
    )
    return {"message": "Preferences saved successfully"}

@api_router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences"""
    prefs = await db.user_preferences.find_one({"user_id": user_id})
    if prefs:
        return UserPreferences(**prefs)
    else:
        # Return default preferences
        return UserPreferences(user_id=user_id)

# Internal endpoint for scraping service communication
@api_router.post("/internal/list-updated")
async def handle_list_update(update_data: dict):
    """Handle player list update from scraping service"""
    await manager.broadcast({
        "type": "player_list_updated",
        "data": update_data
    })
    return {"status": "broadcasted"}

@api_router.post("/internal/notification")
async def handle_intelligence_notification(notification: dict):
    """Handle intelligence notification from scraping service"""
    await manager.broadcast({
        "type": "intelligence_notification",
        "data": notification
    })
    return {"status": "broadcasted"}

# Include router
app.include_router(api_router)

# --- WEBSOCKET ENDPOINT ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types from frontend
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            elif message.get("type") == "request_status":
                status = await call_scraping_service("/api/scraping/status")
                await websocket.send_json({"type": "status_update", "data": status})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- BACKGROUND TASKS ---
async def intelligence_monitor():
    """Background task to monitor scraping service for real-time updates"""
    while True:
        try:
            # Get recent notifications from scraping service
            notifications = await call_scraping_service("/api/scraping/notifications")
            
            if notifications and "notifications" in notifications:
                recent_notifications = notifications["notifications"][:5]  # Last 5 notifications
                
                # Broadcast to all connected clients
                await manager.broadcast({
                    "type": "intelligence_update",
                    "data": {
                        "notifications": recent_notifications,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
        except Exception as e:
            print(f"Error in intelligence monitor: {e}")
        
        await asyncio.sleep(10)  # Check every 10 seconds

# This duplicate was removed - lifespan is now defined above

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)