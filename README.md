<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/static/logo.png" width="30%">

# Channels DVR Collection Manager

A powerful web-based tool for automatically managing channel collections in Channels DVR based on flexible pattern matching rules.

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen)

[![Docker Pulls](https://img.shields.io/docker/pulls/curtisfeatures/channels-dvr-collection-manager)](https://hub.docker.com/r/curtisfeatures/channels-dvr-collection-manager)
[![GitHub Stars](https://img.shields.io/github/stars/CurtisFeatures/channels-dvr-collection-manager)](https://github.com/CurtisFeatures/channels-dvr-collection-manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 What's New in v1.1.0

### Major Features
- **🎨 Beautiful New UI** - Custom purple theme with professional design
- **✏️ Visual Pattern Builder** - Build complex patterns without knowing regex
- **🔍 Live Preview** - Test patterns as you build them
- **📋 Copy & Clone** - Reuse patterns and duplicate rules
- **⚙️ Granular Refresh Control** - Separate source and EPG refresh options
- **⌨️ Better UX** - ESC key support, scrollable previews, inline editing

See [CHANGELOG.md](Documentation/CHANGELOG.md) for complete details.

## ✨ Features

### Automated Collection Management
- **Pattern-Based Matching**: Use regex patterns to automatically match channels
- **Visual Pattern Builder**: Build patterns without regex knowledge
  - Simple mode with 7 pattern types
  - Advanced mode with multi-condition AND/OR logic  
  - Live preview showing matching channels
- **Multiple Match Types**: Match on channel name, number, or EPG data
- **Source Filtering**: Include or exclude specific sources
- **Smart Sorting**: Multiple options including "Events Last" for sports
- **Per-Rule Sync**: Custom intervals for each rule
- **Selective Refresh**: Refresh only relevant sources before syncing

### Pattern Builder

Build complex regex patterns visually:

**Simple Mode** - Choose from 7 common patterns:
- Contains text
- Starts with text
- Ends with text
- Exact match
- Any of these words (OR)
- Channel number range
- Does NOT contain

**Advanced Mode** - Combine multiple conditions:
- Multiple conditions with AND logic
- OR logic within conditions (comma-separated)
- Per-condition case sensitivity
- Real-time pattern generation
- Built-in examples

### Live Testing
- **Test Before Adding** - See matches before committing
- **Scrollable Results** - View all matching channels
- **Multiple Preview Points** - Builder, manual entry, and complete rule

### Smart Sorting Options
- **Events Last**: Puts event channels (e.g., "Event 1") at the end
- **Alphabetical**: A-Z or Z-A
- **Channel Number**: Ascending or descending
- **Custom Regex**: Prioritize channels matching a pattern
- **Paramount+ Events**: Special handling for Paramount+ numbering

### Copy & Clone
- **Copy Patterns**: Reuse successful patterns from other rules
- **Clone Rules**: Duplicate entire rules for variations
- **Edit Patterns**: Modify existing patterns inline

## 🚀 Quick Start

### Docker Compose (Recommended)

1. Create `docker-compose.yml`:
```yaml
services:
  channels-collection-manager:
    image: curtisfeatures/channels-dvr-collection-manager:latest
    container_name: channels-collection-manager
    ports:
      - "5000:5000"
    environment:
      - DVR_URL=http://your-channels-dvr:8089
      - SYNC_INTERVAL_MINUTES=60
    volumes:
      - ./config:/config
    restart: unless-stopped
```

2. Start the container:
```bash
docker-compose up -d
```

3. Open web interface:
```
http://localhost:5000
```


## 📖 Usage

### Creating Your First Rule

1. **Click "+ Add Rule"**

2. **Basic Settings:**
   - Name: e.g., "DAZN Sports Channels"
   - Collection: Select from your Channels DVR collections
   - Match Types: Channel Name, Number, or EPG

3. **Build Patterns** - Choose your method:

   **Option A: Pattern Builder** (Recommended for beginners)
   - Click "Show Builder"
   - **Simple Mode**: Select pattern type and enter text
   - **Advanced Mode**: Combine multiple conditions
   - Click "Test Pattern" to see matches
   - Click "Add This Pattern"

   **Option B: Copy from Another Rule**
   - Expand "📋 Copy Patterns from Another Rule"
   - Select a rule from dropdown
   - Choose which patterns to copy
   - Click "Copy Selected Patterns"

   **Option C: Manual Entry** (For regex experts)
   - Enter pattern directly
   - Click "Test" to preview
   - Click "Add"

4. **Configure Options:**
   - **Sort Order**: Choose how channels are sorted
   - **Source Filters**: Include/exclude specific sources
   - **Sync Interval**: Per-rule override (optional)
   - **Refresh Options**:
     - ☐ Refresh Sources Before Each Sync
     - ☐ Refresh EPG Before Each Sync

5. **Preview:** Click "Preview" to see complete results

6. **Save:** Rule syncs immediately and on schedule

### Example Rules

#### DAZN Sports (Simple Mode)
- Pattern Type: "Contains"
- Text: "DAZN"
- Match: Channel Name
- Sort: Events Last
- Include Sources: DAZN UK P1

#### ESPN (excluding news)
Using Advanced Mode:
- Condition 1: Starts with "ESPN"
- Condition 2: Does NOT contain "News"
- Result: `^(?!.*News)ESPN.*$`

#### Channel Range
- Pattern Type: "Channel number range"
- Range: "100-200"
- Match: Channel Number

## 🔧 Advanced Features

### Pattern Examples

**Simple Patterns:**
```
Sport                    # Contains "Sport"
^ESPN                    # Starts with "ESPN"
HD$                      # Ends with "HD"
^ESPN HD$                # Exact match "ESPN HD"
ESPN|FOX|NBC             # Any of these (OR)
^(?!.*Kids).*$           # Does NOT contain "Kids"
100-200                  # Channel range
```

**Advanced Combinations:**
```
^(?!.*football)(?=.*DAZN).*$
# Contains "DAZN" AND Does NOT contain "football"

^(?=.*(Sport|ESPN))Sky.*$
# Contains "Sport" OR "ESPN" AND Starts with "Sky"
```

### Refresh Options

Control when data is refreshed:

**Refresh Sources Before Each Sync:**
- Rescans sources for new/changed channels
- Only refreshes sources used by the rule
- Useful for IPTV providers with dynamic channels

**Refresh EPG Before Each Sync:**
- Updates program guide data
- Ensures latest schedule information

**Smart Scoping:**
- If "Include Sources" set: Only those sources refreshed
- If "Exclude Sources" set: All except those refreshed
- If no filters: All sources refreshed

### Clone Rules

Create variations quickly:
1. Find existing rule
2. Click "📋 Clone"
3. Modify settings
4. Save as new rule

Perfect for:
- Testing different sort orders
- Creating similar rules for different collections
- Building variations of successful patterns

## 🔌 API

REST API for programmatic access:

### Endpoints

```
GET    /api/rules          # List all rules
POST   /api/rules          # Create rule
PUT    /api/rules/{id}     # Update rule
DELETE /api/rules/{id}     # Delete rule
POST   /api/preview        # Preview matches
GET    /api/status         # Sync status
```

See [API Documentation](Channels_Collection_Manager.postman_collection.json) for details.

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DVR_URL` | `http://channelsdvr:8089` | Channels DVR server URL |
| `SYNC_INTERVAL_MINUTES` | `60` | Global sync interval |

### Rule Structure

```json
{
  "id": "unique-id",
  "name": "Rule Name",
  "collection_slug": "collection-slug",
  "patterns": ["pattern1", "pattern2"],
  "match_types": ["name", "number"],
  "sort_order": "events_last",
  "include_sources": ["source-id"],
  "exclude_sources": ["source-id"],
  "sync_interval_minutes": 15,
  "refresh_sources_before_sync": true,
  "refresh_epg_before_sync": false,
  "enabled": true
}
```

## 🐛 Troubleshooting

### Common Issues

**Rules not syncing:**
- Verify `DVR_URL` is correct and accessible
- Check collections exist in Channels DVR
- View logs: `docker logs channels-collection-manager`

**Patterns not matching:**
- Use Pattern Builder's live preview
- Test with "Test Pattern" button
- Verify match types are selected
- Check case sensitivity settings

**Preview shows wrong channels:**
- Review source filters (include/exclude)
- Confirm match types are correct
- Test individual patterns separately


## 📚 Documentation

- [Quick Start Guide](Documentation/QUICKSTART.md)
- [First Rule Guide](Documentation/FIRST_RULE_GUIDE.md)
- [Advanced Features](Documentation/ADVANCED_FEATURES.md)
- [Changelog](Documentation/CHANGELOG.md)

## 🤝 Support

- **Documentation**: [GitHub](https://github.com/CurtisFeatures/channels-dvr-collection-manager)
- **Issues**: [GitHub Issues](https://github.com/CurtisFeatures/channels-dvr-collection-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/CurtisFeatures/channels-dvr-collection-manager/discussions)

## 🙏 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🌟 Acknowledgments

- Built for [Channels DVR](https://getchannels.com/)
- Inspired by the Channels DVR community
- Custom UI design and pattern builder

## Screenshots
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Main%20Screen.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Main%20Preview.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Existing%20Collections.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Rule%20Edit1.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Rule%20Edit2.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Pattern%20Builder%20Simple.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Pattern%20Builder%20Advanced.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Pattern%20Manual.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Sort.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Preview%20No%20Sort.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Preview%20with%20Sort.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Existing%20Collections.png" width="80%">
<img src="https://github.com/CurtisFeatures/channels-dvr-collection-manager/blob/main/img/Sync%20Results.png" width="80%">
