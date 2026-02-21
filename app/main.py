#!/usr/bin/env python3
import os
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Set
from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configuration
DVR_URL = os.environ.get('DVR_URL', 'http://channelsdvr:8089')
CONFIG_FILE = '/config/rules.json'
SYNC_INTERVAL = int(os.environ.get('SYNC_INTERVAL_MINUTES', '60'))

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
        
        for pattern in patterns:
            try:
                # Check if pattern is a channel number range (e.g., "100-200")
                if '-' in pattern and pattern.replace('-', '').replace('.', '').isdigit():
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
            """Check if channel name contains 'Event' followed by a number/space"""
            channel = channel_map.get(channel_id, {})
            name = channel.get('GuideName', '').strip()
            # Match patterns like "Event 1", "Event 01", "DAZN UK - Event 50", etc.
            import re
            return bool(re.search(r'\bEvent\s+\d+', name, re.IGNORECASE))
        
        def extract_event_number(channel_id: str) -> int:
            """Extract the event number from channel name for proper sorting"""
            channel = channel_map.get(channel_id, {})
            name = channel.get('GuideName', '')
            import re
            match = re.search(r'\bEvent\s+(\d+)', name, re.IGNORECASE)
            if match:
                return int(match.group(1))
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
                import re
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
                    'removed': len(removed)
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
            'errors': []
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
        'sync_interval': SYNC_INTERVAL,
        'rules_count': len(rule_manager.rules)
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


def scheduled_sync():
    """Scheduled sync job"""
    with app.app_context():
        logger.info("Running scheduled sync")
        sync_manager.sync_all()


def setup_rule_schedulers():
    """Setup individual schedulers for rules with custom sync intervals"""
    scheduler.remove_all_jobs()
    
    # Add main global sync job
    scheduler.add_job(
        func=scheduled_sync,
        trigger='interval',
        minutes=SYNC_INTERVAL,
        id='global_sync',
        name='Global sync',
        replace_existing=True
    )
    
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
