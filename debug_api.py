#!/usr/bin/env python3
"""
Debug script to test Barafranca API directly
"""
import requests
import json
from datetime import datetime

def test_barafranca_api():
    print("🔍 BARAFRANCA API DEBUG TEST")
    print("=" * 50)
    
    url = "https://barafranca.com/index.php?module=API&action=users"
    
    try:
        print(f"📡 Making request to: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Content Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"📏 Content Length: {len(response.text)} characters")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ JSON Parse: SUCCESS")
                print(f"📈 Data Type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"🔑 Top Level Keys: {list(data.keys())}")
                    
                    # Look for users
                    if 'users' in data:
                        users = data['users']
                        print(f"👥 Users Count: {len(users) if isinstance(users, list) else 'Not a list'}")
                        
                        if isinstance(users, list) and len(users) > 0:
                            first_user = users[0]
                            print(f"👤 First User Type: {type(first_user)}")
                            
                            if isinstance(first_user, dict):
                                print(f"🏷️  First User Keys: {list(first_user.keys())}")
                                print(f"📝 First User Sample:")
                                for key, value in list(first_user.items())[:10]:  # First 10 fields
                                    print(f"   {key}: {value}")
                                
                                # Check for ID fields
                                id_fields = ['user_id', 'id', 'player_id', 'userId', 'playerId']
                                found_id = None
                                for field in id_fields:
                                    if field in first_user:
                                        found_id = field
                                        break
                                
                                if found_id:
                                    print(f"🆔 ID Field Found: '{found_id}' = {first_user[found_id]}")
                                else:
                                    print(f"❌ No ID field found in: {id_fields}")
                                
                                # Check for username fields
                                name_fields = ['username', 'name', 'player_name', 'userName', 'playerName']
                                found_name = None
                                for field in name_fields:
                                    if field in first_user:
                                        found_name = field
                                        break
                                
                                if found_name:
                                    print(f"👤 Name Field Found: '{found_name}' = {first_user[found_name]}")
                                else:
                                    print(f"❌ No name field found in: {name_fields}")
                                    
                elif isinstance(data, list):
                    print(f"📋 Direct List: {len(data)} items")
                    if len(data) > 0:
                        first_item = data[0]
                        print(f"🔍 First Item: {type(first_item)}")
                        if isinstance(first_item, dict):
                            print(f"🏷️  Keys: {list(first_item.keys())}")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print(f"📄 Raw Content Preview (first 500 chars):")
                print(response.text[:500])
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 DEBUG TEST COMPLETE")

if __name__ == "__main__":
    test_barafranca_api()