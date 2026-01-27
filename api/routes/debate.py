
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agents.debate_council import DebateCouncil
import json
import asyncio

router = APIRouter()

@router.websocket("/ws/debate/{site_id}")
async def websocket_endpoint(websocket: WebSocket, site_id: str):
    await websocket.accept()
    try:
        # Initialize the debate council
        await websocket.send_json({"type": "status", "content": "Initializing Debate Council..."})
        
        council = DebateCouncil()
        
        await websocket.send_json({
            "type": "status", 
            "content": f"Debate Council Ready. Analyzing {site_id}..."
        })
        
        # Run the debate
        iterator = council.run_debate(site_id)
        
        async for event in iterator:
            speaker = event.get("speaker", "Unknown")
            content = event.get("content", "...")
            msg_type = event.get("type", "message")
            
            # Simple filtering logic
            if speaker == "System" and msg_type == "verdict":
                payload = {
                    "type": "verdict",
                    "speaker": "Owl",
                    "content": content
                }
            elif speaker in ["Hawk", "Dove", "Owl"]:
                payload = {
                    "type": "message",
                    "speaker": speaker,
                    "content": content
                }
            else:
                payload = {
                    "type": "trace",
                    "speaker": speaker,
                    "content": str(content)
                }
            
            await websocket.send_json(payload)
            await asyncio.sleep(0.05)
            
        await websocket.send_json({"type": "status", "content": "Debate Concluded."})
        await websocket.close()
            
    except WebSocketDisconnect:
        print(f"Client disconnected for {site_id}")
    except Exception as e:
        print(f"Error in debate websocket: {e}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
            await websocket.close()
        except:
            pass
