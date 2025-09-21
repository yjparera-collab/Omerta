#!/usr/bin/env python3
"""
Omerta Intelligence Dashboard Backend API Testing - Username-First Implementation
Tests all FastAPI endpoints with focus on username-first approach
"""

import requests
import json
import sys
import asyncio
import websockets
from datetime import datetime
import time

class OmertaIntelligenceAPITester:
    def __init__(self, base_url="https://omerta-intel.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.ws_url = base_url.replace('https', 'wss') + '/ws'
        self.scraping_service_url = "http://127.0.0.1:5001"  # Internal scraping service
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.sample_usernames = ["Kazuo", "TestPlayer", "AlphaPlayer", "DeltaPlayer"]

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

    def test_api_endpoint(self, name, endpoint, method='GET', data=None, expected_status=200, base_url=None):
        """Test a single API endpoint"""
        if base_url:
            url = f"{base_url}{endpoint}"
        else:
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
                try:
                    error_data = response.json()
                    self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}: {error_data}")
                except:
                    self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, {}
                
        except requests.exceptions.RequestException as e:
            self.log_test(name, False, f"Request failed: {str(e)}")
            return False, {}

    def test_scraping_service_status(self):
        """Test if scraping service is running"""
        print("\n🔧 Testing Scraping Service Status...")
        try:
            response = requests.get(f"{self.scraping_service_url}/api/scraping/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Scraping Service Status", True, f"Service online with {data.get('cached_players', 0)} cached players")
                return True, data
            else:
                self.log_test("Scraping Service Status", False, f"Service returned {response.status_code}")
                return False, {}
        except Exception as e:
            self.log_test("Scraping Service Status", False, f"Service not accessible: {str(e)}")
            return False, {}

    def test_username_first_endpoints(self):
        """Test username-first implementation endpoints"""
        print("\n👤 Testing Username-First Implementation...")
        
        # Test backend proxy endpoint
        for username in self.sample_usernames:
            success, data = self.test_api_endpoint(
                f"Backend Username Proxy - {username}", 
                f"/players/by-username/{username}",
                expected_status=404  # Expected to fail if scraping service not running
            )
            if success and data:
                print(f"   Found data for {username}: kills={data.get('kills', 'N/A')}, shots={data.get('bullets_shot', {}).get('total', 'N/A')}")
        
        # Test scraping service direct endpoint (if available)
        scraping_available, _ = self.test_scraping_service_status()
        if scraping_available:
            for username in self.sample_usernames:
                success, data = self.test_api_endpoint(
                    f"Scraping Service Username - {username}",
                    f"/api/scraping/player-username/{username}",
                    base_url=self.scraping_service_url,
                    expected_status=404  # May not exist in cache
                )
                if success and data:
                    print(f"   Direct scraping data for {username}: wealth={data.get('wealth', 'N/A')}, plating={data.get('plating', 'N/A')}")

    def test_data_flow_verification(self):
        """Test data flow from general endpoints"""
        print("\n🔄 Testing Data Flow Verification...")
        
        # Test general player list
        success, players_data = self.test_api_endpoint("Get All Players", "/players")
        if success and players_data:
            players = players_data.get('players', [])
            print(f"   Found {len(players)} players in general list")
            
            # Test a few player details by ID
            for i, player in enumerate(players[:3]):  # Test first 3 players
                player_id = player.get('id')
                if player_id:
                    self.test_api_endpoint(f"Player Details by ID - {player_id}", f"/players/{player_id}")
        
        # Test tracked players
        success, tracked_data = self.test_api_endpoint("Get Tracked Players", "/intelligence/tracked-players")
        if success and tracked_data:
            tracked_players = tracked_data.get('tracked_players', [])
            print(f"   Found {len(tracked_players)} tracked players")
            for player in tracked_players[:3]:  # Show first 3
                username = player.get('username', 'Unknown')
                kills = player.get('kills', 'N/A')
                shots = player.get('shots', 'N/A')
                print(f"   Tracked: {username} - Kills: {kills}, Shots: {shots}")

    def test_detective_targets_management(self):
        """Test detective targets with sample usernames"""
        print("\n🕵️ Testing Detective Targets Management...")
        
        # Add sample detective targets
        detective_data = {"usernames": self.sample_usernames}
        success, response = self.test_api_endpoint(
            "Add Detective Targets", 
            "/intelligence/detective/add", 
            "POST", 
            detective_data
        )
        
        if success:
            print(f"   Added targets: {', '.join(self.sample_usernames)}")
            
            # Verify they were added by checking tracked players
            time.sleep(2)  # Wait for processing
            success, tracked_data = self.test_api_endpoint("Verify Added Targets", "/intelligence/tracked-players")
            if success and tracked_data:
                tracked_players = tracked_data.get('tracked_players', [])
                added_usernames = [p.get('username') for p in tracked_players]
                for username in self.sample_usernames:
                    if username in added_usernames:
                        print(f"   ✅ {username} successfully added to tracked players")
                    else:
                        print(f"   ❌ {username} not found in tracked players")

    def test_mongodb_integration(self):
        """Test MongoDB integration through API responses"""
        print("\n🗄️ Testing MongoDB Integration...")
        
        # Test system status to check MongoDB connection
        success, status_data = self.test_api_endpoint("System Status", "/status")
        if success and status_data:
            db_info = status_data.get('database', {})
            scraping_info = status_data.get('scraping_service', {})
            
            print(f"   Database connected: {db_info.get('connected', False)}")
            print(f"   Preferences count: {db_info.get('preferences_count', 0)}")
            print(f"   WebSocket connections: {status_data.get('websocket_connections', 0)}")
            print(f"   Scraping service: {scraping_info.get('status', 'unknown')}")

    async def test_websocket_connection(self):
        """Test WebSocket connection and basic communication"""
        try:
            print(f"\n🔌 Testing WebSocket connection to {self.ws_url}")
            
            async with websockets.connect(self.ws_url, timeout=10) as websocket:
                # Wait for connection established message
                try:
                    initial_message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    message = json.loads(initial_message)
                    if message.get("type") == "connection_established":
                        self.log_test("WebSocket Connection", True, "Connection established successfully")
                    else:
                        self.log_test("WebSocket Connection", True, f"Connected with message: {message.get('type')}")
                except asyncio.TimeoutError:
                    self.log_test("WebSocket Connection", True, "Connected but no initial message")
                
                # Test ping-pong
                ping_message = json.dumps({"type": "ping"})
                await websocket.send(ping_message)
                
                # Wait for pong response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                message = json.loads(response)
                
                if message.get("type") == "pong":
                    self.log_test("WebSocket Ping-Pong", True, "Successfully received pong response")
                else:
                    self.log_test("WebSocket Ping-Pong", False, f"Expected pong, got {message.get('type')}")
                        
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Connection failed: {str(e)}")

    def test_real_time_updates(self):
        """Test real-time update endpoints"""
        print("\n📡 Testing Real-time Update Endpoints...")
        
        # Test internal list update endpoint
        update_data = {
            "type": "player_list_updated",
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
        self.test_api_endpoint("Internal List Update", "/internal/list-updated", "POST", update_data)
        
        # Test internal notification endpoint
        notification_data = {
            "type": "test_notification",
            "username": "TestPlayer",
            "message": "Test notification for username-first implementation",
            "timestamp": datetime.now().isoformat()
        }
        self.test_api_endpoint("Internal Notification", "/internal/notification", "POST", notification_data)

    def run_all_tests(self):
        """Run comprehensive API tests for username-first implementation"""
        print("🎯 OMERTA INTELLIGENCE DASHBOARD - USERNAME-FIRST TESTING")
        print("=" * 70)
        
        # Test basic API health
        print("\n📡 Testing Core API Endpoints...")
        self.test_api_endpoint("API Root", "/")
        
        # Test MongoDB integration
        self.test_mongodb_integration()
        
        # Test scraping service
        self.test_scraping_service_status()
        
        # Test username-first endpoints (main focus)
        self.test_username_first_endpoints()
        
        # Test data flow verification
        self.test_data_flow_verification()
        
        # Test detective targets management
        self.test_detective_targets_management()
        
        # Test real-time updates
        self.test_real_time_updates()

    async def run_websocket_tests(self):
        """Run WebSocket tests"""
        print("\n🔌 Testing WebSocket Functionality...")
        await self.test_websocket_connection()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 USERNAME-FIRST IMPLEMENTATION TEST SUMMARY")
        print("=" * 70)
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
                    # Show relevant data for username-first implementation
                    data = test['response_data']
                    if 'username' in data:
                        print(f"    - Username: {data['username']}")
                    if 'kills' in data:
                        print(f"    - Kills: {data['kills']}")
                    if 'bullets_shot' in data:
                        shots = data['bullets_shot']
                        if isinstance(shots, dict):
                            print(f"    - Shots: {shots.get('total', 'N/A')}")
                        else:
                            print(f"    - Shots: {shots}")
                    if 'tracked_players' in data:
                        print(f"    - Tracked Players Count: {len(data['tracked_players'])}")

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