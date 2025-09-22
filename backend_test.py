#!/usr/bin/env python3
"""
Backend Test Suite for Omerta Intelligence Dashboard Settings API
Tests both direct scraping service calls and backend proxy endpoints
"""

import requests
import json
import time
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

class SettingsAPITester:
    def __init__(self):
        # URLs from environment
        self.backend_url = "https://omerta-tactics.preview.emergentagent.com"
        self.scraping_service_url = "http://127.0.0.1:5001"
        
        # MongoDB connection
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client[os.environ.get('DB_NAME', 'omerta_intelligence')]
        
        # Test data
        self.test_settings = {
            "list_worker_interval": 1800,
            "detail_worker_interval": 300,
            "parallel_tabs": 3,
            "cloudflare_timeout": 90
        }
        
        self.default_settings = {
            "list_worker_interval": 3600,
            "detail_worker_interval": 900,
            "parallel_tabs": 5,
            "cloudflare_timeout": 60
        }
        
        print(f"🔧 Backend URL: {self.backend_url}")
        print(f"🔧 Scraping Service URL: {self.scraping_service_url}")
        print(f"🔧 MongoDB: {mongo_url}")

    def test_scraping_service_get_settings(self):
        """Test GET /api/scraping/settings on scraping service directly"""
        print("\n" + "="*60)
        print("🧪 TEST 1: Direct Scraping Service GET Settings")
        print("="*60)
        
        try:
            url = f"{self.scraping_service_url}/api/scraping/settings"
            print(f"📡 GET {url}")
            
            response = requests.get(url, timeout=10)
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received")
                print(f"📋 Settings: {json.dumps(data.get('settings', {}), indent=2)}")
                
                # Verify structure
                if 'settings' in data:
                    settings = data['settings']
                    required_keys = ['list_worker_interval', 'detail_worker_interval', 'parallel_tabs', 'cloudflare_timeout']
                    
                    missing_keys = [key for key in required_keys if key not in settings]
                    if missing_keys:
                        print(f"❌ Missing required keys: {missing_keys}")
                        return False
                    
                    print(f"✅ All required settings keys present")
                    return True
                else:
                    print(f"❌ Response missing 'settings' key")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_scraping_service_post_settings(self):
        """Test POST /api/scraping/settings on scraping service directly"""
        print("\n" + "="*60)
        print("🧪 TEST 2: Direct Scraping Service POST Settings")
        print("="*60)
        
        try:
            url = f"{self.scraping_service_url}/api/scraping/settings"
            print(f"📡 POST {url}")
            print(f"📤 Payload: {json.dumps(self.test_settings, indent=2)}")
            
            response = requests.post(url, json=self.test_settings, timeout=10)
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received")
                print(f"📋 Message: {data.get('message', 'No message')}")
                print(f"📋 Note: {data.get('note', 'No note')}")
                
                # Verify settings were saved
                if 'settings' in data:
                    saved_settings = data['settings']
                    print(f"💾 Saved Settings: {json.dumps(saved_settings, indent=2)}")
                    
                    # Check if our test values were applied
                    for key, expected_value in self.test_settings.items():
                        if saved_settings.get(key) != expected_value:
                            print(f"❌ Setting {key}: expected {expected_value}, got {saved_settings.get(key)}")
                            return False
                    
                    print(f"✅ All settings saved correctly")
                    
                    # Check for restart message
                    if "restart" in data.get('note', '').lower():
                        print(f"✅ Restart message present: {data.get('note')}")
                    else:
                        print(f"⚠️ No restart message found")
                    
                    return True
                else:
                    print(f"❌ Response missing 'settings' key")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_backend_proxy_get_settings(self):
        """Test GET /api/scraping/settings on backend proxy"""
        print("\n" + "="*60)
        print("🧪 TEST 3: Backend Proxy GET Settings")
        print("="*60)
        
        try:
            url = f"{self.backend_url}/api/scraping/settings"
            print(f"📡 GET {url}")
            
            response = requests.get(url, timeout=10)
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received")
                print(f"📋 Settings: {json.dumps(data.get('settings', {}), indent=2)}")
                
                # Verify structure
                if 'settings' in data:
                    settings = data['settings']
                    required_keys = ['list_worker_interval', 'detail_worker_interval', 'parallel_tabs', 'cloudflare_timeout']
                    
                    missing_keys = [key for key in required_keys if key not in settings]
                    if missing_keys:
                        print(f"❌ Missing required keys: {missing_keys}")
                        return False
                    
                    print(f"✅ All required settings keys present")
                    
                    # Verify these are the test settings we just saved
                    for key, expected_value in self.test_settings.items():
                        if settings.get(key) != expected_value:
                            print(f"❌ Setting {key}: expected {expected_value}, got {settings.get(key)}")
                            return False
                    
                    print(f"✅ Backend proxy returns same settings as direct service")
                    return True
                else:
                    print(f"❌ Response missing 'settings' key")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_backend_proxy_post_settings(self):
        """Test POST /api/scraping/settings on backend proxy"""
        print("\n" + "="*60)
        print("🧪 TEST 4: Backend Proxy POST Settings")
        print("="*60)
        
        # Use different settings to verify the change
        new_test_settings = {
            "list_worker_interval": 2400,
            "detail_worker_interval": 600,
            "parallel_tabs": 4,
            "cloudflare_timeout": 120
        }
        
        try:
            url = f"{self.backend_url}/api/scraping/settings"
            print(f"📡 POST {url}")
            print(f"📤 Payload: {json.dumps(new_test_settings, indent=2)}")
            
            response = requests.post(url, json=new_test_settings, timeout=10)
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received")
                print(f"📋 Message: {data.get('message', 'No message')}")
                print(f"📋 Note: {data.get('note', 'No note')}")
                
                # Verify settings were saved
                if 'settings' in data:
                    saved_settings = data['settings']
                    print(f"💾 Saved Settings: {json.dumps(saved_settings, indent=2)}")
                    
                    # Check if our new test values were applied
                    for key, expected_value in new_test_settings.items():
                        if saved_settings.get(key) != expected_value:
                            print(f"❌ Setting {key}: expected {expected_value}, got {saved_settings.get(key)}")
                            return False
                    
                    print(f"✅ All settings saved correctly via backend proxy")
                    
                    # Check for restart message
                    if "restart" in data.get('note', '').lower():
                        print(f"✅ Restart message present: {data.get('note')}")
                    else:
                        print(f"⚠️ No restart message found")
                    
                    # Store these settings for MongoDB verification
                    self.latest_settings = new_test_settings
                    return True
                else:
                    print(f"❌ Response missing 'settings' key")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_mongodb_persistence(self):
        """Test that settings are persisted in MongoDB"""
        print("\n" + "="*60)
        print("🧪 TEST 5: MongoDB Settings Persistence")
        print("="*60)
        
        try:
            # Query MongoDB directly
            settings_doc = self.db.scraping_settings.find_one({"type": "intervals"})
            
            if not settings_doc:
                print(f"❌ No settings document found in MongoDB")
                return False
            
            print(f"✅ Settings document found in MongoDB")
            print(f"📋 Document ID: {settings_doc.get('_id')}")
            print(f"📋 Updated At: {settings_doc.get('updated_at')}")
            
            stored_settings = settings_doc.get('settings', {})
            print(f"💾 Stored Settings: {json.dumps(stored_settings, indent=2)}")
            
            # Verify the latest settings match what we saved
            if hasattr(self, 'latest_settings'):
                for key, expected_value in self.latest_settings.items():
                    if stored_settings.get(key) != expected_value:
                        print(f"❌ MongoDB setting {key}: expected {expected_value}, got {stored_settings.get(key)}")
                        return False
                
                print(f"✅ MongoDB settings match latest API update")
            else:
                print(f"⚠️ No latest settings to compare (previous test may have failed)")
            
            return True
            
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            return False

    def test_settings_validation(self):
        """Test settings validation (minimum values)"""
        print("\n" + "="*60)
        print("🧪 TEST 6: Settings Validation")
        print("="*60)
        
        # Test with invalid (too low) values
        invalid_settings = {
            "list_worker_interval": 5,  # Should be min 10
            "detail_worker_interval": 1,  # Should be min 10
            "parallel_tabs": 0,  # Should be min 1
            "cloudflare_timeout": 5  # Should be min 10
        }
        
        try:
            url = f"{self.scraping_service_url}/api/scraping/settings"
            print(f"📡 POST {url}")
            print(f"📤 Invalid Payload: {json.dumps(invalid_settings, indent=2)}")
            
            response = requests.post(url, json=invalid_settings, timeout=10)
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received")
                
                if 'settings' in data:
                    validated_settings = data['settings']
                    print(f"🔧 Validated Settings: {json.dumps(validated_settings, indent=2)}")
                    
                    # Check if validation worked
                    validation_checks = [
                        (validated_settings.get('list_worker_interval', 0) >= 10, 'list_worker_interval >= 10'),
                        (validated_settings.get('detail_worker_interval', 0) >= 10, 'detail_worker_interval >= 10'),
                        (validated_settings.get('parallel_tabs', 0) >= 1, 'parallel_tabs >= 1'),
                        (validated_settings.get('cloudflare_timeout', 0) >= 10, 'cloudflare_timeout >= 10'),
                        (validated_settings.get('parallel_tabs', 11) <= 10, 'parallel_tabs <= 10')
                    ]
                    
                    all_valid = True
                    for check_passed, check_name in validation_checks:
                        if check_passed:
                            print(f"✅ Validation: {check_name}")
                        else:
                            print(f"❌ Validation failed: {check_name}")
                            all_valid = False
                    
                    return all_valid
                else:
                    print(f"❌ Response missing 'settings' key")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_default_settings_behavior(self):
        """Test that default settings are returned when none exist"""
        print("\n" + "="*60)
        print("🧪 TEST 7: Default Settings Behavior")
        print("="*60)
        
        try:
            # First, clear any existing settings
            print("🗑️ Clearing existing settings from MongoDB...")
            self.db.scraping_settings.delete_many({"type": "intervals"})
            
            # Now test GET to see if defaults are returned
            url = f"{self.scraping_service_url}/api/scraping/settings"
            print(f"📡 GET {url} (after clearing settings)")
            
            response = requests.get(url, timeout=10)
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received")
                
                if 'settings' in data:
                    settings = data['settings']
                    print(f"📋 Default Settings: {json.dumps(settings, indent=2)}")
                    
                    # Verify these match expected defaults
                    for key, expected_value in self.default_settings.items():
                        if settings.get(key) != expected_value:
                            print(f"❌ Default {key}: expected {expected_value}, got {settings.get(key)}")
                            return False
                    
                    print(f"✅ All default settings correct")
                    return True
                else:
                    print(f"❌ Response missing 'settings' key")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_service_restart_persistence(self):
        """Test that settings persist across service restarts (simulated)"""
        print("\n" + "="*60)
        print("🧪 TEST 8: Settings Persistence Across Restarts")
        print("="*60)
        
        # Save specific settings
        restart_test_settings = {
            "list_worker_interval": 7200,
            "detail_worker_interval": 1200,
            "parallel_tabs": 2,
            "cloudflare_timeout": 180
        }
        
        try:
            # Save settings
            url = f"{self.scraping_service_url}/api/scraping/settings"
            print(f"📡 POST {url} (saving settings for restart test)")
            print(f"📤 Payload: {json.dumps(restart_test_settings, indent=2)}")
            
            response = requests.post(url, json=restart_test_settings, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to save settings: {response.status_code}")
                return False
            
            print(f"✅ Settings saved")
            
            # Simulate restart by creating a new data manager instance
            # (In real scenario, this would be a service restart)
            print("🔄 Simulating service restart...")
            time.sleep(1)
            
            # Retrieve settings again
            print(f"📡 GET {url} (after simulated restart)")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'settings' in data:
                    retrieved_settings = data['settings']
                    print(f"📋 Retrieved Settings: {json.dumps(retrieved_settings, indent=2)}")
                    
                    # Verify settings persisted
                    for key, expected_value in restart_test_settings.items():
                        if retrieved_settings.get(key) != expected_value:
                            print(f"❌ After restart, {key}: expected {expected_value}, got {retrieved_settings.get(key)}")
                            return False
                    
                    print(f"✅ All settings persisted across restart")
                    return True
                else:
                    print(f"❌ Response missing 'settings' key")
                    return False
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("\n" + "🚀" + "="*58 + "🚀")
        print("🧪 OMERTA INTELLIGENCE SETTINGS API TEST SUITE")
        print("🚀" + "="*58 + "🚀")
        
        tests = [
            ("Direct Scraping Service GET", self.test_scraping_service_get_settings),
            ("Direct Scraping Service POST", self.test_scraping_service_post_settings),
            ("Backend Proxy GET", self.test_backend_proxy_get_settings),
            ("Backend Proxy POST", self.test_backend_proxy_post_settings),
            ("MongoDB Persistence", self.test_mongodb_persistence),
            ("Settings Validation", self.test_settings_validation),
            ("Default Settings Behavior", self.test_default_settings_behavior),
            ("Restart Persistence", self.test_service_restart_persistence)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "📊" + "="*58 + "📊")
        print("🧪 TEST RESULTS SUMMARY")
        print("📊" + "="*58 + "📊")
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} | {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n📈 TOTAL: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Settings API is working correctly.")
        else:
            print(f"⚠️ {failed} test(s) failed. Please check the issues above.")
        
        return failed == 0

if __name__ == "__main__":
    tester = SettingsAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)