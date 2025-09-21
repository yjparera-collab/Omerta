#!/usr/bin/env python3
"""
Script om .env bestand te controleren en repareren
"""
import os

def check_and_fix_env():
    env_path = "backend/.env"
    
    print("🔍 CONTROLEREN VAN .ENV BESTAND")
    print("=" * 50)
    
    if not os.path.exists(env_path):
        print("❌ .env bestand niet gevonden!")
        print("📝 Maken van nieuw .env bestand...")
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("MONGO_URL=mongodb://localhost:27017\n")
            f.write("DB_NAME=omerta_intelligence\n")
            f.write("CORS_ORIGINS=http://localhost:3000\n")
        
        print("✅ Nieuw .env bestand aangemaakt")
        return
    
    print(f"✅ .env bestand gevonden: {env_path}")
    
    # Lees huidige inhoud
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("\n📄 HUIDIGE INHOUD:")
    for i, line in enumerate(lines, 1):
        # Toon ook onzichtbare karakters
        repr_line = repr(line)
        print(f"Regel {i}: {repr_line}")
        
        # Controleer op spaties aan het eind
        if line.rstrip() != line.rstrip('\n').rstrip():
            print(f"   ⚠️  SPATIE GEDETECTEERD aan het eind van regel {i}!")
    
    # Repareer het bestand
    print("\n🔧 REPAREREN VAN .ENV BESTAND...")
    
    fixed_lines = []
    for line in lines:
        # Verwijder alle trailing whitespace behalve newline
        fixed_line = line.rstrip() + '\n'
        fixed_lines.append(fixed_line)
    
    # Schrijf gerepareerde versie
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ .env bestand gerepareerd!")
    
    # Toon nieuwe inhoud
    print("\n📄 NIEUWE INHOUD:")
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        print(f"Regel {i}: {repr(line)}")
    
    print("\n🧪 TEST MONGODB CONNECTIE...")
    
    # Test de connectie
    try:
        from pymongo import MongoClient
        
        # Lees de gerepareerde waarden
        mongo_url = None
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('MONGO_URL='):
                    mongo_url = line.split('=', 1)[1].strip()
                    break
        
        if mongo_url:
            print(f"🔗 Proberen te connecten met: {repr(mongo_url)}")
            client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            
            # Test de connectie
            client.admin.command('ismaster')
            print("✅ MongoDB connectie succesvol!")
            client.close()
        else:
            print("❌ MONGO_URL niet gevonden in .env")
            
    except Exception as e:
        print(f"❌ MongoDB connectie gefaald: {e}")
        print("\n🔧 MOGELIJKE OPLOSSINGEN:")
        print("1. Controleer of MongoDB draait: net start MongoDB")
        print("2. Installeer MongoDB Community Server")
        print("3. Controleer of port 27017 vrij is")

if __name__ == "__main__":
    check_and_fix_env()