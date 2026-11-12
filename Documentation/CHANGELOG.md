# Changelog

All notable changes to Channels DVR Collection Manager will be documented in this file.

## [2.2.0] - 2026-11-12

### Added
- `GET`/`POST`/`DELETE /api/curato/rule` for Curato Command Center's *New channel group* wizard: gets or creates the collection by name, adds or updates a number-range rule limited to chosen sources (found again by a `key`), sets the sort order and sync interval, and syncs it. Delete removes the rule, and the collection only if this endpoint created it and no other rule uses it.

### Changed
- "Events Last" sort: a channel counts as generic when it has no description before the channel label (`:Sky Sports UK 48`), is only words and a number (`Event 12`, `PPV 03`, `DAZN UK - 50`, `Paramount+ 50 :`) or says nothing is on (`No Event Scheduled`, `Off Air`, `TBA`). Anything with `@`, `v`/`vs`, a time or a date is a named event. Named channels go first, generic ones after, each in channel-number order (named channels were sorted A-Z before, so leading-colon placeholders came first).
- `/api/status` reports the app version (2.2.0).

## [2.0.0] - 2026-02-25

### 🚀 Major Features - Dispatcharr Integration

#### Dispatcharr IPTV Management
- **Connect to Dispatcharr Server** - Full integration with Dispatcharr IPTV management
  - JWT authentication with automatic token refresh
  - Secure credential storage in `/config/dispatcharr.json`
  - Test connection before saving
  - Token caching for 10x performance improvement (500ms → 50ms per request)
  - Automatic re-authentication on token expiry
- **Browse Channel Groups** - View all enabled Dispatcharr groups
  - Real-time group listing with channel counts
  - Provider and local group support
  - Server-side filtering (enabled + channel_count > 0)
  - Reduces groups from ~240 to ~50 for faster loading
- **Provider & Local Groups** - Dual group type support
  - **Provider Groups**: M3U account-based channels (m3u_account_count > 0)
  - **Local Groups**: Manually created channels (m3u_account_count = 0)
  - Toggle filter to view provider-only, local-only, or all
  - Different icons (📡 provider, 📂 local)
  - Smart API routing based on group type

#### One-Click Rule Creation
- **Create from Dispatcharr Group** - Generate rules instantly
  - Click "➕ Create Rule" on any Dispatcharr group
  - Auto-populates rule name from group name
  - Intelligent pattern generation from channel numbers
  - Smart gap handling (e.g., "101-104,107-108,115,120-122")
  - Supports ranges, individual numbers, and mixed patterns
  - Pre-filled match type (number for ranges, name for text)
  - Default group: "Dispatcharr"

#### Dispatcharr Sync Feature
- **🔄 Dispatcharr Sync** - Auto-update patterns from Dispatcharr
  - Checkbox: "Enable Dispatcharr Sync" when creating rule
  - Patterns automatically update before each sync
  - Always uses latest channel assignments from Dispatcharr
  - Perfect for dynamic IPTV lineups that change frequently
  - Visual badge: "🔄 Dispatcharr Sync" on rules and cards
  - Prevents creating duplicate auto-sync rules for same group
  - Stores Dispatcharr group ID in rule metadata

#### Auto Channel Creation Detection
- **⊕ Auto Channel Creation** - Detects Dispatcharr's built-in feature
  - Shows when Dispatcharr group has auto_channel_sync enabled
  - Visual badge: "⊕ Auto Channel Creation" in card body
  - Distinguishes from our Dispatcharr Sync feature
  - Helps identify groups with automatic channel assignment

### 📥 On-Demand Channel Fetching

#### Smart Loading Strategy
- **Removed Auto-Preload** - No more background loading of all groups
  - Old: Loaded 241 groups × preloaded all channels = 40s wait
  - New: Load ~50 filtered groups = 1s ⚡
- **Get Channels Button** - Fetch channel pattern on-demand
  - Green "📥 Get Channels" button on each card
  - Fetches channels for specific group only
  - Updates card with smart pattern
  - Shows success alert with pattern
  - ~0.5s per group (only when needed)
