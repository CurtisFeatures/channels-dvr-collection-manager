# Creating Your First Rule - Quick Guide

Based on your setup, you have these collections:
- Sky Sports Plus (Slug: 8) - 60 channels
- PDC Darts (Slug: 9) - 2 channels
- Sky Sports (Slug: 11) - 16 channels
- Movies (Slug: 12) - 11 channels

## Test Rule #1: Add All Channels with "Sport" in Name

Let's create a simple rule to test the system:

1. Click **"+ Add Rule"** in the Collection Rules section

2. Fill in the form:
   - **Rule Name:** `Test - All Sports Channels`
   - **Collection:** Select `Sky Sports Plus` (or any collection you want to test)
   - **Match Types:** 
     - ✓ Channel Name
   - **Patterns:** Click in the pattern input box and add:
     - Type: `Sport`
     - Click "Add"
   - **Enabled:** ✓ Make sure this is checked!

3. Click **"Preview Matches"**
   - You should see channels that have "Sport" in their name
   - This will show you channel IDs and names

4. If the preview looks good, click **"Save Rule"**

5. Click **"🔄 Sync Now"** at the top

6. Check "Last Sync Results" section - you should see:
   ```
   Sky Sports Plus
   📊 Total: X  ➕ Added: X  ➖ Removed: 0
   ```

## Test Rule #2: Match Specific Channel IDs

If you want to match specific channels by ID:

1. First, click "View Channels ▼" on one of your collections to see channel IDs

2. Create a new rule:
   - **Pattern:** Use the exact channel ID you see (e.g., `sky-sports-main` or similar)
   - **Match Type:** Channel Name
   - This will match that specific channel

## Test Rule #3: Match by Number Pattern

If you want all channels in a number range:

1. **Pattern:** `^[0-9]+$` (matches any number)
2. **Match Type:** ✓ Channel Number

## Troubleshooting Your 404 Errors

The 404 errors on /devices and /dvr/collections/channels are unusual since:
- Collections ARE loading (you can see them)
- Channels are found (340 channels)

This might be:
1. **DVR version difference** - Older/newer versions might use different paths
2. **Permissions/CORS issue** - Direct requests failing but proxied ones working
3. **URL path issue** - Missing or extra slashes

**Don't worry!** The fact that you see collections means the app IS working. The test connection function just can't verify it directly.

## What to Do Next

1. **Create a test rule** using the guide above
2. **Sync it**
3. **Verify in Channels DVR** that channels were added to the collection

If sync works and channels appear in your DVR collection, then everything is functioning correctly despite the 404 errors in the test!

## Expected Sync Log Output

When you sync, your Docker logs should show:

```
INFO:__main__:Starting sync of all collections
INFO:__main__:Fetching all channels from DVR...
INFO:__main__:Found 340 channels from DVR
INFO:__main__:Processing 1 active rule(s) out of 1 total
INFO:__main__:Processing rule: Test - All Sports Channels for collection 8
INFO:__main__:Rule 'Test - All Sports Channels' matched 15 channels
INFO:__main__:✓ Updated collection 'Sky Sports Plus': 15 channels (+15, -0)
INFO:__main__:Sync completed: 1 collections updated, 0 errors
```

If you see this, it's working!
