#!/usr/bin/env python3
"""
Test MongoDB connectie
"""
import os
from dotenv import load_dotenv

# Laad .env bestand
load_dotenv('backend/.env')

def test_mongodb():
    print("🧪 MONGODB CONNECTIE TEST")
    print("=" * 40)
    
    # Toon environment variables
    mongo_url = os.environ.get('MONGO_URL', 'niet gevonden')
    db_name = os.environ.get('DB_NAME', 'niet gevonden') 
    
    print(f"📋 MONGO_URL: {repr(mongo_url)}")
    print(f"📋 DB_NAME: {repr(db_name)}")
    
    if 'niet gevonden' in mongo_url:
        print("❌ MONGO_URL niet geladen uit .env bestand!")
        return False
    
    try:
        print("\n🔗 Verbinden met MongoDB...")
        from pymongo import MongoClient
        
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        
        # Test connectie
        print("🏓 Ping MongoDB server...")
        client.admin.command('ismaster')
        
        # Test database access
        print(f"📊 Toegang tot database '{db_name}'...")
        db = client[db_name]
        
        # Test collection access
        print("📝 Test write/read...")
        test_collection = db.test_connection
        
        # Insert test document
        result = test_collection.insert_one({"test": "connection", "timestamp": "now"})
        print(f"✅ Test document inserted: {result.inserted_id}")
        
        # Read test document  
        doc = test_collection.find_one({"_id": result.inserted_id})
        print(f"✅ Test document retrieved: {doc}")
        
        # Cleanup
        test_collection.delete_one({"_id": result.inserted_id})
        print("🧹 Test document verwijderd")
        
        client.close()
        print("\n🎉 MONGODB CONNECTIE SUCCESVOL!")
        return True
        
    except Exception as e:
        print(f"\n❌ MONGODB CONNECTIE GEFAALD!")
        print(f"Fout: {e}")
        print(f"Type: {type(e).__name__}")
        
        print("\n🔧 TROUBLESHOOTING TIPS:")
        print("1. Is MongoDB geïnstalleerd en draait het?")
        print("   - net start MongoDB")
        print("2. Is port 27017 in gebruik door een ander proces?")
        print("   - netstat -an | findstr 27017")
        print("3. Firewall issues?")
        print("4. Probeer: mongodb://127.0.0.1:27017 in plaats van localhost")
        
        return False

if __name__ == "__main__":
    test_mongodb()