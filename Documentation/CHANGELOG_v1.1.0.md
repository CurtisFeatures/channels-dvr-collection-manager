# Changelog

All notable changes to Channels DVR Collection Manager will be documented in this file.

## [1.1.0] - 2026-02-22

### 🎨 UI/UX Overhaul

#### Custom Theme & Branding
- **Custom Purple Gradient Theme** - Beautiful new color scheme throughout the interface
- **Custom Logo** - Professional folder/collections icon (1024x1024px)
- **Inter Font Typography** - Modern, clean font (Bold 700, SemiBold 600)
  - Headers: Inter Bold with optimized letter-spacing
  - Body: Inter Regular for better readability
- **Enhanced Button Styling** - Gradient effects with hover animations
- **Improved Shadows** - Purple-tinted shadows for depth

#### Pattern Builder (NEW!)
- **Visual Pattern Builder** - Build complex regex without knowing regex
- **Two Modes:**
  - **Simple Mode** - 7 common pattern types:
    - Contains text
    - Starts with text
    - Ends with text
    - Exact match
    - Any of these words (OR logic)
    - Channel number range
    - Does NOT contain (negative lookahead)
  - **Advanced Mode** - Multi-condition builder:
    - Multiple conditions with AND logic
    - OR logic within conditions (comma-separated values)
    - Per-condition case sensitivity
    - Real-time pattern generation
- **Built-in Examples** - Expandable section with 5 common use cases
- **Case Sensitivity Toggle** - Available in both Simple and Advanced modes
  - Simple: Global toggle (adds `(?i)` flag)
  - Advanced: Per-condition toggle (uses `(?i:...)` inline flag)

#### Live Preview Features
- **Pattern Builder Preview** - Test patterns as you build
  - Shows matching channel count
  - Displays first 5 channels with numbers/names
  - Auto-refreshes on pattern changes
- **Manual Entry Preview** - New "Test" button next to "Add"
  - Test patterns before adding them
  - Scrollable results list (200px max height)
  - Shows all matches, not just first 5
- **Scrollable Results** - No more "+X more" text
  - All channels visible with scrollbar
  - Better UX for large result sets

#### Copy & Clone Features
- **Copy Patterns from Rules** - Reuse successful patterns
  - Collapsible dropdown (collapsed by default)
  - Select source rule from dropdown
  - Checkbox selection for individual patterns
  - Only shows rules with patterns
  - Filters out current rule when editing
- **Clone Rules** - New "📋 Clone" button
  - Duplicates entire rule configuration
  - Automatically adds " (Copy)" to name
  - Opens in editor for modifications
  - Perfect for creating variations

#### Edit & Management
- **Edit Existing Patterns** - New "Edit" button on each pattern
  - Inline editing with prompt dialog
  - Instant save and update
- **Pattern Organization** - Better visual layout
  - Patterns shown as code blocks
  - Edit and Remove buttons on each

#### Modal & Navigation Improvements
- **ESC Key Support** - Press ESC to close rule modal
- **Fixed Preview Modal** - No longer appears at bottom
  - Proper z-index layering (9999/10000)
  - Fixed positioning overlay
  - Centered display
- **Collapsible Sections** - Cleaner interface
  - Copy patterns collapsed by default
  - Pattern builder collapsible
  - Less visual clutter

### ⚙️ Backend Enhancements

#### Refresh Control
- **Granular Refresh Options** - Separate controls
  - ☐ Refresh Sources Before Each Sync
  - ☐ Refresh EPG Before Each Sync
  - Independent selection
  - Per-rule configuration
- **Smart Source Refresh** - Only refreshes relevant sources
  - If "Include Sources" selected: Only those sources
  - If "Exclude Sources" selected: All except those
  - If no filters: All sources
- **Background Processing** - Non-blocking refresh
  - Runs in separate thread
  - Server stays responsive
  - 0.5 second startup delay
  - 5-second timeout per API call

#### Data Storage Updates
- **New Rule Fields:**
  ```json
  {
    "refresh_sources_before_sync": false,
    "refresh_epg_before_sync": false
  }
  ```
- **Backward Compatible** - Old rules still work
- **Migration Friendly** - Missing fields default to false

### 🐛 Bug Fixes

#### Docker Compose
- **Removed obsolete `version` field** - No more warnings
  - Updated `docker-compose.yml`
  - Updated `docker-compose.example.yml`
  - Follows latest Compose spec

#### JavaScript Fixes
- **Fixed preview modal try-catch** - Missing catch block
  - Properly nested try-catch structure
  - Error handling for both rule loading and preview
- **Fixed pattern copy dropdown** - Null reference error
  - Added null checks for DOM elements
  - Safe handling of missing elements
- **Builder reset on close** - Modal cleanup
  - Resets advanced conditions array
  - Clears simple mode fields
  - Prevents data persistence between edits

#### UI Fixes
- **EPG Matching** - Marked as "Not Yet Implemented"
  - Checkbox disabled
  - Gray italic text indicator
  - Prevents confusion
- **Pattern preview positioning** - Fixed layout
  - Proper spacing and borders
  - Scrollable container
  - Clear visual hierarchy

### 📚 Documentation

