#!/usr/bin/env python3
"""
WebSocket Test for Debate Council
"""
import asyncio
import websockets
import json

async def test_debate_websocket():
    uri = "ws://127.0.0.1:8000/api/debate/ws/debate/Site 2"
    
    print("=" * 60)
    print("🔌 Testing Debate Council WebSocket")
    print("=" * 60)
    print(f"\n📡 Connecting to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!\n")
            print("-" * 60)
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    data = json.loads(message)
                    
                    msg_type = data.get("type", "unknown")
                    speaker = data.get("speaker", "System")
                    content = data.get("content", "")
                    
                    # Format output based on type
                    if msg_type == "status":
                        print(f"📋 STATUS: {content}")
                    elif msg_type == "message":
                        icon = {"Hawk": "🦅", "Dove": "🕊️", "Owl": "🦉"}.get(speaker, "💬")
                        print(f"\n{icon} [{speaker}]:")
                        print(f"   {content[:300]}{'...' if len(content) > 300 else ''}")
                    elif msg_type == "verdict":
                        print(f"\n📜 VERDICT from {speaker}:")
                        print(f"   {content}")
                    elif msg_type == "error":
                        print(f"\n❌ ERROR: {content}")
                    else:
                        print(f"\n🔧 {msg_type.upper()}: {content[:200]}")
                        
                except asyncio.TimeoutError:
                    print("\n⏰ Timeout waiting for response")
                    break
                    
    except websockets.exceptions.ConnectionClosed:
        print("\n🔌 Connection closed by server")
    except ConnectionRefusedError:
        print("\n❌ Connection refused - is the server running?")
        print("   Run: uvicorn api.main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    print("\n" + "=" * 60)
    print("🏁 Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_debate_websocket())
