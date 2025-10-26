import os
import json
import socket
import re
from datetime import datetime, timezone
from dateutil import parser

# Configuration
CHANNEL_NAME = os.environ.get('TWITCH_CHANNEL_NAME', 'marlon')
MARATHON_START = "2025-10-27T00:00:00-07:00"  # PST timezone

# Twitch IRC Configuration
IRC_SERVER = "irc.chat.twitch.tv"
IRC_PORT = 6667
BOT_NICKNAME = "justinfan12345"  # Anonymous viewer bot

# Data file paths
DATA_DIR = 'data'
STATS_FILE = f'{DATA_DIR}/stats.json'
DAILY_FILE = f'{DATA_DIR}/daily.json'

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

def connect_to_twitch(channel):
    """Connect to Twitch IRC chat"""
    print(f"Connecting to Twitch IRC for channel: {channel}")
    sock = socket.socket()
    sock.connect((IRC_SERVER, IRC_PORT))
    
    # Send authentication (anonymous)
    sock.send(f"PASS oauth:justinfan12345\n".encode('utf-8'))
    sock.send(f"NICK {BOT_NICKNAME}\n".encode('utf-8'))
    sock.send(f"JOIN #{channel}\n".encode('utf-8'))
    sock.send("CAP REQ :twitch.tv/tags\n".encode('utf-8'))
    
    print(f"✓ Connected to #{channel}")
    return sock

def parse_irc_message(message):
    """Parse IRC message and extract sub/bits information"""
    try:
        # Check for subscription events
        if "msg-id=sub" in message or "msg-id=resub" in message:
            username_match = re.search(r'display-name=([^;]+)', message)
            if username_match:
                username = username_match.group(1)
                return {"type": "sub", "username": username, "amount": 1}
        
        # Check for gift sub events
        if "msg-id=subgift" in message or "msg-id=submysterygift" in message:
            gifter_match = re.search(r'display-name=([^;]+)', message)
            recipient_match = re.search(r'msg-param-recipient-display-name=([^;]+)', message)
            count_match = re.search(r'msg-param-mass-gift-count=([0-9]+)', message)
            
            if gifter_match:
                gifter = gifter_match.group(1)
                count = int(count_match.group(1)) if count_match else 1
                return {"type": "gift", "username": gifter, "amount": count}
        
        # Check for bits/cheers
        bits_match = re.search(r'bits=([0-9]+)', message)
        if bits_match:
            username_match = re.search(r'display-name=([^;]+)', message)
            if username_match:
                username = username_match.group(1)
                bits = int(bits_match.group(1))
                return {"type": "bits", "username": username, "amount": bits}
        
    except Exception as e:
        print(f"Error parsing message: {e}")
    
    return None

def count_chat_message(username):
    """Increment chat message count for a user"""
    stats = load_existing_data(STATS_FILE)
    if not stats:
        return
    
    # Update total chats
    stats['stats']['totalChats'] = stats['stats'].get('totalChats', 0) + 1
    
    # Update top chatters
    chatters = {c['username']: c['messages'] for c in stats.get('topChatters', [])}
    chatters[username] = chatters.get(username, 0) + 1
    stats['topChatters'] = [
        {'username': u, 'messages': m}
        for u, m in sorted(chatters.items(), key=lambda x: x[1], reverse=True)
    ][:10]
    
    save_data(STATS_FILE, stats)

def update_stats(event):
    """Update stats with new sub/gift/bits event"""
    current_day = calculate_marathon_day()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Load existing data
    stats = load_existing_data(STATS_FILE) or {
        "lastUpdated": timestamp,
        "marathonStart": MARATHON_START,
        "currentDay": current_day,
        "stats": {
            "totalSubs": 0,
            "marathonSubs": 0,
            "totalFollowers": 0,
            "marathonFollowers": 0,
            "totalChats": 0
        },
        "dailySubs": {},
        "topGifters": [],
        "topChatters": []
    }
    
    daily_data = load_existing_data(DAILY_FILE) or {}
    day_key = f"day{current_day}"
    
    if day_key not in daily_data:
        daily_data[day_key] = {
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'subGifters': [],
            'bitDonors': [],
            'chatters': []
        }
    
    # Process event
    username = event['username']
    amount = event['amount']
    event_type = event['type']
    
    # Update totals
    if event_type in ['sub', 'gift']:
        stats['stats']['marathonSubs'] = stats['stats'].get('marathonSubs', 0) + amount
        
        # Update daily subs count
        if 'dailySubs' not in stats:
            stats['dailySubs'] = {}
        stats['dailySubs'][day_key] = stats['dailySubs'].get(day_key, 0) + amount
        
        # Update gifters leaderboard
        gifters = {g['username']: g['amount'] for g in stats.get('topGifters', [])}
        gifters[username] = gifters.get(username, 0) + amount
        stats['topGifters'] = [
            {'username': u, 'amount': a} 
            for u, a in sorted(gifters.items(), key=lambda x: x[1], reverse=True)
        ][:10]
        
        # Update daily gifters
        daily_gifters = {g['username']: g['amount'] for g in daily_data[day_key].get('subGifters', [])}
        daily_gifters[username] = daily_gifters.get(username, 0) + amount
        daily_data[day_key]['subGifters'] = [
            {'username': u, 'amount': a}
            for u, a in sorted(daily_gifters.items(), key=lambda x: x[1], reverse=True)
        ][:5]
    
    # Update timestamp
    stats['lastUpdated'] = timestamp
    stats['currentDay'] = current_day
    
    # Save everything
    save_data(STATS_FILE, stats)
    save_data(DAILY_FILE, daily_data)
    
    return stats

def main():
    """Main bot loop"""
    print("=" * 60)
    print("TWITCH CHAT BOT - AUTOMATIC SUB/BITS TRACKER")
    print("=" * 60)
    print(f"Channel: {CHANNEL_NAME}")
    print(f"Marathon Day: {calculate_marathon_day()}/28")
    print("=" * 60)
    
    # Connect to Twitch
    sock = connect_to_twitch(CHANNEL_NAME)
    
    print("\n🤖 Bot is listening for subs, gifts, and bits...")
    print("💡 This will run for 5 minutes to capture events\n")
    
    buffer = ""
    events_captured = 0
    chat_messages = 0
    import time
    start_time = time.time()
    timeout = 300  # 5 minutes
    
    try:
        while time.time() - start_time < timeout:
            try:
                sock.settimeout(1.0)
                response = sock.recv(2048).decode('utf-8')
                buffer += response
                
                # Process complete messages
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    
                    # Respond to PING
                    if line.startswith('PING'):
                        sock.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
                        continue
                    
                    # Count regular chat messages
                    if 'PRIVMSG' in line and 'display-name=' in line:
                        username_match = re.search(r'display-name=([^;]+)', line)
                        if username_match and 'msg-id=' not in line:
                            username = username_match.group(1)
                            count_chat_message(username)
                            chat_messages += 1
                    
                    # Parse for sub/gift/bits events
                    event = parse_irc_message(line)
                    if event:
                        events_captured += 1
                        print(f"✓ Captured {event['type'].upper()}: {event['username']} - {event['amount']}")
                        update_stats(event)
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error: {e}")
                continue
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Bot stopped by user")
    
    finally:
        sock.close()
        print("\n" + "=" * 60)
        print(f"✅ BOT SESSION COMPLETE")
        print("=" * 60)
        print(f"Events captured: {events_captured} (subs/
