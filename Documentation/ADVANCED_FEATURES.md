# Advanced Features Guide

## Channel Number Ranges

You can now match channels by number ranges instead of just patterns!

### How to Use

**Pattern Format:** `START-END` (where START and END are numbers)

**Examples:**
- `100-200` - Matches channels 100 through 200
- `5.1-5.9` - Matches subchannels 5.1, 5.2, 5.3, etc.
- `1-99` - Matches channels 1 through 99

### Creating a Number Range Rule

1. Click "+ Add Rule"
2. **Name:** `Channels 100-299`
3. **Collection:** Select your collection
4. **Match Types:** Check ✓ **Channel Number** (important!)
5. **Patterns:** Add `100-299`
6. **Sort Order:** Select `Channel Number (Low to High)`
7. **Save**

The app will automatically detect patterns like `100-200` as number ranges and match accordingly.

### Combining Ranges with Other Patterns

You can mix number ranges with regular patterns:

**Pattern 1:** `100-200`
**Pattern 2:** `ESPN`

This will match:
- All channels between 100-200, AND
- Any channel with "ESPN" in the name

---

## Channel Sort Orders

Control how channels are arranged in your collections!

### Sort Options

#### **No sorting (default)**
- Channels added in default order (alphabetical by ID)
- Good for most use cases

#### **Alphabetically (A-Z)**
- Sorts channels by name: A → Z
- Example: BBC, CNN, ESPN, FOX, NBC

#### **Alphabetically (Z-A)**
- Sorts channels by name: Z → A  
- Example: NBC, FOX, ESPN, CNN, BBC

#### **Channel Number (Low to High)**
- Sorts by channel number: 1, 2, 3... 100, 101...
- Perfect for numbered channel ranges
- Example: 2.1, 5.1, 7.1, 100.1, 200.1

#### **Channel Number (High to Low)**
- Sorts by channel number descending: 999, 500, 100... 5, 2, 1
- Example: 200.1, 100.1, 7.1, 5.1, 2.1

#### **Events Last (Named channels first)** ⭐ NEW!
- Puts "Event XX" channels at the end
- Regular named channels appear first, sorted A-Z
- Event channels appear last, sorted A-Z
- Perfect for IPTV channels with placeholder names

### Events Last - Use Case

Many IPTV services use channel names like "Event 01", "Event 02" as placeholders. When a game or show is on, the name changes to the actual program name.

**Example Before Sorting:**
1. Event 01
2. Football: Arsenal vs Chelsea
3. Event 04
4. Rugby: England vs Wales
5. Event 03

**After "Events Last" Sorting:**
1. Football: Arsenal vs Chelsea
2. Rugby: England vs Wales
3. Event 01
4. Event 03
5. Event 04

This keeps your real content at the top, with placeholder events at the bottom!

### How to Set Sort Order

When creating or editing a rule:
1. Scroll to **"Channel Sort Order"** dropdown
2. Select your preferred sorting method
3. Save the rule
4. Run sync - channels will be arranged in the specified order

---

## Complete Example: Sports Channels with Events Last

Let's create a comprehensive sports rule:

**Rule Name:** `All Sports Channels`

**Collection:** `Sports` (slug: 8)

**Match Types:**
- ✓ Channel Name
- ✓ EPG (Callsign/Affiliate)

**Patterns:**
- `Sport`
- `Football`
- `Soccer`
- `Rugby`
- `Cricket`
- `Golf`
- `Tennis`
- `^ESPN`
- `^FOX Sports`
- `Sky Sports`

**Sort Order:** `Events Last (Named channels first)`

**Result:**
Your sports collection will have:
1. All named sports channels (BBC Sport, ESPN, FOX Sports, etc.) - sorted A-Z
2. Followed by Event channels (Event 01, Event 02, etc.) - sorted A-Z

---

## Pattern Tips for Number Ranges

### Single Channel
Pattern: `100`
Match Type: Channel Number
Result: Only channel 100

### Range of Channels  
Pattern: `100-200`
Match Type: Channel Number
Result: Channels 100, 101, 102... 199, 200

### Subchannels in Range
Pattern: `5.1-5.9`
Match Type: Channel Number
Result: 5.1, 5.2, 5.3, etc.

### Multiple Ranges
Pattern 1: `100-200`
Pattern 2: `500-600`
Match Type: Channel Number
Result: Channels 100-200 AND 500-600

### Range + Name Pattern
Pattern 1: `100-200`
Pattern 2: `HD$`
Match Type: Channel Number + Channel Name
Result: Channels 100-200 that have "HD" at the end of their name

---

## Common Sorting Scenarios

### Scenario 1: Local Broadcast Channels
**Want:** Channels sorted by number (2, 5, 7, 11, etc.)
**Pattern:** `2|5|7|11|13` or use names
**Sort:** `Channel Number (Low to High)`

### Scenario 2: Premium Movie Channels
**Want:** HBO, Showtime, etc. alphabetically, events at end
**Pattern:** `HBO|Showtime|Starz|Cinemax`
**Sort:** `Events Last`

### Scenario 3: Sports PPV Events
**Want:** All sports PPV channels, numbered order
**Pattern:** `400-499`
**Match:** Channel Number
**Sort:** `Channel Number (Low to High)`

### Scenario 4: News Networks
**Want:** Alphabetical list of news channels
**Pattern:** `News|CNN|MSNBC|FOX News|BBC News`
**Sort:** `Alphabetically (A-Z)`

---

## Testing Your Sort Order

1. Create a rule with your desired sort order
2. Click **"Preview Matches"**
3. The preview will show channels in the order they'll appear
4. Adjust sort order if needed
5. Save and sync

Note: Preview shows channels sorted, so you can verify before syncing!

---

## Troubleshooting

### Channels Not Sorting
- Make sure you've selected a sort order (not "No sorting")
- After changing sort order, you must click "Sync Now" to apply
- Check Docker logs for any sorting errors

### Number Range Not Working  
- Ensure Match Type includes "Channel Number"
- Verify pattern format: `START-END` with no spaces
- Check that your channels actually have numbers in that range

### Events Not Sorting Correctly
- "Events Last" specifically looks for channels starting with "Event"
- Case insensitive: "event", "Event", "EVENT" all work
- If your placeholder channels have different names, contact us for custom logic

---

## Advanced: Combining Multiple Features

**Goal:** Create a comprehensive sports collection
- Channels 200-299 (sports block)
- Any channel with "Sport" in name
- ESPN, FOX Sports family
- Sorted with real channels first, events last

**Setup:**
1. **Patterns:**
   - `200-299`
   - `Sport`
   - `ESPN`
   - `FOX Sports`

2. **Match Types:**
   - ✓ Channel Name
   - ✓ Channel Number

3. **Sort Order:** `Events Last`

4. **Result:**
   - Named sports channels first (A-Z)
   - Event 01, Event 02, etc. last
   - Perfectly organized sports collection!

---

## Performance Notes

- Sorting happens during sync, not during preview
- No performance impact on large channel lists
- Sort order is applied every sync (keeps collection organized even as channels change)
- If you change sort order, next sync will re-arrange all channels
