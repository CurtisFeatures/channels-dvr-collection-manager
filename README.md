```markdown
[![Docker Pulls](https://img.shields.io/docker/pulls/CurtisFeatures/channels-collection-manager)](https://hub.docker.com/r/yourusername/channels-collection-manager)
[![GitHub Stars](https://img.shields.io/github/stars/CurtisFeatures/channels-collection-manager)](https://github.com/yourusername/channels-collection-manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

# Channels DVR Collection Manager

A web-based service to dynamically manage Channels DVR channel collections using pattern matching and regex. Automatically adds and removes channels based on configurable rules.

## Features

- 🎯 **Pattern Matching**: Use regex patterns to match channels by name, number, or EPG data
- 🔄 **Automatic Sync**: Scheduled synchronization to keep collections up-to-date
- 🌐 **Web Interface**: Easy-to-use web UI for managing rules
- 👁️ **Preview**: See which channels match your patterns before applying
- 📊 **Sync Reports**: View detailed results of each sync operation
- 🐳 **Docker Ready**: Easy deployment with Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Channels DVR server running on your network
- Access to your Channels DVR API (usually port 8089)

### Installation

1. **Clone or download this repository**

2. **Edit `docker-compose.yml`**
   
   Update the `DVR_URL` environment variable to point to your Channels DVR server:
   ```yaml
   environment:
     - DVR_URL=http://192.168.1.100:8089  # Change to your DVR IP
   ```

3. **Build and start the container**
   ```bash
   docker-compose up -d
   ```

4. **Access the web interface**
   
   Open your browser and go to: `http://localhost:5000`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DVR_URL` | `http://channelsdvr:8089` | URL to your Channels DVR server |
| `SYNC_INTERVAL_MINUTES` | `60` | How often to sync collections (in minutes) |
| `SECRET_KEY` | `dev-secret-key` | Flask secret key for sessions |

### Docker Compose for Unraid

For Unraid users, add this to your docker-compose file or use the Unraid Docker UI:

```yaml
version: '3.8'

services:
  channels-collection-manager:
    image: ghcr.io/CurtisFeatures/channels-collection-manager:latest
    container_name: channels-collection-manager
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - DVR_URL=http://192.168.1.100:8089
      - SYNC_INTERVAL_MINUTES=60
      - SECRET_KEY=your-random-secret-key-here
    volumes:
      - /mnt/user/appdata/channels-collection-manager:/config
```

## Usage

### Important: Create Collections First

**Before creating rules**, you must create channel collections in Channels DVR:

1. Open your Channels DVR web interface (usually `http://your-dvr-ip:8089`)
2. Go to **Live TV → Channel Collections**
3. Click **"New Collection"**
4. Give it a name (e.g., "Sports", "News", "Local HD")
5. You can leave it empty - the rules will populate it automatically
6. Save the collection

Repeat this for each collection you want to manage automatically. Then come back to the Collection Manager web interface and click the refresh button to see your collections.

### Creating a Rule

1. Click **"+ Add Rule"** in the web interface
2. Enter a **Rule Name** (e.g., "Sports Channels")
3. Select the **Collection** to manage
4. Choose **Match Types**:
   - **Channel Name**: Match against the channel's display name
   - **Channel Number**: Match against the channel number
   - **EPG**: Match against callsign and affiliate data
5. Add **Patterns** (regex):
   - Click "Add" after entering each pattern
   - Examples:
     - `^ESPN` - Channels starting with "ESPN"
     - `^FOX Sports` - Channels starting with "FOX Sports"
     - `HBO|Showtime|Starz` - Any channel containing HBO, Showtime, or Starz
     - `\d+-\d+` - Channels with numbers like "2-1" or "5-3"
6. Click **"Preview Matches"** to see which channels will be included
7. Click **"Save Rule"**

### Pattern Examples

Here are some useful regex patterns:

