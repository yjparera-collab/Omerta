#!/usr/bin/env python3
"""
Omerta Intelligence Dashboard Backend API Testing
Tests all FastAPI endpoints and WebSocket functionality
"""

import requests
import json
import sys
import asyncio
import websockets
from datetime import datetime
import time

class OmertaIntelligenceAPITester:
    def __init__(self, base_url="https://intel-dash-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.ws_url = base_url.replace('https', 'wss') + '/ws'
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data
        })

    def test_api_endpoint(self, name, endpoint, method='GET', data=None, expected_status=200):
        """Test a single API endpoint"""
        url = f"{self.api_base}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    self.log_test(name, True, f"Status: {response.status_code}", response_data)
                    return True, response_data
                except:
                    self.log_test(name, True, f"Status: {response.status_code} (No JSON)")
                    return True, {}
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, {}
                
        except requests.exceptions.RequestException as e:
            self.log_test(name, False, f"Request failed: {str(e)}")
            return False, {}

    async def test_websocket_connection(self):
        """Test WebSocket connection and basic communication"""
        try:
            print(f"\n🔌 Testing WebSocket connection to {self.ws_url}")
            
            async with websockets.connect(self.ws_url, timeout=10) as websocket:
                # Test ping-pong
                ping_message = json.dumps({"type": "ping"})
                await websocket.send(ping_message)
                
                # Wait for pong response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                message = json.loads(response)
                
                if message.get("type") == "pong":
                    self.log_test("WebSocket Ping-Pong", True, "Successfully received pong response")
                    
                    # Test status request
                    status_request = json.dumps({"type": "request_status"})
                    await websocket.send(status_request)
                    
                    # Wait for status response
                    try:
                        status_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        status_message = json.loads(status_response)
                        
                        if status_message.get("type") == "status_update":
                            self.log_test("WebSocket Status Request", True, "Received status update")
                        else:
                            self.log_test("WebSocket Status Request", False, "Unexpected response type")
                    except asyncio.TimeoutError:
                        self.log_test("WebSocket Status Request", False, "Timeout waiting for status response")
                        
                else:
                    self.log_test("WebSocket Ping-Pong", False, f"Expected pong, got {message.get('type')}")
                    
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Connection failed: {str(e)}")

    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🎯 OMERTA INTELLIGENCE DASHBOARD API TESTING")
        print("=" * 60)
        
        # Test basic API health
        print("\n📡 Testing Core API Endpoints...")
        self.test_api_endpoint("API Root", "/")
        self.test_api_endpoint("System Status", "/status")
        
        # Test player endpoints
        print("\n👥 Testing Player Endpoints...")
        success, players_data = self.test_api_endpoint("Get All Players", "/players", expected_status=503)  # Expected to fail without scraping service
        self.test_api_endpoint("Get Player Details", "/players/test123", expected_status=404)  # Expected to fail
        
        # Test intelligence endpoints
        print("\n🚨 Testing Intelligence Endpoints...")
        self.test_api_endpoint("Get Notifications", "/intelligence/notifications")
        
        # Test detective targets
        print("\n🕵️ Testing Detective Target Management...")
        detective_data = {"usernames": ["TestPlayer1", "TestPlayer2"]}
        self.test_api_endpoint("Add Detective Targets", "/intelligence/detective/add", "POST", detective_data, expected_status=503)  # Expected to fail without scraping service
        
        # Test family targets
        print("\n🎯 Testing Family Target Management...")
        family_data = {"families": ["TestFamily1", "TestFamily2"]}
        self.test_api_endpoint("Set Family Targets", "/families/set-targets", "POST", family_data)
        self.test_api_endpoint("Get Family Targets", "/families/targets")
        
        # Test user preferences
        print("\n⚙️ Testing User Preferences...")
        test_user_id = f"test_user_{int(time.time())}"
        preferences_data = {
            "user_id": test_user_id,
            "favorite_families": ["TestFamily1"],
            "detective_targets": ["TestPlayer1"],
            "notification_settings": {
                "kills": True,
                "shots": True,
                "plating_drops": True,
                "profile_changes": True
            },
            "ui_settings": {
                "theme": "dark",
                "auto_refresh": True,
                "show_dead_players": False
            }
        }
        self.test_api_endpoint("Save User Preferences", "/preferences", "POST", preferences_data)
        self.test_api_endpoint("Get User Preferences", f"/preferences/{test_user_id}")
        
        # Test internal endpoints (these might not be accessible externally)
        print("\n🔧 Testing Internal Endpoints...")
        internal_data = {"test": "data"}
        self.test_api_endpoint("Internal List Update", "/internal/list-updated", "POST", internal_data)
        self.test_api_endpoint("Internal Notification", "/internal/notification", "POST", internal_data)

    async def run_websocket_tests(self):
        """Run WebSocket tests"""
        print("\n🔌 Testing WebSocket Functionality...")
        await self.test_websocket_connection()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        # Show successful tests with interesting data
        successful_tests = [test for test in self.test_results if test['success'] and test['response_data']]
        if successful_tests:
            print(f"\n✅ SUCCESSFUL TESTS WITH DATA ({len(successful_tests)}):")
            for test in successful_tests:
                print(f"  • {test['name']}")
                if isinstance(test['response_data'], dict):
                    for key, value in list(test['response_data'].items())[:3]:  # Show first 3 keys
                        print(f"    - {key}: {value}")

async def main():
    """Main test execution"""
    tester = OmertaIntelligenceAPITester()
    
    # Run API tests
    tester.run_all_tests()
    
    # Run WebSocket tests
    await tester.run_websocket_tests()
    
    # Print summary
    tester.print_summary()
    
    # Return exit code
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        sys.exit(1)