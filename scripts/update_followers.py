import os
import json
import requests
from datetime import datetime, timezone
from dateutil import parser

# Configuration
CHANNEL_NAME = os.environ.get('TWITCH_CHANNEL_NAME', 'marlon')
MARATHON_START = "2025-10-27T00:00:00-07:00"  # PST timezone

# Data file paths
DATA_DIR = 'data'
STATS_FILE = f'{DATA_DIR}/stats.json'

def get_twitch_follower_count(channel_name):
    """Get follower count from public API"""
    try:
        url = f'https://decapi.me/twitch/followcount/{channel_name}'
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            count = response.text.strip()
            return int(count) if count.isdigit() else 0
        return 0
    except Exception as e:
        print(f"Error getting follower count: {e}")
        return 0

def get_twitch_live_status(channel_name):
    """Check if channel is live"""
    try:
        url = f'https://decapi.me/twitch/uptime/{channel_name}'
        response = requests.get(url, timeout=10)
        text = response.text.strip().lower()
        return 'offline' not in text
    except Exception as e:
        print(f"Error checking live status: {e}")
        return False

def calculate_marathon_day():
    """Calculate which day of the marathon we're on (PST timezone)"""
    start = parser.parse(MARATHON_START)
    now = datetime.now(timezone.utc)
    delta = now - start
    return max(1, min(28, delta.days + 1))

def load_existing_data(filepath):
    """Load existing data file"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def save_data(filepath, data):
    """Save data to file"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, indent=2, fp=f)

def main():
    print("=" * 60)
    print("UPDATING FOLLOWER COUNT")
    print("=" * 60)
    
    # Get current data
    follower_count = get_twitch_follower_count(CHANNEL_NAME)
    is_live = get_twitch_live_status(CHANNEL_NAME)
    current_day = calculate_marathon_day()
    
    print(f"\n✓ Followers: {follower_count:,}")
    print(f"✓ Stream: {'🔴 LIVE' if is_live else '⚫ OFFLINE'}")
    print(f"✓ Day: {current_day}/28")
    
    # Load existing stats
    stats = load_existing_data(STATS_FILE)
    
    if stats:
        # Calculate marathon followers
        if 'marathonStartFollowers' in stats.get('stats', {}):
            marathon_start_followers = stats['stats']['marathonStartFollowers']
            marathon_followers = follower_count - marathon_start_followers
        else:
            # First run - save baseline
            marathon_start_followers = follower_count
            marathon_followers = 0
        
        # Update stats
        stats['lastUpdated'] = datetime.now(timezone.utc).isoformat()
        stats['currentDay'] = current_day
        
        if 'stats' not in stats:
            stats['stats'] = {}
        
        stats['stats']['totalFollowers'] = follower_count
        stats['stats']['marathonFollowers'] = marathon_followers
        stats['stats']['marathonStartFollowers'] = marathon_start_followers
        
        save_data(STATS_FILE, stats)
        print(f"\n✓ Updated stats.json")
        print(f"  • Marathon Followers: {marathon_followers:,}")
    else:
        # Create initial stats file
        stats = {
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "marathonStart": MARATHON_START,
            "currentDay": current_day,
            "stats": {
                "totalSubs": 0,
                "marathonSubs": 0,
                "totalFollowers": follower_count,
                "marathonFollowers": 0,
                "marathonStartFollowers": follower_count,
                "totalChats": 0
            },
            "dailySubs": {},
            "topGifters": [],
            "topChatters": []
        }
        save_data(STATS_FILE, stats)
        print(f"\n✓ Created initial stats.json")
    
    print("=" * 60)
    print("✅ FOLLOWER UPDATE COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()