#### Updated Files
- **README.md** - Complete rewrite with all new features
- **CHANGELOG.md** - Detailed version history
- **README_GITHUB.md** - GitHub-specific formatting
- **ADVANCED_FEATURES.md** - Pattern builder documentation

#### New Sections
- Pattern Builder guide with examples
- Copy & Clone workflow documentation
- Refresh options explained
- Live preview usage

### 🔧 Technical Changes

#### Frontend
- **CSS Enhancements:**
  - Purple gradient theme (#5b4fc7 → #8b7ee3)
  - Inter font integration from Google Fonts
  - Enhanced button gradients with hover effects
  - Improved modal z-index management
- **JavaScript Functions Added:**
  - `switchBuilderMode()` - Toggle Simple/Advanced
  - `addCondition()` / `removeCondition()` - Manage conditions
  - `updateGeneratedPattern()` - Real-time pattern generation
  - `testBuilderPattern()` - Preview builder results
  - `testManualPattern()` - Preview manual entry
  - `copySelectedPatterns()` - Copy from other rules
  - `cloneRule()` - Duplicate rules
  - `editPattern()` - Inline pattern editing
  - `populateCopyRulesDropdown()` - Load copy options

#### Backend (Python/Flask)
- **Refresh Logic:**
  - Separate source and EPG refresh handling
  - Source-specific refresh calls
  - Background threading for non-blocking
  - Timeout protection
- **API Updates:**
  - Rule schema extended with refresh fields
  - Backward-compatible field handling

#### Static Assets
- **New Files:**
  - `/static/logo.png` - 1024x1024px custom logo
  - `/static/favicon.png` - Browser favicon
  - `/static/README.md` - Asset documentation

### 🎯 Quality of Life

#### User Experience
- **Faster Workflow** - Less clicking, more doing
  - Test patterns before adding
  - Copy successful patterns
  - Clone similar rules
  - ESC to close
- **Better Feedback** - Know what's happening
  - Live previews everywhere
  - Success/error messages
  - Loading indicators
- **Smarter Defaults** - Less configuration
  - Copy section collapsed
  - Case sensitivity on by default in Simple mode
  - Refresh options both off by default

#### Developer Experience
- **Cleaner Code** - Better organization
  - Modular functions
  - Proper error handling
  - Consistent naming
- **Better Comments** - Easier to maintain
  - Function documentation
  - Complex logic explained

### ⚡ Performance

- **Background Refresh** - Server never blocks
- **Minimal Re-renders** - Only update what changed
- **Efficient Preview** - Reuses API calls
- **Smart Caching** - Collections cached in memory

---

## [1.0.1] - 2026-02-21

### Added
- Collection names displayed in rule cards
- In-app preview modal (replaces new tab)
- Enhanced Paramount+ event detection for "Events Last" sorting

### Fixed
- Collection slug resolution
- Modal overlay click handling

---

## [1.0.0] - 2026-02-20

### Initial Release

#### Core Features
- Pattern-based channel matching
- Multiple match types (name, number, EPG)
- Source filtering (include/exclude)
- Multiple sort orders including "Events Last"
- Per-rule sync intervals
- Real-time preview
- Web-based UI
- Docker deployment
- REST API

#### Sorting Options
- Alphabetical (A-Z, Z-A)
- Channel Number (ascending/descending)
- Events Last (special sports handling)
- Custom Regex pattern matching

#### Management
- Create, edit, delete rules
- Enable/disable rules
- Preview before saving
- Sync status display

---

## Future Enhancements

### Planned Features
- **EPG Pattern Matching** - Match on callsign/affiliate
- **Batch Operations** - Edit multiple rules at once
- **Rule Templates** - Pre-built rules for common scenarios
- **Import/Export** - Share rules between installations
- **Advanced Scheduling** - Time-based rule activation
- **Notification System** - Alerts for sync failures
- **Multi-DVR Support** - Manage multiple DVR instances

### Under Consideration
- Dark mode theme
- Custom color themes
- Rule grouping/folders
- Search and filter for rules
- Rule execution history
- Conflict detection
- Auto-backup rules

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.1.0 | 2026-02-22 | Pattern Builder, Copy/Clone, Theme overhaul |
| 1.0.1 | 2026-02-21 | Collection names, in-app preview |
| 1.0.0 | 2026-02-20 | Initial release |

---

## Migration Guide

### From 1.0.x to 1.1.0

**No breaking changes!** Simply update your Docker image:

```bash
docker-compose pull
docker-compose up -d
```

Your existing rules will continue to work. New features are additive:
- Refresh options default to `false` (no change in behavior)
- Existing patterns work as before
- All rule data preserved

**Recommended:**
1. Update Docker Compose files (remove `version:` line to clear warnings)
2. Try the new Pattern Builder for future rules
3. Enable refresh options on IPTV/dynamic source rules
4. Use Clone feature to create rule variations

---

## Support & Contributing

- **Report Issues**: [GitHub Issues](https://github.com/CurtisFeatures/channels-dvr-collection-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/CurtisFeatures/channels-dvr-collection-manager/discussions)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Note**: This project follows [Semantic Versioning](https://semver.org/). Version numbers are: MAJOR.MINOR.PATCH