- **View Channels Button** - Opens modal with full channel list
  - Purple "👁️ View Channels" button
  - Shows all channels with numbers and names
  - Stream counts per channel
  - Pattern suggestion at bottom
  - Instant loading with no preload

#### API Optimization
- **Token Refresh System** - Reuse tokens instead of re-authenticating
  - Uses `/api/accounts/token/refresh/` endpoint
  - Saves access_token, refresh_token, expiry timestamp
  - Falls back to full auth if refresh fails
  - 10x performance improvement
- **Server-Side Filtering** - Filter groups at API level
  - Only enabled groups with channels
  - Reduces payload from 241 groups to ~50
  - Less data transfer, faster rendering
- **Exact Channel Lookup** - Query by channel_group_id
  - Uses `?channel_group_id=<ID>` parameter
  - Returns only channels for that specific group
  - Prevents false matches (e.g., 1 channel vs 6 channels)

### ➕ Dynamic Collection Creation

#### Create Collections On-The-Fly
- **New Collection Option** - Create collections without leaving the app
  - Dropdown option: "➕ Create New Collection"
  - Expands form with collection name and transform options
  - Available in both rule creation and Dispatcharr flows
- **Collection Name Transform** - Regex-based name modification
  - Input: Custom name or defaults to rule name
  - Find/Replace: Regex pattern and replacement text
  - Common templates:
    - Remove Prefix: `^UK\|\s*` → ""
    - Remove Suffix: `\s*[ᴴᴰᴿᴬᵂ⁴ᴷ]+$` → ""
    - Replace Text: `\|` → " - "
    - Remove Special: `[ᴴᴰᴿᴬᵂ⁴ᴷ\|]+` → ""
    - Extract Part: `^.*\|\s*(.*)$` → "$1"
  - Live preview shows transformation in real-time
- **Smart Get-or-Create** - Checks for existing collections
  - Backend endpoint: `POST /api/collections/get-or-create`
  - Case-insensitive name matching
  - If exists: Uses existing collection
  - If not: Creates new collection
  - Returns slug for use in rule
  - Channels DVR endpoint: `/dvr/collections/channels/new`

#### Regex Builder for Collections
- **Visual Transform Builder** - No regex knowledge required
  - Click "Show Regex Builder" to expand
  - 5 common templates with descriptions
  - One-click application
  - Preview updates instantly
  - Example: "UK| DOCUMENTARY ᴴᴰ/ᴿᴬᵂ" → "DOCUMENTARY"

### 🔀 Shared Collection Management

#### Automatic Protection
- **Detect Shared Collections** - When 2+ rules target same collection
  - Automatic detection during sync
  - Checks all enabled rules for matching collection_slug
  - Counts how many rules share the collection
- **Additive Mode** - Channels are added, never removed
  - Old channels ∪ new channels (union)
  - Prevents rules from fighting each other
  - Maintains sorting from rule settings
  - Log message: "⚠️ Shared collection detected! N rules target 'Name' - using additive mode"
  - Returns: `{shared_collection: true, rules_count: N}`
- **Normal Mode** - Single rule per collection
  - Old behavior: Add and remove channels
  - Replace collection items with new matches
  - Returns: `{shared_collection: false}`

