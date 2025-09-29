import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/realtime"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server\n")

            # Receive welcome message
            response = await websocket.recv()
            welcome = json.loads(response)
            print(f"📌 Welcome message received:")
            print(f"   Type: {welcome.get('type')}")
            print(f"   Message: {welcome.get('message')}\n")

            # Test cases for grammar and spelling
            test_cases = [
                "What France is capital?",  # Should correct to "What is the capital of France?"
                "This are wrong.",          # Should correct to "This is wrong."
                "I goes to school.",        # Should correct to "I go to school."
                "The cat are sleeping.",    # Should correct to "The cat is sleeping."
                "teh quik brown fox",       # Spelling errors
                "She don't has no idea what is the problem, the documents was not being file correctly, and him and me goes to court but not knowed the rules."
            ]

            for i, test_text in enumerate(test_cases, 1):
                print(f"Test {i}: '{test_text}'")
                
                # Send test message
                test_message = {
                    "type": "text_input",
                    "text": test_text
                }
                await websocket.send(json.dumps(test_message))
                print(f"📤 Sent: {test_text}")

                # Receive and parse response
                response = await websocket.recv()
                result = json.loads(response)
                
                # Display results nicely
                if result.get("type") == "analysis_result":
                    print(f"📥 Analysis Result:")
                    
                    # Show grammar corrections if any
                    if result.get("grammar_check"):
                        grammar = result["grammar_check"]
                        print(f"   ✏️ Grammar Correction:")
                        print(f"      Original:  '{grammar.get('original')}'")
                        print(f"      Corrected: '{grammar.get('corrected')}'")
                        print(f"      Changed:   {grammar.get('has_changes')}")
                    
                    # Show spelling suggestions if any
                    if result.get("spelling_suggestions"):
                        print(f"   📖 Spelling Suggestions:")
                        for word, suggestions in result["spelling_suggestions"].items():
                            print(f"      '{word}' → {suggestions}")
                    
                    # Show metrics
                    print(f"   📊 Metrics:")
                    print(f"      Processing time: {result.get('processing_time_ms')}ms")
                    print(f"      Word count: {result.get('word_count')}")
                    print(f"      Character count: {result.get('character_count')}")
                else:
                    print(f"   Response: {result}")
                
                print("-" * 50 + "\n")
                
                # Small delay between tests
                await asyncio.sleep(0.5)

            # Test ping-pong
            print("Testing ping-pong mechanism:")
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping")

            # Receive pong with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                pong = json.loads(response)
                if pong.get("type") == "pong":
                    print(f"📥 Received pong successfully\n")
                else:
                    print(f"📥 Received: {pong}\n")
            except asyncio.TimeoutError:
                print("⏱️ Timeout waiting for pong\n")

            print("✅ All tests completed successfully!")

    except websockets.exceptions.ConnectionRefused:
        print("❌ Error: Could not connect to WebSocket server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_single_message():
    """Simplified test for a single message"""
    uri = "ws://localhost:8000/ws/realtime"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")
        
        # Skip welcome message
        await websocket.recv()
        
        # Send your specific test
        test_message = {
            "type": "text_input",
            "text": "What France is capital?"
        }
        await websocket.send(json.dumps(test_message))
        
        # Get response
        response = await websocket.recv()
        result = json.loads(response)
        
        # Pretty print the result
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    print("🚀 Starting WebSocket test...\n")
    
    # Run the comprehensive test
    asyncio.run(test_websocket())
    
    # Or run just a single test
    # asyncio.run(test_single_message())