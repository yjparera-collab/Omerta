# 🎯 Omerta War Intelligence Dashboard

A sophisticated, real-time intelligence dashboard for the online game Barafranca (Omerta). This application transforms raw public API data into actionable tactical intelligence during intense endgame scenarios.

## 🏗️ Architecture

**Hybrid System Design:**
- **Flask Scraping Service** (Port 5001) - Handles Selenium-based data collection with Cloudflare bypass
- **FastAPI Intelligence API** (Port 8001) - Provides WebSocket real-time updates and REST APIs  
- **React Frontend** (Port 3000) - Modern dashboard interface with live intelligence feed
- **Dual Database** - SQLite for high-frequency cache/analytics + MongoDB for app state

## 🚀 Features

### 📡 Real-Time Intelligence
- **Smart List Worker (Analist)** - Monitors all players every 30 seconds, detects changes
- **Batch Detail Worker (Detective)** - Intensive tracking of selected targets with 30s cache
- **Intelligence Notifications** - Critical alerts for plating drops, kills, shots, profile changes
- **WebSocket Updates** - Live dashboard updates without page refresh

### 🎯 Target Management  
- **Family-Based Tracking** - Monitor entire families with one click
- **Individual Detective Mode** - Precision tracking of specific high-value targets
- **Priority Queue System** - Smart scheduling ensures critical targets get fastest updates
- **Configurable Tracking** - Easy setup through modern web interface

### 📊 War Analytics
- **Kill/Shot Trend Analysis** - Real-time combat activity charts
- **Activity Feed** - Live stream of all combat actions with timestamps  
- **Performance Metrics** - System status and queue monitoring
- **Historical Data** - SQLite-based analytics with configurable time ranges

### 🛡️ Advanced Features
- **Cloudflare Bypass** - Undetected Chrome driver with smart CAPTCHA handling
- **Change Detection** - Only processes data when actual changes occur (efficiency)
- **Rank-Aware Sorting** - Proper hierarchy sorting (Godfather > Bruglione > Chief, etc.)
- **Status Intelligence** - Distinguishes alive, dead, ranked, unranked players
- **Plating Alerts** - Critical notifications when targets become vulnerable

## ⚡ Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Chrome browser (for Selenium)
- MongoDB (local or remote)

### Installation

1. **Install Dependencies**
```bash
python install_dependencies.py
```

2. **Start All Services**  
```bash
python start_intelligence.py
```

3. **Manual Setup (Alternative)**
```bash
# Backend services
cd backend && python intelligence_server.py &
python scraping_service.py &

# Frontend  
cd frontend && yarn start &
```

### First Time Setup
1. **Browser Setup** - The scraping service will open Chrome and may require manual CAPTCHA solving on first run
2. **Target Configuration** - Navigate to http://localhost:3000/families to select target families
3. **Intelligence Monitoring** - Watch the real-time feed on the Players dashboard

## 🔧 Configuration

### Environment Variables
```bash
# Backend (.env)
MONGO_URL=mongodb://localhost:27017
DB_NAME=omerta_intelligence  
CORS_ORIGINS=*

# Frontend (.env)
REACT_APP_BACKEND_URL=https://your-domain.com
```

### Scraping Parameters
```python
# scraping_service.py
MAIN_LIST_INTERVAL = 30      # Seconds between full list scans
CACHE_DURATION = 30          # Cache time for detective targets  
BATCH_SIZE = 5               # Players processed per batch
MAX_CONCURRENT_TABS = 2      # Browser tab limit
```

## 🎮 Game Integration

### API Endpoints Used
- `https://barafranca.com/index.php?module=API&action=users` - Player list
- `https://barafranca.com/index.php?module=API&action=user&name={USERNAME}` - Player details

### Intelligence Detection Logic
1. **Plating Drops** - When player plating changes to "None" or "No plating" (CRITICAL)
2. **Kill Updates** - When kill count increases (HIGH PRIORITY) 
3. **Shot Activity** - When bullets_shot total increases (MEDIUM PRIORITY)
4. **Profile Changes** - When private profiles become public (INTELLIGENCE VALUE)

## 📊 Dashboard Usage

### Players Page
- **Filter & Search** - Name, family, rank filters with dead player toggle
- **Smart Sorting** - Rank-hierarchy aware, position 0 handling
- **Detective Selection** - Multi-select players for intensive tracking
- **Live Intelligence** - Real-time notifications sidebar

### Families Page  
- **Target Configuration** - Select families for enhanced monitoring
- **Member Overview** - Expandable family rosters with stats
- **Batch Operations** - Select all/none, family-wide tracking

