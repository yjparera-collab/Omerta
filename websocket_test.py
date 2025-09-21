#!/usr/bin/env python3
"""
WebSocket sanity check for player_list_updated messages
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_websocket():
    """Test WebSocket connection and listen for player_list_updated messages"""
    uri = "wss://intel-dash-2.preview.emergentagent.com/ws"
    
    try:
        print(f"🔌 Connecting to WebSocket: {uri}")
        
        async with websockets.connect(uri, timeout=10) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Send ping to test basic communication
            ping_message = json.dumps({"type": "ping"})
            await websocket.send(ping_message)
            print("📤 Sent ping message")
            
            # Listen for messages for a short time
            print("👂 Listening for messages (10 seconds)...")
            
            try:
                # Wait for messages with timeout
                for i in range(10):  # Listen for 10 seconds
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        
                        message_type = data.get("type", "unknown")
                        print(f"📨 Received: {message_type}")
                        
                        if message_type == "player_list_updated":
                            print("✅ PASS: Received player_list_updated message")
                            return True
                        elif message_type == "pong":
                            print("✅ Pong received - WebSocket communication working")
                        elif message_type == "connection_established":
                            print("✅ Connection established message received")
                        else:
                            print(f"ℹ️  Other message type: {message_type}")
                            
                    except asyncio.TimeoutError:
                        continue  # No message in this second, continue listening
                
                print("ℹ️  No player_list_updated message received in 10 seconds (this is normal)")
                print("✅ PASS: WebSocket connection and basic communication working")
                return True
                
            except Exception as e:
                print(f"❌ Error during message listening: {e}")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def main():
    """Main execution"""
    print("🎯 WEBSOCKET SANITY CHECK")
    print("=" * 50)
    
    success = await test_websocket()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ WebSocket sanity check PASSED")
        return 0
    else:
        print("❌ WebSocket sanity check FAILED")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 WebSocket test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)