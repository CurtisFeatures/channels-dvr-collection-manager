#!/usr/bin/env python3
import os
import re
import json
import logging
import uuid
from datetime import datetime, time
from typing import List, Dict, Any, Set, Optional
from flask import Flask, render_template, request, jsonify, send_file
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import tempfile
from io import BytesIO

# Import Dispatcharr client
try:
    from dispatcharr_client import DispatcharrClient
except ImportError:
    from app.dispatcharr_client import DispatcharrClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Flask with absolute paths
app = Flask(__name__, 
            static_folder='/app/static',
            template_folder='/app/templates',
            static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configuration
DVR_URL = os.environ.get('DVR_URL', 'http://channelsdvr:8089')
CONFIG_FILE = '/config/rules.json'
DISPATCHARR_CONFIG_FILE = '/config/dispatcharr.json'
SETTINGS_FILE = '/config/settings.json'
SYNC_INTERVAL = int(os.environ.get('SYNC_INTERVAL_MINUTES', '60'))  # env var default


def load_app_settings() -> Dict[str, Any]:
    """Load application settings from settings file"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading app settings: {e}")
    return {}


def save_app_settings(settings: Dict[str, Any]) -> bool:
    """Save application settings to settings file"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving app settings: {e}")
        return False


def get_sync_interval() -> int:
    """Return effective global sync interval: settings file takes priority over env var"""
    settings = load_app_settings()
    return int(settings.get('sync_interval_minutes', SYNC_INTERVAL))



def is_rule_scheduled_now(rule: Dict[str, Any]) -> bool:
    """Check if rule should run based on schedule"""
    if not rule.get('schedule_enabled', False):
        return True  # No schedule = always active
    
    now = datetime.now()
    current_time = now.time()
    current_day = now.strftime('%A').lower()
    
    # Check days of week
    schedule_days = rule.get('schedule_days', [])
    if schedule_days and current_day not in schedule_days:
        return False
    
    # Check time window
    start_time_str = rule.get('schedule_start_time')
    end_time_str = rule.get('schedule_end_time')
    
    if start_time_str and end_time_str:
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        if start_time <= end_time:
            # Normal range (e.g., 09:00 - 17:00)
            return start_time <= current_time <= end_time
        else:
            # Overnight range (e.g., 22:00 - 06:00)
            return current_time >= start_time or current_time <= end_time
    
    return True