#### Visual Indicators
- **Shared Collection Badge** - Shows on affected rules
  - Badge: "⚠️ Shared (N)" where N = number of rules
  - Amber/yellow color (#fbbf24) for visibility
  - Tooltip: "N rules share this collection - Channels are ADDED only, never removed"
  - Appears in rule header next to rule name
- **Collection Label** - Additive mode indicator
  - Text: "(Additive Mode)" next to collection name
  - Orange color (#f59e0b) 
  - Shows in rule info section
- **Merge Button** - One-click rule consolidation
  - Button: "🔀 Merge Rules" (orange)
  - Only visible on shared collection rules
  - Click to merge all rules for that collection

#### Merge Rules Feature
- **Combine Multiple Rules** - Merge shared collection rules into one
  - Confirmation dialog shows:
    - Collection name
    - List of all rules to merge
    - What will happen (combine patterns, delete duplicates)
  - Merge logic:
    - Uses first rule as base
    - Combines all patterns (unique set)
    - Merges pattern_metadata from all rules
    - Adds " (Merged)" to name
    - Deletes original rules after save
  - Returns to normal mode (not additive)
  - Success message with merged rule name
  - Automatic rule list refresh

### 🎯 Enhanced Channel Matching

#### Exact Number Matching
- **Word Boundary Matching** - Prevents partial number matches
  - Old: Pattern "400" matched channels 400, 6400, 4001, etc.
  - New: Pattern "400" matches only channel 400
  - Implementation: Uses `\b400\b` regex word boundaries
  - Only applies to pure numeric patterns
  - Non-numeric patterns use normal regex matching
  - Handles decimal numbers (400.1, 400.2)
- **Smart Pattern Detection** - Determines if pattern is numeric
  - Check: `pattern.replace('.', '').replace(',', '').isdigit()`
  - If numeric: Apply word boundaries
  - If not: Use standard regex
  - Preserves flexibility for complex patterns

### 🎨 UI/UX Improvements

#### Unified Card Layout
- **Bottom-Aligned Buttons** - All Dispatcharr cards uniform height
  - Used flexbox with `display: flex; flex-direction: column`
  - Main content area with `flex: 1`
  - Button container with `margin-top: auto`
  - All buttons align at bottom regardless of content
  - Consistent spacing between buttons
- **Button Wrapper** - New `.dispatcharr-buttons` container
  - Groups all action buttons
  - Consistent gap between buttons
  - Flex column layout
  - Removed individual margin-bottom styles

#### Clear Badge Naming
- **Dispatcharr Sync** - Our auto-update feature
  - Icon: 🔄
  - Color: Green (#10b981)
  - Location: Rule header (top right)
  - Tooltip: "Patterns are automatically updated from Dispatcharr before each sync"
- **Auto Channel Creation** - Dispatcharr's built-in feature
  - Icon: ⊕
  - Color: Inherits from card
  - Location: Card body (info section)
  - Shows when Dispatcharr group has auto_channel_sync enabled

#### Provider/Local Filtering
- **Group Type Toggle** - Filter Dispatcharr groups by type
  - Dropdown with 3 options:
    - All Groups (both provider and local)
    - Provider Groups (m3u_account_count > 0) - default
    - Local Groups (m3u_account_count = 0)
  - Auto-hides provider filter when "Local Groups" selected
  - Smart filtering logic updates in real-time
- **Visual Distinctions**
  - Provider groups: 📡 icon + provider name
  - Local groups: 📂 icon + "Local" label
  - Different data sources for channel lookup

### 🔧 Technical Improvements

#### Backend Optimizations
- **DispatcharrClient Enhancements**
  - `refresh_access_token()` - Token refresh endpoint
  - `_ensure_authenticated()` - Smart auth with refresh fallback
  - `_save_tokens_to_config()` - Persist tokens to disk
  - `get_enabled_groups()` - Includes local groups (m3u_account_count = 0)
  - Token expiry tracking with datetime comparison
- **API Endpoints**
  - `POST /api/collections/get-or-create` - Dynamic collection creation
  - `POST /api/dispatcharr/groups/<id>/channels` - Fetch group channels
  - `POST /api/dispatcharr/groups/<id>/create-rule` - Generate rule from group
  - Token restoration from config on startup
- **Efficient Channel Queries**
  - Uses `channel_group_id` parameter for exact filtering
  - Validates response format (list vs dict/paginated)
  - Handles both provider and local group lookups
  - Error handling with fallback to full auth

#### Frontend Architecture  
- **Removed Complexity** - Eliminated ~150 lines of preload code
  - No background preload on page load
  - No 60-minute auto-refresh interval
  - No localStorage caching (saveDispatcharrCache, loadDispatcharrCache)
  - No AbortController priority system
  - No concurrent pool processing
  - No progress indicators for preload
- **Simplified State Management**
  - Removed isPreloading state tracking
  - Removed preloadAbortController
  - Removed assigned_channels_count field (uses channel_count directly)
  - toggleDispatcharrView() just calls loadDispatcharrGroups()
  - filterDispatcharrGroups() uses channel_count from API

#### Error Handling
- **Better Logging** - More informative console output
  - Token refresh success/failure messages
  - Group type detection (Provider vs Local)
  - Channel lookup method (by ID vs by name)
  - Shared collection detection warnings
  - Additive mode activation notices
- **Graceful Degradation**
  - Falls back to full auth if token refresh fails
  - Shows helpful error messages to user
  - Validates all API responses before processing
  - Handles missing or invalid data gracefully

### 🐛 Bug Fixes

#### Critical Fixes
- **Channel Count Accuracy** - Fixed incorrect channel display
  - Old: Showed 6 channels when group had 1
  - Issue: Filtering by stream IDs found channels that shared streams
  - Fix: Query by `channel_group_id` parameter for exact results
  - Result: Accurate 1:1 group-to-channel mapping
- **Variable Name Error** - Fixed rule creation crash
  - Error: `name 'group' is not defined`
  - Location: `create_rule_from_dispatcharr_group()`
  - Fix: Changed `group['name']` to `target_group['name']`
  - Lines 1489, 1495 in main.py
- **JavaScript Syntax** - Fixed duplicate function
  - Error: `try:` instead of `try {`
  - Removed duplicate `cloneRule()` function
  - Kept original implementation
- **Python Indentation** - Fixed sync_rule else statement
  - Error: Misaligned `else:` at line 631
  - Fixed indentation to match parent `if`
  - Service now starts correctly

#### Minor Fixes
- **Collection Dropdown** - Added "Create New" option
  - Now visible in all rule creation flows
  - Separator line for clarity
  - Works with Dispatcharr rule creation
- **Token Caching** - Fixed Response object iteration
  - Error: `'Response' object is not iterable`
  - Fix: Call `api.get_collections()` instead of route `get_collections()`
  - Proper separation of Flask routes and API methods

### 📊 Performance Metrics

#### Speed Improvements
- **Initial Load** - 40s → 1s (40x faster)
  - Removed preload of 241 groups
  - Server-side filtering to ~50 groups
  - On-demand channel fetching
- **Token Overhead** - 500ms → 50ms per request (10x faster)
  - Token refresh instead of re-auth
  - Cached tokens persist across restarts
  - Reduced API calls by 90%
- **Channel Lookup** - More accurate and faster
  - Direct query by group ID
  - No need to filter thousands of channels
  - Exact results every time

#### Code Reduction
- **Lines Removed** - ~150 lines of preload code
  - Simpler architecture
  - Easier to maintain
  - Fewer edge cases
  - Better performance

### 📝 Documentation Updates


#### Updated Docs
- **README** - v2.0 feature highlights
- **CHANGELOG** - Complete v2.0 changes
- **Quick Start** - Dispatcharr environment variables
- **Advanced Features** - New sections for v2.0

### 🔄 Migration from v1.2

#### Automatic Compatibility
- All existing rules continue to work
- No manual migration required
- Rules file format unchanged
- Collections unaffected

#### New Optional Features
- Dispatcharr integration (opt-in)
- Collection creation (available when needed)
- Shared collection protection (automatic)
- All v1.2 features still available

#### Configuration
- Add optional Dispatcharr environment variables
- Or configure from Settings page
- Existing DVR_URL still required
- No breaking changes

---

## [1.2.0] - 2026-02-23

See [CHANGELOG_v1_2_0.md](Documentation/CHANGELOG_v1_2_0.md) for v1.2.0 changes.

---

## Version History

- **2.2.0** (2026-11-12) - Smarter Events Last sorting, Curato Command Center endpoint
- **2.0.0** (2026-02-25) - Dispatcharr integration, shared collections, dynamic collection creation
- **1.2.0** (2026-02-23) - Import/export, groups, scheduling, templates
- **1.1.0** (2025-12-15) - Pattern builder, live preview, source filtering
- **1.0.0** (2025-11-01) - Initial release