| Pattern | Matches |
|---------|---------|
| `^ESPN` | ESPN, ESPN2, ESPNEWS, etc. |
| `^NBC\|^CBS\|^ABC\|^FOX` | Major broadcast networks |
| `HD$` | Channels ending with "HD" |
| `\d+-\d+` | Sub-channels (2-1, 5-3, etc.) |
| `HBO\|Showtime\|Starz` | Premium channels |
| `Sports?\|NFL\|NBA\|MLB\|NHL` | Sports-related channels |
| `News` | Any channel with "News" in the name |
| `^[0-9]{1,2}$` | Single or double-digit channel numbers |
| `Local` | Channels with "Local" in the name |

### Managing Rules

- **Edit**: Click "Edit" on any rule to modify it
- **Delete**: Click "Delete" to remove a rule
- **Enable/Disable**: Use the "Enabled" checkbox when editing
- **Preview**: Use the preview feature to test patterns before saving

### Syncing

- **Automatic**: Runs every hour (configurable)
- **Manual**: Click "🔄 Sync Now" at the top of the page
- **Results**: View sync results at the bottom of the page

## How It Works

1. **Rule Evaluation**: On each sync, the service:
   - Fetches all available channels from your Channels DVR
   - Applies each enabled rule's patterns
   - Identifies matching channels

2. **Collection Update**: For each collection:
   - Compares current channels with matched channels
   - Adds new matching channels
   - Removes channels that no longer match
   - Updates the collection via the Channels DVR API

3. **Reporting**: After each sync:
   - Shows which channels were added/removed
   - Displays any errors
   - Updates the dashboard

## API Endpoints

The service exposes a REST API for advanced users:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Get system status |
| `/api/rules` | GET | List all rules |
| `/api/rules` | POST | Create a new rule |
| `/api/rules/<id>` | PUT | Update a rule |
| `/api/rules/<id>` | DELETE | Delete a rule |
| `/api/channels` | GET | List all channels |
| `/api/collections` | GET | List all collections |
| `/api/preview` | POST | Preview rule matches |
| `/api/sync` | POST | Trigger manual sync |
| `/api/sync/status` | GET | Get last sync results |

## Troubleshooting

### "Failed to fetch channels from DVR"

- Verify the `DVR_URL` is correct
- Ensure your Channels DVR is running
- Check that port 8089 is accessible
- Try accessing `http://your-dvr-ip:8089/devices` in a browser

### Rules not syncing

- Check that rules are **Enabled**
- Verify your regex patterns are valid
- Use the **Preview** feature to test patterns
- Check the sync results for errors

### No channels matching

- Double-check your patterns using the preview feature
- Try broader patterns first, then narrow down
- Remember that patterns are case-insensitive
- Check the actual channel names in the Channels DVR web interface

### Container won't start

- Check Docker logs: `docker-compose logs channels-collection-manager`
- Verify all environment variables are set correctly
- Ensure the config volume path exists and is writable

## File Locations

- **Configuration**: `/config/rules.json` (inside container)
- **Logs**: Check Docker logs with `docker-compose logs -f`

## Advanced Usage

### Multiple Match Types

You can combine match types for more precise filtering:
- Enable both "Name" and "Number" to match either
- Use EPG matching for callsign/affiliate based rules

### Complex Patterns

Combine multiple patterns for OR logic:
```
Pattern 1: ^ESPN
Pattern 2: ^FOX Sports
Pattern 3: NFL
```
This will match channels starting with "ESPN", starting with "FOX Sports", OR containing "NFL".

### Excluding Channels

Use negative lookahead in regex:
```
^(?!.*Kids)HBO
```
This matches HBO channels but excludes those with "Kids" in the name.

## Building from Source

```bash
# Clone the repository
git clone <repo-url>
cd channels-collection-manager

# Build the Docker image
docker build -t channels-collection-manager .

# Run with docker-compose
docker-compose up -d
```

## Support

For issues, feature requests, or questions, please open an issue on GitHub.

## License

MIT License - feel free to use and modify as needed.

## Credits

Built for the Channels DVR community. Channels DVR is a product of Fancy Bits.
