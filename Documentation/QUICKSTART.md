# Quick Start Debugging Guide

## "No collections synced" - Step by Step Fix

If you're seeing "No collections synced" after clicking "Sync Now", follow these steps:

### Step 1: Test DVR Connection

1. Click the **"🔌 Test DVR Connection"** button at the top
2. You should see a popup with:
   ```
   ✅ Devices: Found X device(s)
   ✅ Collections: Found X collection(s)
   ✅ Channels: Found X channel(s)
   ```

**If you see ❌ errors:**
- Check your `DVR_URL` in docker-compose.yml
- Make sure Channels DVR is running
- Try accessing the DVR URL in your browser
- See TROUBLESHOOTING.md for detailed connection help

### Step 2: Check Collections Exist

1. Look at the **"📺 Current Collections in Channels DVR"** section
2. You should see at least one collection listed

**If no collections appear:**
- Collections must be created in Channels DVR first!
- Open Channels DVR web interface: `http://your-dvr-ip:8089`
- Go to Live TV → Channel Collections
- Click "New Collection" and create one
- Come back and click the refresh button

### Step 3: Create a Rule

1. Click **"+ Add Rule"** in the Collection Rules section
2. Fill in:
   - **Rule Name**: e.g., "Test Rule"
   - **Collection**: Select from dropdown (should have your collections now)
   - **Match Types**: Check at least "Channel Name"
   - **Patterns**: Add a simple pattern like `ESPN` or `News`
3. Click **"Preview Matches"** to verify channels are matched
4. Check **"Enabled"**
5. Click **"Save Rule"**

**If collection dropdown is empty:**
- Collections don't exist yet - see Step 2
- DVR connection failed - see Step 1

**If preview shows 0 channels:**
- Try a broader pattern (just `E` will match anything with E)
- Check the "Current Collections" section to see actual channel names
- Adjust your pattern to match those names

### Step 4: Run Sync

1. Click **"🔄 Sync Now"**
2. Wait a few seconds
3. Check the **"Last Sync Results"** section at the bottom

**You should see:**
```
Collection Name
📊 Total: 10  ➕ Added: 10  ➖ Removed: 0
```

### Step 5: Verify in Channels DVR

1. Go back to Channels DVR: `http://your-dvr-ip:8089`
2. Settings → Channel Collections
3. Open the collection you created a rule for
4. You should see the channels that matched your pattern!

## Common Issues and Quick Fixes

### Issue: "No enabled rules found"
**Fix:** Create at least one rule and make sure "Enabled" is checked

### Issue: "Collection 'XXX' not found"
**Fix:** The collection was deleted from Channels DVR - create it again or update your rule

### Issue: "Failed to fetch channels from DVR"
**Fix:** 
- Verify DVR_URL is correct
- Check Channels DVR is running
- Test with: `curl http://your-dvr-ip:8089/devices`

### Issue: Preview shows channels but sync shows 0
**Fix:** 
- Check Docker logs: `docker logs channels-collection-manager`
- Look for error messages about collection updates
- Verify collection ID matches exactly

## Checking Docker Logs

See what's happening behind the scenes:
```bash
docker logs -f channels-collection-manager
```

You should see logs like:
```
INFO:__main__:Starting sync of all collections
INFO:__main__:Fetching all channels from DVR...
INFO:__main__:Found 150 channels from DVR
INFO:__main__:Processing 1 active rule(s) out of 1 total
INFO:__main__:Processing rule: Test Rule for collection sports-collection
INFO:__main__:Rule 'Test Rule' matched 25 channels
INFO:__main__:✓ Updated collection 'Sports': 25 channels (+25, -0)
```

## Still Not Working?

1. **Try the simplest possible rule:**
   - Pattern: Just the letter `a` (will match many channels)
   - Match Type: Channel Name only
   - Preview it first to confirm it works

2. **Check the exact collection ID:**
   - Look at "Current Collections" section
   - Note the exact "ID: xxx" shown under the collection name
   - Make sure your rule uses this exact ID

3. **Restart the container:**
   ```bash
   docker-compose restart
   ```

4. **Check the troubleshooting guide:**
   - See TROUBLESHOOTING.md for detailed help
   - Or create an issue with your Docker logs

## Success Checklist

- [ ] Test DVR Connection shows all ✅
- [ ] Collections appear in "Current Collections"
- [ ] Rule created with collection selected
- [ ] Preview shows matched channels
- [ ] Rule is Enabled (checkbox checked)
- [ ] Sync Now shows collections updated
- [ ] Channels appear in Channels DVR collection
