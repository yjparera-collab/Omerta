# Omerta War Intelligence Dashboard

## 🎯 Project Overview

Advanced tactical intelligence dashboard for Barafranca.com (Omerta) with real-time player tracking, combat statistics, and strategic analysis capabilities.

### Key Features
- **Real-time Player Intelligence**: Live tracking of kills, shots, wealth, and plating data
- **Detective Agency System**: Deep surveillance of high-value targets  
- **Username-First Architecture**: Reliable data tracking using usernames as primary keys
- **Cloudflare Bypass**: Advanced browser automation to overcome protection
- **Combat Analytics**: Strategic intelligence for tactical decision-making

## 🚨 CRITICAL CLOUDFLARE ISSUE

### The Problem
Barafranca.com uses **Cloudflare protection** that blocks automated API requests:
- Direct HTTP requests return `403 Forbidden`
- APIs require browser-based access with CAPTCHA solving
- Container environments cannot run visible browsers

### Evidence
```bash
# This will fail with 403 Forbidden:
curl "https://barafranca.com/index.php?module=API&action=user&name=teg"
```

### Solution
**Must run the scraping service on Windows with visible Chrome browser:**
1. Use `mongodb_scraping_service_windows.py` (not container version)
2. Keep Chrome window open and visible
3. Manually solve CAPTCHAs when they appear
4. Allow browser automation to bypass Cloudflare

## 📁 File Structure

### Core Files
```
/app/
├── backend/
│   ├── intelligence_server.py      # FastAPI backend with WebSocket support
│   ├── requirements.txt           # Python dependencies
│   └── .env                      # Backend configuration
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PlayersPage.js    # Main intelligence dashboard
│   │   │   ├── FamiliesPage.js   # Target configuration
│   │   │   └── AnalyticsPage.js  # Combat analytics
│   │   └── hooks/
│   │       └── useIntelligence.js # API integration hook
│   └── package.json              # Frontend dependencies
├── mongodb_scraping_service_windows.py  # PRODUCTION scraping (Windows only)
├── container_scraping_service.py        # Demo service (container)
├── start_omerta_windows.bat            # Windows startup script
└── test_result.md                      # Testing documentation
```

### Cleaned Up (Removed)
- All test/debug scripts
- Deprecated services
- Duplicate configuration files
- Development artifacts

## 🚀 Quick Start

### Windows Setup (PRODUCTION)
```bash
# 1. Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install

# 2. Start all services
start_omerta_windows.bat

# 3. IMPORTANT: Keep Chrome window open and solve CAPTCHAs
```

### Container Setup (DEMO ONLY)
```bash
# Container provides sample data but cannot access real Barafranca APIs
python container_scraping_service.py
```

## 🛠 Architecture

### Username-First Design
- **Primary Key**: Username (reliable identifier)
- **Secondary Key**: User ID (legacy compatibility)  
- **Cache Strategy**: MongoDB with username-based indexing
- **API Endpoints**: `/api/players/by-username/{username}`

### Data Flow
```
Barafranca API → Cloudflare Bypass → Chrome Browser → Scraping Service → MongoDB → Backend API → Frontend
```

### Real-time Updates
- WebSocket connections for live intelligence updates
- Automatic data refresh when new intelligence is gathered
- Push notifications for combat activity

## 📊 API Endpoints

### Backend (Port 8001)
- `GET /api/players` - All cached players
- `GET /api/players/by-username/{username}` - Player details
- `GET /api/intelligence/tracked-players` - Detective targets
- `POST /api/intelligence/detective/add` - Add surveillance targets
- `WebSocket /ws` - Real-time updates

### Scraping Service (Port 5001)
- `GET /api/scraping/status` - Service status
- `GET /api/scraping/debug-info` - Cloudflare troubleshooting
- `GET /api/scraping/detective/targets` - Tracked players data
- `POST /api/scraping/detective/add` - Add tracking targets

## 🎯 Intelligence Features

### Players Dashboard
- **Filter by Name/Family/Rank**: Advanced search capabilities
- **Tracked Players Only**: Focus on surveillance targets
- **Real Combat Data**: Actual kills, shots, wealth, plating
- **Strategic Sorting**: Position, combat effectiveness, wealth levels

### Target Configuration
- **Detective Agency**: Add players to surveillance list
- **Family Tracking**: Monitor entire family organizations
- **Priority Targets**: High-value surveillance subjects

### Analytics
- **Combat Statistics**: Kill/death ratios, shooting accuracy
- **Wealth Analysis**: Economic intelligence and target prioritization
- **Plating Intelligence**: Defensive capabilities assessment

## 🔧 Troubleshooting

### "Kills: N/A, Shots: N/A, Wealth: N/A"
**Cause**: Cloudflare is blocking the scraping service
**Solution**:
1. Ensure Windows scraping service is running
2. Keep Chrome browser window open and visible
3. Solve any CAPTCHAs that appear
4. Check `http://localhost:5001/api/scraping/debug-info`

### MongoDB Connection Issues
**Cause**: Trailing spaces in environment variables
**Solution**: Use quoted environment variables in .bat file:
```batch
set "MONGO_URL=mongodb://localhost:27017"
```

### Frontend Shows No Players
**Cause**: Backend cannot reach scraping service
**Solution**:
1. Verify scraping service status: `http://localhost:5001/api/scraping/status`
2. Check backend logs for API connectivity
3. Ensure all services started properly

## 🧪 Testing

### Manual Testing
```bash
# Test backend API
curl http://localhost:8001/api/players

# Test scraping service
curl http://localhost:5001/api/scraping/status

# Test username-based retrieval
curl http://localhost:8001/api/players/by-username/Kazuo
```

### Automated Testing
- Backend: `deep_testing_backend_v2`
- Frontend: `auto_frontend_testing_agent`
- Integration: Full end-to-end testing

## ⚠️ Important Notes

### Environment Requirements
- **Windows**: Required for production scraping (Chrome automation)
- **MongoDB**: Local instance for data persistence
- **Chrome**: Visible browser window required for Cloudflare bypass

### Security Considerations
- Uses undetected-chromedriver for stealth browsing
- Manual CAPTCHA solving required (no automated bypass)
- Session management for persistent authentication

### Performance
- Real-time WebSocket updates minimize API calls
- MongoDB caching reduces external requests
- Username-first architecture improves data reliability

## 📈 Future Enhancements

### Planned Features
- Advanced combat analytics and predictions
- Historical data tracking and trends
- Automated threat assessment scoring
- Multi-server intelligence aggregation

### Technical Improvements
- Enhanced Cloudflare bypass techniques
- Headless browser optimization
- Advanced session management
- Distributed scraping architecture

## 🤝 Support

For issues related to:
- **Cloudflare Problems**: Check debug endpoint and ensure Windows setup
- **Data Display Issues**: Verify username-first implementation
- **MongoDB Issues**: Check connection strings and indexes
- **Browser Automation**: Ensure Chrome stays visible and interactive

---

**Note**: This intelligence dashboard is designed for legitimate game strategy and analysis purposes within Barafranca.com community guidelines.