class ChannelsAPI:
    """Interface to Channels DVR API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def get_channels(self) -> List[Dict[str, Any]]:
        """Fetch all available channels"""
        try:
            response = requests.get(f"{self.base_url}/devices")
            devices = response.json()
            
            all_channels = []
            for device in devices:
                device_name = device.get('FriendlyName', 'Unknown')
                device_id = device.get('DeviceID', '')
                channels_response = requests.get(f"{self.base_url}/devices/{device['DeviceID']}/channels")
                if channels_response.status_code == 200:
                    channels = channels_response.json()
                    # Add device info to each channel
                    for channel in channels:
                        channel['_device_name'] = device_name
                        channel['_device_id'] = device_id
                    all_channels.extend(channels)
            
            return all_channels
        except Exception as e:
            logger.error(f"Error fetching channels: {e}")
            return []
    
    def get_collections(self) -> List[Dict[str, Any]]:
        """Fetch all channel collections using the correct endpoint"""
        try:
            # Use the correct collections endpoint
            response = requests.get(f"{self.base_url}/dvr/collections/channels")
            if response.status_code == 200:
                data = response.json()
                # This endpoint returns a list of collections
                if isinstance(data, list):
                    return data
                return []
            logger.warning(f"Failed to fetch collections: status {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error fetching collections: {e}")
            return []
    
    def get_collection(self, collection_slug: str) -> Dict[str, Any]:
        """Fetch a specific collection using slug"""
        try:
            # Use the correct collections endpoint with slug
            response = requests.get(f"{self.base_url}/dvr/collections/channels/{collection_slug}")
            if response.status_code == 200:
                return response.json()
            
            logger.warning(f"Collection {collection_slug} not found")
            return {}
        except Exception as e:
            logger.error(f"Error fetching collection {collection_slug}: {e}")
            return {}
    
    def update_collection(self, collection_slug: str, collection_data: Dict[str, Any]) -> bool:
        """Update a collection using the correct endpoint"""
        try:
            # Use PUT to update collection at the correct endpoint
            response = requests.put(
                f"{self.base_url}/dvr/collections/channels/{collection_slug}",
                json=collection_data
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating collection {collection_slug}: {e}")
            return False


class RuleManager:
    """Manages pattern matching rules for collections"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.rules = self.load_rules()
    
    def load_rules(self) -> List[Dict[str, Any]]:
        """Load rules from config file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading rules: {e}")
        return []
    
    def save_rules(self) -> bool:
        """Save rules to config file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.rules, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving rules: {e}")
            return False
    
    def add_rule(self, rule: Dict[str, Any]) -> bool:
        """Add a new rule"""
        rule['id'] = datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.rules.append(rule)
        return self.save_rules()
    
    def update_rule(self, rule_id: str, rule: Dict[str, Any]) -> bool:
        """Update an existing rule"""
        for i, r in enumerate(self.rules):
            if r.get('id') == rule_id:
                rule['id'] = rule_id
                self.rules[i] = rule
                return self.save_rules()
        return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        self.rules = [r for r in self.rules if r.get('id') != rule_id]
        return self.save_rules()
    
    def match_channel(self, channel: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Check if a channel matches a rule"""
        # First check source filters
        include_sources = rule.get('include_sources', [])
        exclude_sources = rule.get('exclude_sources', [])
        device_id = channel.get('_device_id', '')
        
        # If include sources specified, channel must be from one of them
        if include_sources and device_id not in include_sources:
            return False
        
        # If exclude sources specified, channel must NOT be from one of them
        if exclude_sources and device_id in exclude_sources:
            return False
        
        patterns = rule.get('patterns', [])
        match_types = rule.get('match_types', ['name'])
        
        # Expand comma-separated patterns (e.g., "101-105,107-108" -> ["101-105", "107-108"])
        expanded_patterns = []
        for pattern in patterns:
            if ',' in pattern and 'number' in match_types:
                # Split comma-separated patterns for number matching
                expanded_patterns.extend([p.strip() for p in pattern.split(',')])
            else:
                expanded_patterns.append(pattern)
        
        for pattern in expanded_patterns:
            try:
                # Check if pattern is a single number (e.g., "115")
                if pattern.replace('.', '').isdigit() and 'number' in match_types:
                    channel_num = channel.get('GuideNumber', '')
                    if channel_num:
                        try:
                            if float(channel_num) == float(pattern):
                                return True
                        except ValueError:
                            pass
                
                # Check if pattern is a channel number range (e.g., "100-200")
                elif '-' in pattern and pattern.replace('-', '').replace('.', '').isdigit():
                    # This is a number range
                    parts = pattern.split('-')
                    if len(parts) == 2:
                        try:
                            start = float(parts[0])
                            end = float(parts[1])
                            channel_num = channel.get('GuideNumber', '')
                            if channel_num:
                                # Convert channel number to float for comparison
                                try:
                                    num = float(channel_num)
                                    if start <= num <= end:
                                        return True
                                except ValueError:
                                    pass
                        except ValueError:
                            pass
                
                # Regular regex matching
                regex = re.compile(pattern, re.IGNORECASE)
                
                # Check channel name
                if 'name' in match_types:
                    channel_name = channel.get('GuideName', '')
                    if regex.search(channel_name):
                        return True
                
                # Check channel number
                if 'number' in match_types:
                    channel_number = str(channel.get('GuideNumber', ''))
                    # Use word boundaries to prevent partial matches (e.g., 400 shouldn't match 6400)
                    # Add word boundary if pattern is purely numeric
                    if pattern.replace('.', '').replace(',', '').isdigit():
                        # Pure number pattern - use exact word boundary matching
                        bounded_pattern = r'\b' + re.escape(pattern) + r'\b'
                        if re.search(bounded_pattern, channel_number):
                            return True
                    else:
                        # Non-numeric pattern - use normal regex
                        if regex.search(channel_number):
                            return True
                
                # Check EPG data (callsign, affiliate, etc)
                if 'epg' in match_types:
                    callsign = channel.get('Callsign', '')
                    affiliate = channel.get('Affiliate', '')
                    if regex.search(callsign) or regex.search(affiliate):
                        return True
                
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern}': {e}")
                continue
        
        return False
    
    def get_matching_channels(self, channels: List[Dict[str, Any]], rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all channels matching a rule"""
        matching = []
        for channel in channels:
            if self.match_channel(channel, rule):
                matching.append(channel)
        return matching


class SyncManager:
    """Manages synchronization of collections based on rules"""
    
    def __init__(self, api: ChannelsAPI, rule_manager: RuleManager):
        self.api = api
        self.rule_manager = rule_manager
        self.last_sync = None
        self.last_sync_results = {}
    
    def _sort_channels(self, channel_ids: List[str], channel_map: Dict[str, Dict], sort_order: str) -> List[str]:
        """Sort channel IDs based on the specified order"""
        import re  # Import at method level for all uses
        
        def get_sort_key(channel_id: str):
            channel = channel_map.get(channel_id, {})
            name = channel.get('GuideName', '')
            number = channel.get('GuideNumber', '')
            
            # Convert channel number to sortable format
            try:
                num_float = float(number) if number else 999999
            except ValueError:
                num_float = 999999
            
            return (name, num_float, channel_id)
        
        def is_event_channel(channel_id: str) -> bool:
            """Check if channel is a generic placeholder (not a real program)"""
            channel = channel_map.get(channel_id, {})
            name = channel.get('GuideName', '').strip()
            
            # Pattern 1: "Event XX" anywhere in name
            if re.search(r'\bEvent\s+\d+', name, re.IGNORECASE):
                return True
            
            # Pattern 2: Placeholder patterns (no program name)
            # Matches: "Paramount+ 50 :", ":Paramount+ 97", "DAZN UK - 50", etc.
            # These are just provider + number with optional leading colon or trailing colon
            placeholder_patterns = [
                r'^:?\s*[\w\s]+(Plus|\+)[\s\-:]+\d+[\s:]*$',  # :Paramount+ 50 or Paramount+ 50 :
                r'^[\w\s]+[\s\-]+\d+[\s:]*$',  # Provider Name - 50 :
            ]
            for pattern in placeholder_patterns:
                if re.search(pattern, name, re.IGNORECASE):
                    # But make sure it doesn't have a real program name (contains @ or long text before :)
                    # Real programs have format: "Program Name @ Date :Paramount+ XX"
                    if '@' in name or re.search(r'^.{30,}:', name):
                        return False  # Has program info, not a placeholder
                    return True
            
            return False
        
        def extract_event_number(channel_id: str) -> int:
            """Extract the event number from channel name for proper sorting"""
            channel = channel_map.get(channel_id, {})
            name = channel.get('GuideName', '')
            match = re.search(r'\bEvent\s+(\d+)', name, re.IGNORECASE)
            if match:
                return int(match.group(1))
            # Also try to extract from "Provider+ 50" format
            match = re.search(r'(Plus|\+)[\s\-:]+(\d+)', name, re.IGNORECASE)
            if match:
                return int(match.group(2))
            return 999999
        
        if sort_order == 'name_asc':
            # Sort alphabetically A-Z
            return sorted(channel_ids, key=lambda cid: channel_map.get(cid, {}).get('GuideName', '').lower())
        
        elif sort_order == 'name_desc':
            # Sort alphabetically Z-A
            return sorted(channel_ids, key=lambda cid: channel_map.get(cid, {}).get('GuideName', '').lower(), reverse=True)
        
        elif sort_order == 'number_asc':
            # Sort by channel number ascending
            def num_key(cid):
                num = channel_map.get(cid, {}).get('GuideNumber', '')
                try:
                    return float(num) if num else 999999
                except ValueError:
                    return 999999
            return sorted(channel_ids, key=num_key)
        
        elif sort_order == 'number_desc':
            # Sort by channel number descending
            def num_key(cid):
                num = channel_map.get(cid, {}).get('GuideNumber', '')
                try:
                    return float(num) if num else 999999
                except ValueError:
                    return 999999
            return sorted(channel_ids, key=num_key, reverse=True)
        
        elif sort_order == 'events_last':
            # Non-event channels first (sorted by name), then event channels (sorted by event number)
            non_events = [cid for cid in channel_ids if not is_event_channel(cid)]
            events = [cid for cid in channel_ids if is_event_channel(cid)]
            
            # Sort non-events alphabetically
            non_events.sort(key=lambda cid: channel_map.get(cid, {}).get('GuideName', '').lower())
            
            # Sort events by their event number
            events.sort(key=extract_event_number)
            
            return non_events + events
        
        elif sort_order.startswith('regex:'):
            # Custom regex-based sorting
            pattern = sort_order[6:]  # Remove 'regex:' prefix
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                
                # Separate channels that match the regex vs those that don't
                matching = []
                non_matching = []
                
                for cid in channel_ids:
                    name = channel_map.get(cid, {}).get('GuideName', '')
                    if regex.search(name):
                        matching.append(cid)
                    else:
                        non_matching.append(cid)
                
                # Sort each group alphabetically
                matching.sort(key=lambda cid: channel_map.get(cid, {}).get('GuideName', '').lower())
                non_matching.sort(key=lambda cid: channel_map.get(cid, {}).get('GuideName', '').lower())
                
                # Matching channels first, then non-matching
                return matching + non_matching
            except re.error as e:
                logger.error(f"Invalid regex pattern in sort order: {pattern}: {e}")
                return sorted(channel_ids)
        
        else:
            # Default: no special sorting
            return sorted(channel_ids)
    
    def sync_rule(self, rule_id: str) -> Dict[str, Any]:
        """Sync a specific rule by ID"""
        logger.info(f"Syncing specific rule: {rule_id}")
        
        # Find the rule
        rule = None
        for r in self.rule_manager.rules:
            if r.get('id') == rule_id:
                rule = r
                break
        
        if not rule:
            logger.error(f"Rule {rule_id} not found")
            return {'error': 'Rule not found'}
        
        if not rule.get('enabled'):
            logger.warning(f"Rule {rule_id} is disabled, skipping")
            return {'error': 'Rule is disabled'}

        # AutoSync: update patterns from Dispatcharr before syncing
        if rule.get('dispatcharr_autosync') and rule.get('_dispatcharr_group_id'):
            logger.info(f"AutoSync: fetching latest channels for rule '{rule.get('name')}' from Dispatcharr")
            autosync_result = _update_rule_patterns_from_dispatcharr(rule)
            if autosync_result['success']:
                logger.info(f"AutoSync: updated patterns to {autosync_result.get('patterns')}")
                # Reload rule with updated patterns
                rule = next((r for r in self.rule_manager.rules if r.get('id') == rule_id), rule)
            else:
                logger.warning(f"AutoSync update failed: {autosync_result['message']} — proceeding with existing patterns")

        # Refresh sources and/or EPG if requested
        refresh_sources = rule.get('refresh_sources_before_sync', False)
        refresh_epg = rule.get('refresh_epg_before_sync', False)
        
        if refresh_sources or refresh_epg:
            logger.info(f"Refresh requested for rule: {rule.get('name')} (sources: {refresh_sources}, EPG: {refresh_epg})")
            
            try:
                import threading
                
                def do_refresh():
                    # Refresh sources if requested
                    if refresh_sources:
                        # Determine which sources to refresh
                        sources_to_refresh = []
                        
                        if rule.get('include_sources'):
                            sources_to_refresh = rule.get('include_sources', [])
                            logger.info(f"Refreshing specific included sources: {sources_to_refresh}")
                        else:
                            # Get all sources
                            try:
                                devices_response = requests.get(f"{self.api.base_url}/devices", timeout=5)
                                if devices_response.status_code == 200:
                                    all_devices = devices_response.json()
                                    sources_to_refresh = [d.get('DeviceID') for d in all_devices if d.get('DeviceID')]
                                    
                                    if rule.get('exclude_sources'):
                                        excluded = set(rule.get('exclude_sources', []))
                                        sources_to_refresh = [s for s in sources_to_refresh if s not in excluded]
                                        logger.info(f"Refreshing all sources except: {list(excluded)}")
                                    else:
                                        logger.info(f"Refreshing all {len(sources_to_refresh)} sources")
                            except Exception as e:
                                logger.warning(f"Error getting devices list: {e}")
                        
                        # Refresh each source
                        for device_id in sources_to_refresh:
                            try:
                                rescan_url = f"{self.api.base_url}/dvr/sources/{device_id}/rescan"
                                rescan_response = requests.put(rescan_url, timeout=5)
                                if rescan_response.status_code == 200:
                                    logger.info(f"✓ Source {device_id} rescan triggered")
                                else:
                                    logger.warning(f"Source {device_id} rescan returned status {rescan_response.status_code}")
                            except Exception as e:
                                logger.warning(f"Error rescanning source {device_id}: {e}")
                    
                    # Refresh EPG if requested
                    if refresh_epg:
                        try:
                            epg_response = requests.put(f"{self.api.base_url}/dvr/guide/refresh", timeout=5)
                            if epg_response.status_code == 200:
                                logger.info("✓ EPG refresh triggered")
                            else:
                                logger.warning(f"EPG refresh returned status {epg_response.status_code}")
                        except Exception as e:
                            logger.warning(f"Error refreshing EPG: {e}")
                
                # Run refresh in background thread
                refresh_thread = threading.Thread(target=do_refresh, daemon=True)
                refresh_thread.start()
                
                # Brief pause to let refresh start
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error starting refresh: {e}")
        
        # Get all channels
        all_channels = self.api.get_channels()
        if not all_channels:
            logger.error("Failed to fetch channels from DVR")
            return {'error': 'Failed to fetch channels'}
        
        # Process this rule
        collection_slug = rule.get('collection_slug')
        if not collection_slug:
            logger.error(f"Rule {rule_id} has no collection_slug")
            return {'error': 'No collection assigned'}
        
        try:
            matching_channels = self.rule_manager.get_matching_channels(all_channels, rule)
            channel_ids = [ch.get('ID') for ch in matching_channels if ch.get('ID')]
            
            collection = self.api.get_collection(collection_slug)
            if not collection:
                return {'error': f'Collection {collection_slug} not found'}
            
            old_channels = set(collection.get('items', []))
            new_channels = set(channel_ids)
            
            # Check if multiple rules target this collection
            rules_for_collection = [r for r in self.rule_manager.rules 
                                   if r.get('collection_slug') == collection_slug 
                                   and r.get('enabled', False)]
            
            is_shared_collection = len(rules_for_collection) > 1
            
            if is_shared_collection:
                # ADDITIVE MODE: Merge with existing channels, don't remove
                logger.info(f"⚠️ Shared collection detected! {len(rules_for_collection)} rules target '{collection.get('name')}' - using additive mode")
                
                # Combine old and new channels (union)
                combined_channels = old_channels | new_channels
                
                # Apply sorting to combined set
                sort_order = rule.get('sort_order', 'none')
                if sort_order != 'none':
                    # Get channel details for all combined channels
                    all_channel_map = {ch.get('ID'): ch for ch in all_channels}
                    combined_channel_details = [all_channel_map.get(cid) for cid in combined_channels if all_channel_map.get(cid)]
                    channel_map = {ch.get('ID'): ch for ch in combined_channel_details}
                    sorted_ids = self._sort_channels(list(combined_channels), channel_map, sort_order)
                    collection['items'] = sorted_ids
                else:
                    collection['items'] = sorted(list(combined_channels))
                
                if self.api.update_collection(collection_slug, collection):
                    added = new_channels - old_channels
                    logger.info(f"✓ Rule sync complete (ADDITIVE): {len(combined_channels)} total channels (+{len(added)}, -0 [shared collection])")
                    return {
                        'success': True,
                        'collection': collection.get('name'),
                        'total': len(combined_channels),
                        'added': len(added),
                        'removed': 0,
                        'shared_collection': True,
                        'rules_count': len(rules_for_collection)
                    }
            else:
                # NORMAL MODE: Replace channels (add and remove)
                # Apply sorting
                sort_order = rule.get('sort_order', 'none')
                if sort_order != 'none':
                    channel_map = {ch.get('ID'): ch for ch in matching_channels}
                    sorted_ids = self._sort_channels(list(new_channels), channel_map, sort_order)
                    collection['items'] = sorted_ids
                else:
                    collection['items'] = sorted(list(new_channels))
                
                if self.api.update_collection(collection_slug, collection):
                    added = new_channels - old_channels
                    removed = old_channels - new_channels
                    logger.info(f"✓ Rule sync complete: {len(new_channels)} channels (+{len(added)}, -{len(removed)})")
                    return {
                        'success': True,
                        'collection': collection.get('name'),
                        'total': len(new_channels),
                        'added': len(added),
                        'removed': len(removed),
                        'shared_collection': False
                    }
                else:
                    return {'error': 'Failed to update collection'}
        except Exception as e:
            logger.error(f"Error syncing rule {rule_id}: {e}")
            return {'error': str(e)}
    
    def sync_all(self) -> Dict[str, Any]:
        """Sync all collections based on rules"""
        logger.info("Starting sync of all collections")
        results = {
            'timestamp': datetime.now().isoformat(),
            'collections': {},
            'errors': [],
            'skipped': []
        }
        
        try:
            # Get all channels
            logger.info("Fetching all channels from DVR...")
            all_channels = self.api.get_channels()
            if not all_channels:
                error_msg = "Failed to fetch channels from DVR - check DVR_URL and connectivity"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            logger.info(f"Found {len(all_channels)} channels from DVR")
            
            # Get all rules
            active_rules = [r for r in self.rule_manager.rules if r.get('enabled', True)]
            logger.info(f"Processing {len(active_rules)} active rule(s) out of {len(self.rule_manager.rules)} total")
            
            if len(active_rules) == 0:
                error_msg = "No enabled rules found - create and enable at least one rule"
                logger.warning(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Process each rule
            for rule in active_rules:
                # Check if rule should run based on schedule
                if not is_rule_scheduled_now(rule):
                    rule_name = rule.get('name', 'Unknown')
                    logger.info(f"Skipping rule '{rule_name}' - outside scheduled time window")
                    results['skipped'].append(rule_name)
                    continue
                
                collection_slug = rule.get('collection_slug')
                if not collection_slug:
                    logger.warning(f"Rule '{rule.get('name')}' has no collection_slug, skipping")
                    results['errors'].append(f"Rule '{rule.get('name')}' has no collection assigned")
                    continue
                
                try:
                    logger.info(f"Processing rule: {rule.get('name')} for collection {collection_slug}")
                    
                    # Get matching channels
                    matching_channels = self.rule_manager.get_matching_channels(all_channels, rule)
                    # Use channel IDs instead of GuideNumbers
                    channel_ids = [ch.get('ID') for ch in matching_channels if ch.get('ID')]
                    
                    logger.info(f"Rule '{rule.get('name')}' matched {len(channel_ids)} channels")
                    
                    # Get current collection
                    collection = self.api.get_collection(collection_slug)
                    if not collection:
                        error_msg = f"Collection '{collection_slug}' not found in Channels DVR"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        continue
                    
                    # Update channel list using 'items' field (not 'Channels')
                    old_channels = set(collection.get('items', []))
                    new_channels = set(channel_ids)
                    
                    # Apply sorting based on rule settings
                    sort_order = rule.get('sort_order', 'none')
                    if sort_order != 'none':
                        # Create a map of channel IDs to channel data
                        channel_map = {ch.get('ID'): ch for ch in matching_channels}
                        sorted_ids = self._sort_channels(list(new_channels), channel_map, sort_order)
                        collection['items'] = sorted_ids
                    else:
                        collection['items'] = sorted(list(new_channels))
                    
                    # Update collection
                    if self.api.update_collection(collection_slug, collection):
                        added = new_channels - old_channels
                        removed = old_channels - new_channels
                        
                        results['collections'][collection_slug] = {
                            'name': collection.get('name', 'Unknown'),
                            'total': len(new_channels),
                            'added': len(added),
                            'removed': len(removed),
                            'channels': sorted(list(new_channels))
                        }
                        logger.info(f"✓ Updated collection '{collection.get('name')}': {len(new_channels)} channels (+{len(added)}, -{len(removed)})")
                    else:
                        error_msg = f"Failed to update collection '{collection_slug}'"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                
                except Exception as e:
                    error_msg = f"Error syncing collection {collection_slug}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            self.last_sync = datetime.now()
            self.last_sync_results = results
            
            logger.info(f"Sync completed: {len(results['collections'])} collections updated, {len(results['errors'])} errors")
            
        except Exception as e:
            error_msg = f"Sync error: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results


# Global instances
api = ChannelsAPI(DVR_URL)
rule_manager = RuleManager(CONFIG_FILE)
sync_manager = SyncManager(api, rule_manager)


# Routes
@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get system status"""
    return jsonify({
        'dvr_url': DVR_URL,
        'last_sync': sync_manager.last_sync.isoformat() if sync_manager.last_sync else None,
        'sync_interval': get_sync_interval(),
        'rules_count': len(rule_manager.rules),
        'version': '1.0.1'
    })


@app.route('/api/settings', methods=['GET'])
def get_settings_route():
    """Get application settings"""
    settings = load_app_settings()
    return jsonify({
        'sync_interval_minutes': settings.get('sync_interval_minutes', SYNC_INTERVAL)
    })


@app.route('/api/settings', methods=['POST'])
def save_settings_route():
    """Save application settings and rebuild scheduler"""
    try:
        data = request.json or {}
        settings = load_app_settings()

        if 'sync_interval_minutes' in data:
            interval = int(data['sync_interval_minutes'])
            if interval < 1 or interval > 10080:  # max 1 week
                return jsonify({'error': 'Sync interval must be between 1 and 10080 minutes'}), 400
            settings['sync_interval_minutes'] = interval

        if save_app_settings(settings):
            # Rebuild scheduler so new interval takes effect immediately
            setup_rule_schedulers()
            logger.info(f"Settings saved: sync_interval={settings.get('sync_interval_minutes')} min")
            return jsonify({'success': True, 'settings': settings})
        else:
            return jsonify({'error': 'Failed to save settings'}), 500

    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/static')
def debug_static():
    """Debug static folder configuration"""
    import os
    return jsonify({
        'static_folder': app.static_folder,
        'static_url_path': app.static_url_path,
        'static_exists': os.path.exists(app.static_folder) if app.static_folder else False,
        'static_contents': os.listdir(app.static_folder) if app.static_folder and os.path.exists(app.static_folder) else []
    })


@app.route('/api/rules', methods=['GET'])
def get_rules():
    """Get all rules"""
    return jsonify(rule_manager.rules)


@app.route('/api/rules', methods=['POST'])
def create_rule():
    """Create a new rule"""
    rule = request.json
    if rule_manager.add_rule(rule):
        setup_rule_schedulers()  # Refresh schedulers
        return jsonify({'success': True, 'rule': rule})
    return jsonify({'success': False, 'error': 'Failed to save rule'}), 500


@app.route('/api/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """Update a rule"""
    rule = request.json
    if rule_manager.update_rule(rule_id, rule):
        setup_rule_schedulers()  # Refresh schedulers
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Rule not found'}), 404


@app.route('/api/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """Delete a rule"""
    if rule_manager.delete_rule(rule_id):
        setup_rule_schedulers()  # Refresh schedulers
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Rule not found'}), 404


@app.route('/api/channels')
def get_channels():
    """Get all available channels"""
    channels = api.get_channels()
    return jsonify(channels)


@app.route('/api/collections/get-or-create', methods=['POST'])
def get_or_create_collection():
    """Get existing collection by name or create new one"""
    try:
        data = request.json
        collection_name = data.get('name', '').strip()
        
        if not collection_name:
            return jsonify({'error': 'Collection name is required'}), 400
        
        # Get all existing collections directly from API
        collections = api.get_collections()
        
        # Check if collection with this name already exists (case-insensitive)
        # Channels DVR returns 'name' field; guard against 'title' for compatibility
        for collection in collections:
            existing_name = (collection.get('name') or collection.get('title') or '').strip()
            if existing_name.lower() == collection_name.lower():
                logger.info(f"Collection '{collection_name}' already exists (slug: {collection.get('slug')})")
                return jsonify({
                    'slug': collection.get('slug'),
                    'name': existing_name,
                    'created': False,
                    'message': f"Using existing collection '{collection_name}'"
                })
        
        # Collection doesn't exist, create it using correct Channels DVR endpoint
        create_url = f"{DVR_URL}/dvr/collections/channels/new"
        
        logger.info(f"Creating new collection '{collection_name}' at {create_url}")
        
        response = requests.post(
            create_url,
            json={'name': collection_name},
            timeout=30
        )
        response.raise_for_status()
        
        new_collection = response.json()
        collection_slug = new_collection.get('slug')
        
        logger.info(f"Created new collection '{collection_name}' (slug: {collection_slug})")
        
        return jsonify({
            'slug': collection_slug,
            'name': collection_name,
            'created': True,
            'message': f"Created new collection '{collection_name}'"
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating collection in Channels DVR: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}, body: {e.response.text}")
        return jsonify({'error': f'Failed to create collection: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error in get-or-create collection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/collections')
def get_collections():
    """Get all collections"""
    collections = api.get_collections()
    return jsonify(collections)


@app.route('/api/collections/<collection_slug>')
def get_collection_detail(collection_slug):
    """Get detailed information about a specific collection"""
    collection = api.get_collection(collection_slug)
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404
    
    # Get all channels to provide names for the channel IDs
    all_channels = api.get_channels()
    channel_map = {ch.get('ID'): ch for ch in all_channels}
    
    # Enrich collection with channel details
    collection_channels = []
    for channel_id in collection.get('items', []):
        channel_info = channel_map.get(channel_id, {})
        collection_channels.append({
            'id': channel_id,
            'number': channel_info.get('GuideNumber', ''),
            'name': channel_info.get('GuideName', channel_id),
            'callsign': channel_info.get('Callsign', ''),
            'affiliate': channel_info.get('Affiliate', '')
        })
    
    return jsonify({
        'slug': collection.get('slug'),
        'name': collection.get('name'),
        'channels': collection_channels,
        'total': len(collection_channels)
    })


@app.route('/api/sources')
def get_sources():
    """Get all available sources/devices"""
    try:
        response = requests.get(f"{DVR_URL}/devices")
        devices = response.json()
        sources = [
            {
                'device_id': device.get('DeviceID'),
                'name': device.get('FriendlyName'),
                'provider': device.get('Provider', 'Unknown')
            }
            for device in devices
        ]
        return jsonify(sources)
    except Exception as e:
        logger.error(f"Error fetching sources: {e}")
        return jsonify([]), 500


@app.route('/api/preview', methods=['POST'])
def preview_rule():
    """Preview channels matching a rule"""
    rule = request.json
    channels = api.get_channels()
    matching = rule_manager.get_matching_channels(channels, rule)
    
    # Apply sorting if specified
    sort_order = rule.get('sort_order', 'none')
    if sort_order and sort_order != 'none':
        # Create channel map for sorting
        channel_map = {ch.get('ID'): ch for ch in matching}
        channel_ids = [ch.get('ID') for ch in matching]
        sorted_ids = sync_manager._sort_channels(channel_ids, channel_map, sort_order)
        
        # Reorder matching channels based on sorted IDs
        id_to_channel = {ch.get('ID'): ch for ch in matching}
        matching = [id_to_channel[cid] for cid in sorted_ids if cid in id_to_channel]
    
    return jsonify({
        'total': len(matching),
        'sort_order': sort_order,
        'channels': [
            {
                'id': ch.get('ID'),
                'number': ch.get('GuideNumber'),
                'name': ch.get('GuideName'),
                'callsign': ch.get('Callsign', ''),
                'affiliate': ch.get('Affiliate', ''),
                'device': ch.get('_device_name', 'Unknown')  # Device info
            }
            for ch in matching
        ]
    })


@app.route('/api/sync', methods=['POST'])
def trigger_sync():
    """Manually trigger a sync"""
    results = sync_manager.sync_all()
    return jsonify(results)


@app.route('/api/sync/status')
def sync_status():
    """Get last sync results"""
    return jsonify({
        'last_sync': sync_manager.last_sync.isoformat() if sync_manager.last_sync else None,
        'results': sync_manager.last_sync_results
    })


@app.route('/api/test-connection')
def test_connection():
    """Test connection to Channels DVR"""
    results = {
        'dvr_url': DVR_URL,
        'tests': {}
    }
    
    try:
        # Test 1: Basic connectivity - try multiple endpoints
        response = requests.get(f"{DVR_URL}/devices", timeout=5)
        results['tests']['devices'] = {
            'status': response.status_code,
            'success': response.status_code == 200,
            'data': response.json() if response.status_code == 200 else None
        }
        
        # If /devices fails with 404, try alternative
        if response.status_code == 404:
            # Try just hitting the root
            response = requests.get(f"{DVR_URL}/", timeout=5)
            results['tests']['dvr_root'] = {
                'status': response.status_code,
                'success': response.status_code == 200
            }
    except Exception as e:
        results['tests']['devices'] = {
            'status': 0,
            'success': False,
            'error': str(e)
        }
    
    try:
        # Test 2: Collections endpoint (using correct endpoint)
        response = requests.get(f"{DVR_URL}/dvr/collections/channels", timeout=5)
        results['tests']['collections'] = {
            'status': response.status_code,
            'success': response.status_code == 200,
            'data': response.json() if response.status_code == 200 else None
        }
        
        # If this fails, note that collections are still loading via api.get_collections()
        if response.status_code != 200:
            # Try via our API wrapper
            collections = api.get_collections()
            results['tests']['collections_via_api'] = {
                'success': len(collections) > 0,
                'count': len(collections),
                'note': 'Collections fetched via API wrapper despite direct endpoint failure'
            }
    except Exception as e:
        results['tests']['collections'] = {
            'status': 0,
            'success': False,
            'error': str(e)
        }
    
    try:
        # Test 3: Channels
        channels = api.get_channels()
        results['tests']['channels'] = {
            'success': len(channels) > 0,
            'count': len(channels)
        }
    except Exception as e:
        results['tests']['channels'] = {
            'success': False,
            'error': str(e)
        }
    
    return jsonify(results)


@app.route('/api/export', methods=['GET'])
def export_rules():
    """Export all rules or specific groups as JSON"""
    try:
        group_filter = request.args.get('group')
        rules_to_export = rule_manager.rules
        
        if group_filter and group_filter != 'all':
            rules_to_export = [r for r in rules_to_export if r.get('group') == group_filter]
        
        export_data = {
            'version': '1.2.0',
            'exported_at': datetime.now().isoformat(),
            'rules_count': len(rules_to_export),
            'rules': rules_to_export
        }
        
        # Create in-memory file
        json_data = json.dumps(export_data, indent=2)
        buffer = BytesIO(json_data.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"channels-rules-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        if group_filter and group_filter != 'all':
            filename = f"channels-rules-{group_filter}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/import', methods=['POST'])
def import_rules():
    """Import rules from JSON file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read and parse JSON
        content = file.read().decode('utf-8')
        import_data = json.loads(content)
        
        if 'rules' not in import_data:
            return jsonify({'error': 'Invalid export file format'}), 400
        
        imported_rules = import_data['rules']
        mode = request.form.get('mode', 'merge')  # merge or replace
        
        if mode == 'replace':
            rule_manager.rules = imported_rules
        else:  # merge
            # Generate new IDs for imported rules to avoid conflicts
            import uuid
            for rule in imported_rules:
                rule['id'] = str(uuid.uuid4())
            rule_manager.rules.extend(imported_rules)
        
        rule_manager.save_rules()
        setup_rule_schedulers()
        
        return jsonify({
            'success': True,
            'imported_count': len(imported_rules),
            'mode': mode,
            'total_rules': len(rule_manager.rules)
        })
    except Exception as e:
        logger.error(f"Import error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/groups', methods=['GET'])
def get_groups():
    """Get all unique rule groups"""
    try:
        groups = set()
        for rule in rule_manager.rules:
            group = rule.get('group', 'ungrouped')
            if group:
                groups.add(group)
        
        return jsonify(sorted(list(groups)))
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get all rule templates"""
    try:
        templates_file = '/config/templates.json'
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                templates = json.load(f)
            return jsonify(templates)
        return jsonify([])
    except Exception as e:
        logger.error(f"Error loading templates: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/templates', methods=['POST'])
def save_template():
    """Save a new template"""
    try:
        template_data = request.json
        
        # Load existing templates
        templates_file = '/config/templates.json'
        templates = []
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                templates = json.load(f)
        
        # Add new template
        template_data['id'] = str(uuid.uuid4())
        template_data['created_at'] = datetime.now().isoformat()
        templates.append(template_data)
        
        # Save
        with open(templates_file, 'w') as f:
            json.dump(templates, f, indent=2)
        
        return jsonify(template_data)
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template"""
    try:
        templates_file = '/config/templates.json'
        if not os.path.exists(templates_file):
            return jsonify({'error': 'No templates found'}), 404
        
        with open(templates_file, 'r') as f:
            templates = json.load(f)
        
        templates = [t for t in templates if t['id'] != template_id]
        
        with open(templates_file, 'w') as f:
            json.dump(templates, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Dispatcharr Integration Routes
# ============================================================================

def load_dispatcharr_config() -> Dict[str, Any]:
    """Load Dispatcharr configuration from file"""
    try:
        if os.path.exists(DISPATCHARR_CONFIG_FILE):
            with open(DISPATCHARR_CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading Dispatcharr config: {e}")
    
    # Return default config
    return {
        'enabled': False,
        'url': '',
        'username': '',
        'password': ''
    }


def save_dispatcharr_config(config: Dict[str, Any]) -> bool:
    """Save Dispatcharr configuration to file"""
    try:
        with open(DISPATCHARR_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving Dispatcharr config: {e}")
        return False


def get_dispatcharr_client() -> Optional[DispatcharrClient]:
    """Get configured Dispatcharr client or None if not configured"""
    config = load_dispatcharr_config()
    
    if not config.get('enabled', False):
        return None
    
    if not all([config.get('url'), config.get('username'), config.get('password')]):
        return None
    
    client = DispatcharrClient(
        base_url=config['url'],
        username=config['username'],
        password=config['password']
    )
    
    # Restore cached tokens if available
    if config.get('access_token') and config.get('refresh_token'):
        client.access_token = config['access_token']
        client.refresh_token = config['refresh_token']
        if config.get('token_expires_at'):
            try:
                client.token_expires_at = datetime.fromisoformat(config['token_expires_at'])
                logger.info("Restored cached Dispatcharr tokens")
            except:
                pass
    
    return client


@app.route('/api/dispatcharr/config', methods=['GET'])
def get_dispatcharr_config():
    """Get Dispatcharr configuration (without password)"""
    try:
        config = load_dispatcharr_config()
        # Don't send password to frontend
        safe_config = {
            'enabled': config.get('enabled', False),
            'url': config.get('url', ''),
            'username': config.get('username', ''),
            'has_password': bool(config.get('password', ''))
        }
        return jsonify(safe_config)
    except Exception as e:
        logger.error(f"Error getting Dispatcharr config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dispatcharr/config', methods=['POST'])
def save_dispatcharr_config_route():
    """Save Dispatcharr configuration"""
    try:
        data = request.json
        
        # Load existing config
        config = load_dispatcharr_config()
        
        # Update config
        config['enabled'] = data.get('enabled', False)
        config['url'] = data.get('url', '').rstrip('/')
        config['username'] = data.get('username', '')
        
        # Only update password if provided
        if data.get('password'):
            config['password'] = data.get('password')
        
        # Save config
        if save_dispatcharr_config(config):
            return jsonify({'success': True, 'message': 'Configuration saved'})
        else:
            return jsonify({'error': 'Failed to save configuration'}), 500
            
    except Exception as e:
        logger.error(f"Error saving Dispatcharr config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dispatcharr/test', methods=['POST'])
def test_dispatcharr_connection():
    """Test Dispatcharr connection"""
    try:
        data = request.json
        
        logger.info(f"Received test request with data keys: {list(data.keys())}")
        logger.info(f"URL: {data.get('url', 'MISSING')}")
        logger.info(f"Username: '{data.get('username', 'MISSING')}' (type: {type(data.get('username'))})")
        
        password = data.get('password', '')
        
        # If placeholder sent, use stored password
        if password == '__USE_STORED__':
            config = load_dispatcharr_config()
            password = config.get('password', '')
            logger.info("Using stored password for test")
        else:
            logger.info(f"Password length: {len(password)}")
        
        # Create temporary client with provided credentials
        client = DispatcharrClient(
            base_url=data.get('url', '').rstrip('/'),
            username=data.get('username', ''),
            password=password
        )
        
        # Test connection
        result = client.test_connection()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error testing Dispatcharr connection: {e}")
        return jsonify({
            'success': False,
            'message': f'Connection test failed: {str(e)}'
        }), 500


@app.route('/api/dispatcharr/groups', methods=['GET'])
def get_dispatcharr_groups():
    """Get all enabled Dispatcharr channel groups"""
    try:
        client = get_dispatcharr_client()

        if not client:
            return jsonify({
                'error': 'Dispatcharr not configured or not enabled'
            }), 400

        # Get enabled groups
        groups = client.get_enabled_groups()

        # Build set of group IDs that already have an AutoSync rule
        autosync_group_ids = {
            r['_dispatcharr_group_id']
            for r in rule_manager.rules
            if r.get('dispatcharr_autosync') and r.get('_dispatcharr_group_id')
        }

        # Annotate each group with has_autosync_rule flag
        for group in groups:
            group['has_autosync_rule'] = group['id'] in autosync_group_ids

        return jsonify(groups)

    except Exception as e:
        logger.error(f"Error getting Dispatcharr groups: {e}")
        return jsonify({'error': str(e)}), 500


def generate_channel_pattern(channel_numbers):
    """
    Generate smart pattern from channel numbers, handling gaps
    Example: [101, 102, 103, 104, 107, 108] -> "101-104,107-108"
    """
    if not channel_numbers:
        return ''
    
    # Sort numbers and ensure they're integers
    sorted_nums = sorted([int(n) for n in channel_numbers])
    
    # Group consecutive numbers into ranges
    ranges = []
    range_start = sorted_nums[0]
    range_end = sorted_nums[0]
    
    for i in range(1, len(sorted_nums) + 1):
        if i < len(sorted_nums) and sorted_nums[i] == range_end + 1:
            # Consecutive number, extend range
            range_end = sorted_nums[i]
        else:
            # Gap or end of array, close current range
            if range_start == range_end:
                # Single number
                ranges.append(str(range_start))
            else:
                # Range
                ranges.append(f"{range_start}-{range_end}")
            
            # Start new range
            if i < len(sorted_nums):
                range_start = sorted_nums[i]
                range_end = sorted_nums[i]
    
    return ','.join(ranges)


@app.route('/api/dispatcharr/groups/<int:group_id>/channels', methods=['GET'])
def get_dispatcharr_group_channels(group_id):
    """Get actual channel assignments for a Dispatcharr group"""
    try:
        client = get_dispatcharr_client()
        
        if not client:
            return jsonify({'error': 'Dispatcharr not configured'}), 400
        
        if not client._ensure_authenticated():
            return jsonify({'error': 'Authentication failed'}), 401
        
        # Get all enabled groups to find M3U account name
        enabled_groups = client.get_enabled_groups()
        target_group = None
        for g in enabled_groups:
            if g['id'] == group_id:
                target_group = g
                break
        
        if not target_group:
            return jsonify({'error': 'Group not found or not enabled'}), 404
        
        group_name = target_group['name']
        m3u_account_name = target_group.get('m3u_account_name', '')
        is_local_group = target_group.get('m3u_account_count', 0) == 0
        
        logger.info(f"Looking up channels for group: {group_name}, Type: {'Local' if is_local_group else 'Provider'}")
        
        # Get streams for this group
        streams_url = f"{client.base_url}/api/channels/streams/"
        
        if is_local_group:
            # Local groups: search by channel_group parameter
            params = {
                'channel_group': group_id
            }
            logger.info(f"Fetching streams for local group by channel_group={group_id}")
        else:
            # Provider groups: search by group name and M3U account
            params = {
                'channel_group_name': group_name,
                'm3u_account_name': m3u_account_name
            }
            logger.info(f"Fetching streams for provider group: {group_name}, M3U account: {m3u_account_name}")
        
        response = requests.get(streams_url, headers=client._get_headers(), params=params, timeout=30)
        response.raise_for_status()
        
        streams_data = response.json()
        stream_ids = [s['id'] for s in streams_data.get('results', [])]
        
        logger.info(f"Found {len(stream_ids)} streams in group")
        
        # Get channels directly by channel_group_id
        channels_url = f"{client.base_url}/api/channels/channels/"
        channels_params = {'channel_group_id': group_id}
        
        response = requests.get(channels_url, headers=client._get_headers(), params=channels_params, timeout=30)
        response.raise_for_status()
        
        channels_data = response.json()
        
        # Check if it's a list or paginated response
        if isinstance(channels_data, dict):
            # Paginated response
            all_channels = channels_data.get('results', [])
            logger.info(f"Retrieved {len(all_channels)} channels from API")
        elif isinstance(channels_data, list):
            # Direct list response
            all_channels = channels_data
            logger.info(f"Retrieved {len(all_channels)} channels from API")
        else:
            logger.error(f"Unexpected response type: {type(channels_data)}")
            all_channels = []
        
        # Filter to only channels that EXACTLY match this group_id
        # (the API parameter might return more than we want)
        matched_channels = []
        for channel in all_channels:
            if not isinstance(channel, dict):
                continue
            
            # Check if this channel's channel_group_id matches our group_id
            if channel.get('channel_group_id') != group_id:
                continue
                
            channel_streams = channel.get('streams', [])
            if not isinstance(channel_streams, list):
                continue
            
            matched_channels.append({
                'channel_number': channel.get('channel_number'),
                'name': channel.get('name', 'Unknown'),
                'streams_count': len(channel_streams)
            })
        
        logger.info(f"Filtered to {len(matched_channels)} channels that exactly match group_id={group_id}")
        
        # Sort by channel number
        matched_channels.sort(key=lambda x: x['channel_number'] if x['channel_number'] is not None else 999999)
        
        # Generate smart pattern
        channel_nums = [c['channel_number'] for c in matched_channels if c['channel_number'] is not None]
        smart_pattern = generate_channel_pattern(channel_nums)
        
        logger.info(f"Found {len(matched_channels)} channels with streams from group {group_name}")
        logger.info(f"Generated pattern: {smart_pattern}")
        
        return jsonify({
            'group_name': group_name,
            'total_streams': len(stream_ids),
            'assigned_channels_count': len(matched_channels),
            'channels': matched_channels,
            'smart_pattern': smart_pattern
        })
        
    except Exception as e:
        logger.error(f"Error getting group channels: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/dispatcharr/groups/<int:group_id>/create-rule', methods=['POST'])
def create_rule_from_dispatcharr_group(group_id):
    """Create a rule from a Dispatcharr group"""
    try:
        client = get_dispatcharr_client()
        
        if not client:
            return jsonify({'error': 'Dispatcharr not configured'}), 400
        
        # Get enabled groups to find this one
        enabled_groups = client.get_enabled_groups()
        target_group = None
        for g in enabled_groups:
            if g['id'] == group_id:
                target_group = g
                break
        
        if not target_group:
            return jsonify({'error': 'Group not found or not enabled'}), 404
        
        group_name = target_group['name']
        
        # Try to get actual channel assignments
        try:
            # Reuse the channel lookup logic
            channels_response = get_dispatcharr_group_channels(group_id)
            channels_data = channels_response.json
            
            if channels_data and 'smart_pattern' in channels_data and channels_data['smart_pattern']:
                # Use the smart pattern from actual channel assignments
                pattern = channels_data['smart_pattern']
                logger.info(f"Using smart pattern from channel assignments: {pattern}")
            else:
                # Fallback to name-based pattern
                pattern = group_name
                logger.info(f"No channel assignments found, using name pattern: {pattern}")
        except Exception as e:
            logger.warning(f"Could not get channel assignments: {e}, falling back to name pattern")
            pattern = group_name
        
        # Determine match type based on pattern
        is_number_pattern = any(char.isdigit() for char in pattern)
        
        # Create rule structure
        rule_data = {
            'name': group_name,
            'group': 'Dispatcharr',
            'patterns': [pattern],
            'pattern_metadata': {
                pattern: {
                    'mode': 'simple',
                    'type': 'range' if is_number_pattern else 'contains',
                    'value': pattern,
                    'caseSensitive': False
                }
            },
            'match_types': ['number'] if is_number_pattern else ['name'],
            'sort_order': 'none',
            'enabled': target_group.get('auto_channel_sync', False),
            'sync_interval_minutes': None,
            'include_sources': [],
            'exclude_sources': [],
            'refresh_sources_before_sync': False,
            'refresh_epg_before_sync': False,
            'schedule_enabled': False,
            'schedule_days': None,
            'schedule_start_time': None,
            'schedule_end_time': None,
            '_dispatcharr_group_id': group_id,
            '_dispatcharr_group_name': target_group['name']
        }
        
        return jsonify({
            'success': True,
            'rule_template': rule_data,
            'message': f'Rule template created for {target_group["name"]}'
        })
        
    except Exception as e:
        logger.error(f"Error creating rule from Dispatcharr group: {e}")
        return jsonify({'error': str(e)}), 500


def _update_rule_patterns_from_dispatcharr(rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch the latest channel numbers for a Dispatcharr-linked rule and update
    its patterns in rule_manager.

    Returns a dict with 'success', 'message', and optionally 'patterns'.
    """
    group_id = rule.get('_dispatcharr_group_id')
    if not group_id:
        return {'success': False, 'message': 'Rule has no _dispatcharr_group_id'}

    client = get_dispatcharr_client()
    if not client:
        return {'success': False, 'message': 'Dispatcharr not configured or not enabled'}

    if not client._ensure_authenticated():
        return {'success': False, 'message': 'Dispatcharr authentication failed'}

    try:
        enabled_groups = client.get_enabled_groups()
        target_group = next((g for g in enabled_groups if g['id'] == group_id), None)
        if not target_group:
            return {'success': False, 'message': f'Dispatcharr group {group_id} not found or not enabled'}

        group_name = target_group['name']
        is_local_group = target_group.get('m3u_account_count', 0) == 0
        m3u_account_name = target_group.get('m3u_account_name', '')

        # Fetch channels by group
        channels_url = f"{client.base_url}/api/channels/channels/"
        channels_response = requests.get(channels_url, headers=client._get_headers(),
                                         params={'channel_group_id': group_id}, timeout=30)
        channels_response.raise_for_status()

        channels_data = channels_response.json()
        all_channels = channels_data.get('results', []) if isinstance(channels_data, dict) else channels_data

        channel_nums = []
        for ch in all_channels:
            if not isinstance(ch, dict):
                continue
            if ch.get('channel_group_id') != group_id:
                continue
            num = ch.get('channel_number')
            if num is not None:
                channel_nums.append(num)

        if not channel_nums:
            return {'success': False, 'message': f'No channels found in Dispatcharr group "{group_name}"'}

        smart_pattern = generate_channel_pattern(channel_nums)
        logger.info(f"AutoSync: group '{group_name}' -> pattern '{smart_pattern}'")

        # Update the rule patterns
        rule_id = rule.get('id')
        updated_rule = {**rule, 'patterns': [smart_pattern], 'match_types': ['number']}
        if rule_manager.update_rule(rule_id, updated_rule):
            return {'success': True, 'message': f'Updated patterns to {smart_pattern}', 'patterns': [smart_pattern]}
        else:
            return {'success': False, 'message': 'Failed to save updated rule patterns'}

    except Exception as e:
        logger.error(f"AutoSync update failed for rule {rule.get('id')}: {e}")
        return {'success': False, 'message': str(e)}


@app.route('/api/rules/<rule_id>/update-from-dispatcharr', methods=['POST'])
def update_rule_from_dispatcharr(rule_id):
    """Fetch latest channel numbers from Dispatcharr and update rule patterns"""
    try:
        rule = next((r for r in rule_manager.rules if r.get('id') == rule_id), None)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404

        if not rule.get('dispatcharr_autosync'):
            return jsonify({'error': 'Rule does not have AutoSync enabled'}), 400

        result = _update_rule_patterns_from_dispatcharr(rule)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['message']}), 400

    except Exception as e:
        logger.error(f"Error in update-from-dispatcharr for rule {rule_id}: {e}")
        return jsonify({'error': str(e)}), 500


def scheduled_sync():
    """Scheduled sync job"""
    with app.app_context():
        logger.info("Running scheduled sync")
        sync_manager.sync_all()


def setup_rule_schedulers():
    """Setup individual schedulers for rules with custom sync intervals"""
    scheduler.remove_all_jobs()

    # Use effective sync interval (settings file overrides env var)
    effective_interval = get_sync_interval()

    # Add main global sync job
    scheduler.add_job(
        func=scheduled_sync,
        trigger='interval',
        minutes=effective_interval,
        id='global_sync',
        name='Global sync',
        replace_existing=True
    )
    logger.info(f"Global sync scheduled every {effective_interval} minutes")
    
    # Add per-rule sync jobs for rules with custom intervals
    for rule in rule_manager.rules:
        if rule.get('enabled') and rule.get('sync_interval_minutes'):
            rule_id = rule.get('id')
            interval = rule.get('sync_interval_minutes')
            
            def make_rule_sync(rule_id):
                def rule_sync():
                    with app.app_context():
                        logger.info(f"Running custom sync for rule {rule_id}")
                        # Sync only this specific rule
                        sync_manager.sync_rule(rule_id)
                return rule_sync
            
            scheduler.add_job(
                func=make_rule_sync(rule_id),
                trigger='interval',
                minutes=interval,
                id=f'rule_sync_{rule_id}',
                name=f'Sync rule {rule.get("name")}',
                replace_existing=True
            )
            logger.info(f"Scheduled rule '{rule.get('name')}' to sync every {interval} minutes")


if __name__ == '__main__':
    # Start scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()
    
    # Setup all sync jobs (global + per-rule)
    setup_rule_schedulers()
    
    # Run initial sync
    logger.info("Running initial sync")
    sync_manager.sync_all()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
