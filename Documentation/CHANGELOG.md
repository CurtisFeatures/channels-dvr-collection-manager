# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-21

### Initial Release

#### Added
- **Pattern Matching**
  - Regex pattern support for channel matching
  - Channel number range matching (e.g., 100-200, 5.1-5.9)
  - Multiple match types: Channel Name, Number, EPG data
  
- **Source Filtering**
  - Include specific sources (providers)
  - Exclude specific sources
  - Source selection interface
  
- **Advanced Sorting**
  - Alphabetical (A-Z, Z-A)
  - Channel number (ascending, descending)
  - Events Last (non-event channels first, events sorted by number)
  - Custom Regex sorting (prioritize channels matching a pattern)
  
- **Scheduling**
  - Global sync interval configuration
  - Per-rule sync intervals
  - Manual sync trigger
  - Background scheduler with APScheduler
  
- **Web Interface**
  - Modern, responsive design
  - Real-time pattern preview
  - Collection browser with expandable channel lists
  - Rule management (create, edit, delete)
  - Connection testing
  - Sync status and results display
  - Collapsible sections
  
- **Docker Support**
  - Docker and docker-compose deployment
  - Persistent storage for rules
  - Environment variable configuration
  - Health monitoring
  
- **Documentation**
  - Comprehensive README
  - Quick start guide
  - Advanced features guide
  - Troubleshooting guide
  - Unraid installation guide
  - API testing guides
  - Example rules

#### Technical Details
- Python Flask backend
- APScheduler for background jobs
- Single-page HTML/CSS/JS frontend (no external dependencies)
- JSON file storage for rules
- Channels DVR API integration
- Docker containerization

### Known Issues
- None at release

### Credits
- Channels DVR team for their excellent product
