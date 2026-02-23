# Changelog

All notable changes to Channels DVR Collection Manager will be documented in this file.

## [1.2.0] - 2026-02-23

### 🎯 Organization & Workflow

#### Import/Export Rules
- **Export Rules** - Backup and share rule configurations
  - Export all rules or filter by group
  - JSON format with metadata (version, timestamp, rule count)
  - Automatic filename with date: `channels-rules-YYYY-MM-DD.json`
  - API endpoint: `GET /api/export?group=all`
- **Import Rules** - Restore or share configurations
  - Two modes: Merge (add to existing) or Replace (delete all first)
  - File validation and preview before import
  - Shows rule count and export metadata
  - Automatic ID generation prevents conflicts
  - API endpoint: `POST /api/import`
- **Duplicate Detection** - Intelligent conflict warnings
  - Detects identical rules (name + collection + patterns)
  - Shows warning with duplicate list
  - User can choose to proceed or cancel
  - Only checks in merge mode (replace doesn't need it)
  - Live preview shows duplicates before import

#### Groups/Folders
- **Organize Rules** - Collapsible folder system
  - Add optional "Group" field when creating/editing rules
  - Rules automatically organize by group name
  - Visual folder icons (📁) with expand/collapse
  - Click folder header to toggle visibility
  - State persists via localStorage
  - Groups sorted alphabetically (Ungrouped always last)
- **Group Management**
  - Autocomplete suggests existing group names
  - Filter dropdown shows all groups
  - Export can filter by specific group
  - Group count displayed in folder header
  - API endpoint: `GET /api/groups`

#### Search & Filter
- **Real-Time Search** - Find rules instantly
  - Search by rule name, pattern text, or collection name
  - Results update as you type
  - Works across all groups
  - Clears with empty search
- **Group Filter** - Show specific categories
  - Dropdown with all groups + "All Groups" + "Ungrouped"
  - Instant filtering on selection
  - Visual feedback for active filter
- **Combined Filtering** - Search + Group together
  - Use both filters simultaneously
  - Narrow results precisely
  - Example: Search "ESPN" in "Sports" group

### 🕐 Advanced Scheduling

#### Time-Based Rule Activation
- **Day of Week Selection** - Choose when rules run
  - 7 checkboxes for Mon-Sun
  - Leave all unchecked = run every day
  - Select specific days (e.g., weekends only)
  - Saved as array: `["monday", "wednesday", "friday"]`
- **Time Windows** - Set start and end times
  - HH:MM format (24-hour)
  - Start time: When rule becomes active
  - End time: When rule becomes inactive
  - Leave blank = run any time
- **Overnight Ranges** - Cross midnight support
  - Example: 22:00 - 06:00
  - Handles time calculations correctly
  - Useful for overnight maintenance windows
- **Visual Indicators** - See schedules at a glance
  - Schedule badge on rule cards
  - Shows time window: "🕐 09:00 - 17:00"
  - Shows abbreviated days: "MON, TUE, WED"
  - Purple accent color
- **Backend Validation** - Rules respect schedules
  - `is_rule_scheduled_now()` checks before sync
  - Logs "Skipping rule - outside scheduled time window"
  - Sync results show skipped rules
  - No errors, just informational

#### Schedule Examples
- Business hours: Mon-Fri, 09:00-17:00
- Weekend sports: Sat-Sun, 08:00-23:00
- Overnight IPTV: Daily, 02:00-05:00
- After school kids: Mon-Fri, 15:00-20:00

### 📑 Rule Templates

#### Save Pattern Configurations
- **Create Templates** - Save successful patterns
  - "💾 Save as Template" button in rule editor
  - Prompts for name and description
  - Saves patterns + metadata + match types + sort order
  - Stored in `/config/templates.json`
  - API endpoint: `POST /api/templates`
- **Browse Templates** - Library view
  - "📑 Templates" button in header
  - Shows all saved templates
  - Displays name, description, patterns, match types, sort
  - Visual pattern tags
  - Delete unwanted templates
- **Use Templates** - One-click application
  - Click "Use Template" button
  - Opens rule modal (or uses current if open)
  - Auto-fills patterns, match types, sort order
  - Preserves pattern metadata (builder info)
  - Just add rule name and collection
- **Share Templates** - Export includes templates
  - Templates embedded in rule exports
  - Import brings in templates
  - Perfect for packaging common patterns

#### Template Structure
```json
{
  "id": "uuid",
  "name": "DAZN Sports Pattern",
  "description": "All DAZN excluding football",
  "patterns": ["^(?!.*football)(?=.*DAZN).*$"],
  "pattern_metadata": {
    "^(?!.*football)(?=.*DAZN).*$": {
      "mode": "advanced",
      "conditions": [...]
    }
  },
  "match_types": ["name"],
  "sort_order": "events_last",
  "created_at": "2026-02-23T..."
}
```

### ⚡ User Experience Enhancements

#### Quick Enable/Disable Toggle
- **Animated Toggle Switch** - Beautiful purple gradient
  - Positioned left of rule name
  - Smooth slide animation
  - Purple when enabled, gray when disabled
  - Hover effects
  - 44x24px size (touch-friendly)
- **Instant Action** - No modal required
  - Click toggle → Rule updates immediately
  - Success notification
  - Rule list refreshes
  - Visual feedback (card dims when disabled)
  - API call: `PUT /api/rules/{id}` with enabled field

#### Smart Pattern Editing
- **Pattern Metadata Persistence** - Edit builder patterns visually
  - When pattern created with builder, metadata saved
  - Metadata includes: mode, type, value, case sensitivity
  - Stored in rule: `pattern_metadata` object
  - Persists across sessions (saved to database)
- **Visual Re-Editing** - Pattern reopens in builder
  - Click "Edit" on pattern
  - If metadata exists → Opens in builder
  - Populates all fields exactly as created
  - If no metadata → Classic text prompt
- **Copy Preserves Metadata** - Copied patterns editable
  - Copy pattern from another rule → Metadata copies too
  - Use template → Metadata restored
  - Clone rule → All metadata preserved
- **Backward Compatible** - Old patterns still work
  - Manual regex patterns use text edit
  - Old rules without metadata work normally
  - Metadata added when re-edited with builder

#### Modal & Navigation
- **ESC Key Support** - Close any modal with ESC
  - Rule modal
  - Import modal
  - Templates modal
  - Preview modal
- **Collapsible Sections** - Cleaner interface
  - Group folders expand/collapse
  - State remembered in localStorage
  - Visual hierarchy

### 🔧 Backend Enhancements

#### New Rule Fields
```json
{
  "group": "Sports",
  "pattern_metadata": {
    "pattern": {
      "mode": "simple",
      "type": "contains",
      "value": "ESPN"
    }
  },
  "schedule_enabled": false,
  "schedule_days": ["monday", "wednesday"],
  "schedule_start_time": "09:00",
  "schedule_end_time": "17:00"
}
```

#### Schedule Validation
- `is_rule_scheduled_now()` function
- Checks day of week match
- Checks time window match
- Handles overnight ranges
- Called before each rule sync
- Logs skip reason

#### API Endpoints Added
```
GET    /api/export?group=all       # Export rules
POST   /api/import                 # Import rules
GET    /api/groups                 # List unique groups
GET    /api/templates              # List templates
POST   /api/templates              # Save template
DELETE /api/templates/{id}         # Delete template
```

### 🐛 Bug Fixes

#### Pattern Metadata
- **Copy Patterns** - Now copies metadata
  - Fixed: Copied patterns couldn't be edited in builder
  - Now: Metadata copies with pattern
  - Deep copy prevents reference issues
- **Templates** - Now include metadata
  - Fixed: Template patterns couldn't be edited in builder
  - Now: Templates save and restore metadata
  - Backward compatible with old templates

#### JavaScript Fixes
- **useTemplate** - Fixed function call
  - Changed `updateSortFields()` to `toggleCustomSortInput()`
  - Fixed undefined function error
- **Error Handling** - Improved throughout
  - Better try-catch blocks
  - User-friendly error messages
  - Graceful degradation

### 📚 Documentation

#### Updated Files
- **README.md** - Complete v1.2.0 rewrite
  - All new features documented
  - Usage examples for all features
  - API endpoint reference
  - Troubleshooting section
- **CHANGELOG.md** - This file!
  - Comprehensive v1.2.0 changelog
  - Migration guide
  - Version history

#### New Documentation
- Import/Export workflow
- Groups/Folders organization guide
- Scheduling examples and use cases
- Template creation and sharing
- Pattern metadata system

### ⚡ Performance

- Background schedule checks (non-blocking)
- Efficient metadata storage (only for builder patterns)
- Smart group rendering (virtual scrolling for large lists)
- localStorage for UI state (faster page loads)

---

## [1.1.0] - 2026-02-22

### 🎨 UI/UX Overhaul

#### Custom Theme & Branding
- **Custom Purple Gradient Theme** - Beautiful new color scheme
- **Custom Logo** - Professional folder/collections icon
- **Inter Font Typography** - Modern, clean font
- **Enhanced Button Styling** - Gradient effects with hover
- **Improved Shadows** - Purple-tinted shadows

#### Pattern Builder
- **Visual Pattern Builder** - Build complex regex without knowing regex
- **Two Modes:**
  - Simple: 7 common pattern types
  - Advanced: Multi-condition builder with AND/OR logic
- **Built-in Examples** - Learn from real use cases
- **Case Sensitivity Toggle** - Global and per-condition

#### Live Preview Features
- **Pattern Builder Preview** - Test as you build
- **Manual Entry Preview** - Test before adding
- **Scrollable Results** - View all matches

#### Copy & Clone Features
- **Copy Patterns** - Reuse from other rules
- **Clone Rules** - Duplicate entire rules
- **Edit Patterns** - Modify existing patterns

### ⚙️ Backend Enhancements

#### Refresh Control
- **Granular Options** - Source and EPG separate
- **Smart Refresh** - Only relevant sources
- **Background Processing** - Non-blocking

### 🐛 Bug Fixes
- Docker Compose version warnings fixed
- Preview modal z-index corrected
- Pattern copy null reference fixed

---

## [1.0.1] - 2026-02-21

### Added
- Collection names in rule cards
- In-app preview modal
- Enhanced Paramount+ event detection

### Fixed
- Collection slug resolution
- Modal overlay click handling

---

## [1.0.0] - 2026-02-20

### Initial Release

#### Core Features
- Pattern-based channel matching
- Multiple match types
- Source filtering
- Multiple sort orders
- Per-rule sync intervals
- Real-time preview
- Web-based UI
- Docker deployment
- REST API

---

## Migration Guides

### From 1.1.x to 1.2.0

**No breaking changes!** Simply update:

```bash
docker-compose pull
docker-compose up -d
```

**What You Get:**
- All existing rules work unchanged
- New fields default to safe values:
  - `group`: null (no grouping)
  - `schedule_enabled`: false (always active)
  - `pattern_metadata`: {} (empty, will populate as patterns edited)
- Can immediately use new features:
  - Add groups to organize
  - Add schedules to any rule
  - Create templates from patterns
  - Import/export all rules

**Recommended:**
1. Try organizing rules with groups
2. Export rules as backup
3. Create templates from successful patterns
4. Add schedules to time-sensitive rules

### From 1.0.x to 1.1.0

Update Docker image:
```bash
docker-compose pull
docker-compose up -d
```

Existing rules preserved. New features additive.

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.2.0 | 2026-02-23 | Import/Export, Groups, Scheduling, Templates, Quick Toggle |
| 1.1.0 | 2026-02-22 | Pattern Builder, Copy/Clone, Theme overhaul |
| 1.0.1 | 2026-02-21 | Collection names, in-app preview |
| 1.0.0 | 2026-02-20 | Initial release |

---

## Future Enhancements

### Planned
- **EPG Pattern Matching** - Match on callsign/affiliate
- **Batch Operations** - Edit multiple rules at once
- **Notification System** - Alerts for sync failures
- **Multi-DVR Support** - Manage multiple instances

### Under Consideration
- Dark mode theme
- Custom color themes
- Rule execution history
- Conflict detection
- Auto-backup rules
- Rule dependencies

---

## Support & Contributing

- **Issues**: [GitHub Issues](https://github.com/CurtisFeatures/channels-dvr-collection-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/CurtisFeatures/channels-dvr-collection-manager/discussions)
- **Contributing**: See [Documentation/CONTRIBUTING.md](Documentation/CONTRIBUTING.md)

---

**Note**: This project follows [Semantic Versioning](https://semver.org/).  
Version format: MAJOR.MINOR.PATCH
