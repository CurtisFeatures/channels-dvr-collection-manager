# Unraid Installation Guide

## Method 1: Docker Compose (Recommended)

1. **Enable Docker Compose on Unraid**
   - Install the "Compose Manager" plugin from Community Applications
   - Or use the command line if you're comfortable with it

2. **Create the compose directory**
   ```bash
   mkdir -p /mnt/user/appdata/channels-collection-manager
   cd /mnt/user/appdata/channels-collection-manager
   ```

3. **Create docker-compose.yml**
   
   Create a file named `docker-compose.yml` with this content:
   
   ```yaml
   version: '3.8'

   services:
     channels-collection-manager:
       image: channels-collection-manager:latest
       build: .
       container_name: channels-collection-manager
       restart: unless-stopped
       ports:
         - "5000:5000"
       environment:
         - DVR_URL=http://192.168.1.100:8089  # Change to your Channels DVR IP
         - SYNC_INTERVAL_MINUTES=60
         - SECRET_KEY=your-random-secret-key-here
       volumes:
         - /mnt/user/appdata/channels-collection-manager/config:/config
   ```

4. **Copy the application files**
   - Copy all files from this repository to `/mnt/user/appdata/channels-collection-manager/`

5. **Build and start**
   ```bash
   cd /mnt/user/appdata/channels-collection-manager
   docker-compose up -d
   ```

6. **Access the interface**
   - Open: `http://your-unraid-ip:5000`

## Method 2: Unraid Docker UI

If you prefer using the Unraid web interface:

1. **Go to Docker tab in Unraid**

2. **Add Container**
   - **Name**: `channels-collection-manager`
   - **Repository**: (You'll need to build and push to Docker Hub first, or use the build method)
   - **Network Type**: Bridge
   
3. **Port Mappings**
   - **Container Port**: 5000
   - **Host Port**: 5000
   - **Connection Type**: TCP

4. **Volume Mappings**
   - **Container Path**: `/config`
   - **Host Path**: `/mnt/user/appdata/channels-collection-manager/config`
   - **Access Mode**: Read/Write

5. **Environment Variables**
   
   Add these environment variables:
   
   | Variable | Value |
   |----------|-------|
   | `DVR_URL` | `http://192.168.1.100:8089` (your DVR IP) |
   | `SYNC_INTERVAL_MINUTES` | `60` |
   | `SECRET_KEY` | (generate a random string) |

6. **Apply and Start**

## Finding Your Channels DVR IP

Your Channels DVR server typically runs on port 8089. To find it:

1. Check your Channels DVR settings
2. Try accessing `http://channelsdvr:8089` (hostname)
3. Or use the IP address: `http://192.168.1.XXX:8089`

You can test the URL by opening it in a browser - you should see the Channels DVR API response.

## Checking Logs

View container logs in Unraid:
```bash
docker logs channels-collection-manager
```

Or use the Unraid Docker UI to view logs.

## Updating

### Docker Compose method:
```bash
cd /mnt/user/appdata/channels-collection-manager
docker-compose pull
docker-compose up -d
```

### Docker UI method:
1. Stop the container
2. Remove it
3. Re-add with the same configuration
4. Start

## Troubleshooting

### Container won't start
1. Check logs: `docker logs channels-collection-manager`
2. Verify the config directory exists and is writable
3. Check that port 5000 isn't already in use

### Can't connect to DVR
1. Verify the DVR_URL is correct
2. Try accessing the URL in a browser
3. Make sure both containers are on the same network (if using custom bridge)

### Changes not persisting
- Make sure the volume mapping is correct
- Check permissions on the host path
- Verify the container is writing to `/config`

## Network Considerations

If your Channels DVR is on a different VLAN or network segment:
1. Make sure the container can route to it
2. Consider using the DVR's IP address instead of hostname
3. Check firewall rules

## Performance Tips

- For large channel lists, consider increasing sync interval
- Monitor CPU usage during sync operations
- The config file is small and shouldn't impact storage

## Backup

To backup your rules:
```bash
cp /mnt/user/appdata/channels-collection-manager/config/rules.json ~/backup/
```

Restore:
```bash
cp ~/backup/rules.json /mnt/user/appdata/channels-collection-manager/config/
docker restart channels-collection-manager
```