### Analytics Page
- **Trend Analysis** - Kill/shot activity over time
- **System Performance** - Queue sizes, cache status, connection health
- **Activity Timeline** - Chronological feed of all intelligence events

## 🔒 Security & Performance

### Cloudflare Bypass Strategy
```python
def setup_browser_session(driver, url, worker_name):
    driver.get(url)
    time.sleep(8)  # Wait for automatic pass
    if "Verify you are human" in driver.page_source:
        input("Manual CAPTCHA solving required...")
    time.sleep(3)
```

### Efficiency Optimizations
- **Hash-Based Change Detection** - Only process when data actually changes
- **Smart Caching** - 30s for detective targets, 5min for others  
- **Priority Queue** - High-value targets get faster updates
- **Tab Reuse** - Single browser instance with tab cycling
- **Batch Processing** - Multiple players per request cycle

## 🛠️ Development

### Project Structure
```
/app/
├── scraping_service.py          # Flask scraping worker
├── backend/
│   ├── intelligence_server.py   # FastAPI dashboard API  
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   └── hooks/             # Intelligence data hooks
│   └── package.json           # Node dependencies  
└── start_intelligence.py      # Unified startup script
```

### Key Components
- **IntelligenceDataManager** - Core data handling and change detection
- **ConnectionManager** - WebSocket connection lifecycle  
- **useIntelligence Hook** - React integration for real-time data
- **Smart Workers** - Selenium automation with error handling

## ⚠️ Important Notes

### Browser Requirements
- **Undetected Chrome** - Uses undetected-chromedriver for Cloudflare bypass
- **Manual CAPTCHA** - First-time setup may require human verification
- **Headless Mode** - Can run without GUI once initialized

### Data Privacy
- **Public APIs Only** - Uses only publicly available game data
- **No Authentication** - No login credentials stored or transmitted  
- **Local Processing** - All intelligence analysis happens locally

### Performance Considerations  
- **Resource Usage** - Chrome browser + Python processes (moderate CPU/RAM)
- **Network Traffic** - Respectful request timing (30s intervals)
- **Cache Efficiency** - SQLite database prevents redundant API calls

## 🔧 Troubleshooting

### Common Issues
1. **Cloudflare Blocks** - Restart scraping service, solve CAPTCHA manually
2. **WebSocket Disconnections** - Check FastAPI service status, auto-reconnect enabled
3. **Missing Players** - Verify target family configuration, check scraping queue
4. **Performance Issues** - Monitor queue sizes, adjust BATCH_SIZE if needed

### Logs Location
```bash
/var/log/supervisor/scraping.err.log    # Scraping service errors
/var/log/supervisor/backend.err.log     # FastAPI errors  
/var/log/supervisor/frontend.err.log    # React build errors
```

### Health Checks
- Scraping Service: http://localhost:5001/api/scraping/status
- Intelligence API: http://localhost:8001/api/status  
- WebSocket: ws://localhost:8001/ws

## 🎯 Advanced Usage

### Custom Intelligence Rules
Modify `log_player_changes()` in `IntelligenceDataManager` to add custom detection logic:

```python
def log_player_changes(self, user_id, username, new_data):
    # Add your custom intelligence detection here
    # Example: Detect rank promotions, family changes, etc.
```

### Performance Tuning
```python
# High-activity periods
MAIN_LIST_INTERVAL = 15      # Faster scanning
BATCH_SIZE = 10              # Larger batches
MAX_CONCURRENT_TABS = 4      # More parallelism

# Low-activity periods  
MAIN_LIST_INTERVAL = 60      # Slower scanning
CACHE_DURATION = 120         # Longer cache
```

## 📈 Roadmap

### Planned Features
- [ ] **Mobile App** - React Native companion app
- [ ] **AI Predictions** - Machine learning for combat outcome prediction
- [ ] **Alliance Intelligence** - Multi-family coordination tools
- [ ] **Historical Analysis** - Long-term trend analysis and reporting
- [ ] **Alert System** - SMS/Email notifications for critical events
- [ ] **Export Tools** - CSV/JSON data export capabilities

## 🤝 Contributing

This is a specialized tool for Barafranca gameplay analysis. Contributions welcome for:
- Performance optimizations
- UI/UX improvements  
- Additional intelligence detection rules
- Mobile compatibility
- Documentation improvements

## ⚖️ Legal & Ethics

- **Fair Use** - Uses only publicly available API data
- **Game Terms** - Complies with Barafranca terms of service
- **No Automation** - Pure intelligence gathering, no game automation
- **Educational** - Demonstrates web scraping and real-time data processing

---

**Built for tactical intelligence in the world of Omerta. Knowledge is power. 🎯**