#!/usr/bin/env python3
"""
Dispatcharr API Client
Handles authentication and API calls to Dispatcharr IPTV management system
"""
import json
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DispatcharrClient:
    """Client for Dispatcharr API interactions"""
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize Dispatcharr client
        
        Args:
            base_url: Dispatcharr server URL (e.g., http://10.0.60.51:9191)
            username: Dispatcharr username
            password: Dispatcharr password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Dispatcharr and get access tokens
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/accounts/token/"
            
            # Send as JSON with explicit content-type
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            logger.info(f"Attempting authentication to {url}")
            logger.info(f"Username: '{self.username}' (length: {len(self.username)})")
            logger.info(f"Password: {'*' * len(self.password)} (length: {len(self.password)})")
            logger.info(f"Payload: {json.dumps({k: v if k != 'password' else '***' for k, v in payload.items()})}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            # Log the response for debugging
            logger.info(f"Auth response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Auth response body: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access')
            self.refresh_token = data.get('refresh')
            
            if not self.access_token:
                logger.error("No access token in response")
                return False
            
            # JWT tokens typically expire in 30 minutes, set expiry
            self.token_expires_at = datetime.now() + timedelta(minutes=25)
            
            logger.info("Successfully authenticated with Dispatcharr")
            
            # Save tokens to config for reuse
            self._save_tokens_to_config()
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Dispatcharr authentication failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            return False
    
    def _save_tokens_to_config(self):
        """Save current tokens to config file for persistence"""
        try:
            # Import here to avoid circular dependency
            from main import load_dispatcharr_config, save_dispatcharr_config
            
            config = load_dispatcharr_config()
            config['access_token'] = self.access_token
            config['refresh_token'] = self.refresh_token
            if self.token_expires_at:
                config['token_expires_at'] = self.token_expires_at.isoformat()
            save_dispatcharr_config(config)
            logger.debug("Saved tokens to config")
        except Exception as e:
            logger.warning(f"Failed to save tokens to config: {e}")
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token
        
        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            logger.warning("No refresh token available, must re-authenticate")
            return self.authenticate()
        
        try:
            url = f"{self.base_url}/api/accounts/token/refresh/"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                "refresh": self.refresh_token
            }
            
            logger.info("Refreshing access token...")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                
                if not self.access_token:
                    logger.error("No access token in refresh response")
                    return self.authenticate()
                
                # JWT tokens typically expire in 30 minutes, set expiry
                self.token_expires_at = datetime.now() + timedelta(minutes=25)
                
                logger.info("Successfully refreshed access token")
                
                # Save updated tokens to config
                self._save_tokens_to_config()
                
                return True
            else:
                logger.warning(f"Token refresh failed with status {response.status_code}, re-authenticating...")
                return self.authenticate()
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Token refresh failed: {e}, re-authenticating...")
            return self.authenticate()
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid access token
        
        Returns:
            True if authenticated, False otherwise
        """
        # If no token, must authenticate
        if not self.access_token:
            logger.info("No access token, authenticating...")
            return self.authenticate()
        
        # If token expired, try to refresh first
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            logger.info("Token expired, attempting refresh...")
            return self.refresh_access_token()
        
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        return {
            'accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
    
    def get_m3u_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all M3U accounts from Dispatcharr
        
        Returns:
            List of M3U account dictionaries
        """
        if not self._ensure_authenticated():
            return []
        
        try:
            url = f"{self.base_url}/api/m3u/accounts/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            accounts = response.json()
            logger.info(f"Retrieved {len(accounts)} M3U accounts")
            return accounts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get M3U accounts: {e}")
            return []
    
    def get_all_groups(self) -> List[Dict[str, Any]]:
        """
        Get all channel groups from Dispatcharr
        
        Returns:
            List of channel group dictionaries
        """
        if not self._ensure_authenticated():
            return []
        
        try:
            url = f"{self.base_url}/api/channels/groups/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            groups = response.json()
            logger.info(f"Retrieved {len(groups)} channel groups")
            return groups
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get channel groups: {e}")
            return []
    
    def get_group_details(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific channel group
        
        Args:
            group_id: ID of the channel group
            
        Returns:
            Group details dictionary or None if failed
        """
        if not self._ensure_authenticated():
            return None
        
        try:
            url = f"{self.base_url}/api/channels/groups/{group_id}/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get group {group_id} details: {e}")
            return None
    
    def get_enabled_groups(self) -> List[Dict[str, Any]]:
        """
        Get all enabled channel groups with active M3U accounts AND local groups
        Filters for: is_active=true, enabled=true, OR m3u_account_count=0 with channel_count > 0
        
        Returns:
            List of enabled group dictionaries with enhanced info
        """
        # Get all groups
        all_groups = self.get_all_groups()
        if not all_groups:
            logger.warning("No channel groups found")
            return []
        
        enabled_groups = []
        
        # First, add local groups (m3u_account_count = 0)
        for group in all_groups:
            m3u_account_count = group.get('m3u_account_count', 0)
            channel_count = group.get('channel_count', 0)
            
            # Local groups: no M3U accounts, but have channels
            if m3u_account_count == 0 and channel_count > 0:
                enabled_groups.append({
                    'id': group['id'],
                    'name': group['name'],
                    'channel_count': channel_count,
                    'm3u_account_count': 0,
                    'm3u_account_name': '',
                    'm3u_account_id': None,
                    'auto_channel_sync': False,  # Not applicable for local groups
                    'auto_sync_channel_start': 0,
                    'is_stale': False,
                    'last_seen': '',
                    'custom_properties': {}
                })
        
        # Get M3U accounts for provider groups
        accounts = self.get_m3u_accounts()
        if not accounts:
            logger.warning("No M3U accounts found, returning local groups only")
            logger.info(f"Found {len(enabled_groups)} local groups with channels")
            return enabled_groups
        
        # Create lookup for groups by ID
        groups_by_id = {group['id']: group for group in all_groups}
        
        # Create lookup for active accounts by ID
        active_accounts = {acc['id']: acc for acc in accounts if acc.get('is_active', False)}
        
        # Add provider groups (from M3U accounts)
        for account in active_accounts.values():
            account_name = account.get('name', 'Unknown')
            account_id = account['id']
            
            # Get channel_groups array from this account
            channel_group_links = account.get('channel_groups', [])
            
            for link in channel_group_links:
                # Check if this link is enabled
                if not link.get('enabled', False):
                    continue
                
                # Get the group ID from the link
                group_id = link.get('channel_group')
                if not group_id:
                    continue
                
                # Get the full group data
                group = groups_by_id.get(group_id)
                if not group:
                    logger.warning(f"Group {group_id} not found in groups list")
                    continue
                
                # Filter: only include groups with channel_count > 0
                channel_count = group.get('channel_count', 0)
                if channel_count <= 0:
                    continue
                
                # Build enhanced group info
                enabled_groups.append({
                    'id': group['id'],
                    'name': group['name'],
                    'channel_count': channel_count,
                    'm3u_account_count': group.get('m3u_account_count', 0),
                    'm3u_account_name': account_name,
                    'm3u_account_id': account_id,
                    'auto_channel_sync': link.get('auto_channel_sync', False),
                    'auto_sync_channel_start': link.get('auto_sync_channel_start', 0),
                    'is_stale': link.get('is_stale', False),
                    'last_seen': link.get('last_seen', ''),
                    'custom_properties': link.get('custom_properties', {})
                })
        
        logger.info(f"Found {len(enabled_groups)} enabled groups with channels ({len([g for g in enabled_groups if g['m3u_account_count'] == 0])} local)")
        return enabled_groups
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Dispatcharr
        
        Returns:
            Dictionary with test results
        """
        result = {
            'success': False,
            'message': '',
            'accounts_count': 0,
            'groups_count': 0,
            'enabled_groups_count': 0
        }
        
        # Test authentication
        if not self.authenticate():
            result['message'] = 'Authentication failed - check URL, username, and password'
            return result
        
        # Test getting accounts
        accounts = self.get_m3u_accounts()
        result['accounts_count'] = len(accounts)
        
        # Test getting groups
        groups = self.get_all_groups()
        result['groups_count'] = len(groups)
        
        # Test getting enabled groups
        enabled = self.get_enabled_groups()
        result['enabled_groups_count'] = len(enabled)
        
        result['success'] = True
        result['message'] = f'Successfully connected! Found {len(enabled)} enabled groups'
        
        return result
