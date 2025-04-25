#!/usr/bin/env python3
import requests
import time
from datetime import datetime

def fetch_live_and_upcoming_matches(limit: int = 5) -> list[dict]:
    """
    Fetch live football matches first, then upcoming scheduled matches if needed,
    stopping as soon as we've collected `limit` distinct events.
    """
    BASE_URL = "https://api.sofascore.com/api/v1"
    now_ms = int(time.time() * 1000)  # milliseconds for scheduled‐events
    
    # More authentic headers - important for avoiding 403 errors
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        ),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.sofascore.com/football',
        'Origin': 'https://www.sofascore.com',
        'sec-ch-ua': '"Chromium";v="122", "Google Chrome";v="122", "Not(A:Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site'
    }
    
    # Try different API patterns
    endpoints = [
        # Standard endpoints
        f"{BASE_URL}/sport/football/events/live",
        f"{BASE_URL}/sport/football/scheduled-events/{now_ms}",
        # Alternative endpoint patterns
        f"{BASE_URL}/sport/football/livescores/json",
        f"{BASE_URL}/football/live-feed", 
        # Date-based endpoints (today's games)
        f"{BASE_URL}/sport/football/scheduled-events/{time.strftime('%Y-%m-%d')}",
        # Mobile endpoints sometimes have different access rules
        f"{BASE_URL}/mobile/sport/football/live",
        # Try a web-friendly endpoint format that might be used by website
        f"https://www.sofascore.com/football/livescore/json"
    ]
    
    seen_ids = set()
    matches = []
    
    for endpoint in endpoints:
        try:
            print(f"Trying endpoint: {endpoint}")
            
            # Add random delay between requests to avoid rate limiting
            if endpoints.index(endpoint) > 0:
                delay = 1 + (time.time() % 1)  # Random delay between 1-2 seconds
                time.sleep(delay)
                
            session = requests.Session()
            
            # First visit the main site to get cookies
            if endpoints.index(endpoint) == 0:  # Only do this for the first endpoint
                print("  › Establishing session cookies...")
                session.get("https://www.sofascore.com/football", 
                           headers=headers, timeout=10)
            
            # Now make the API request
            resp = session.get(endpoint, headers=headers, timeout=10)
            
            # Print status for debugging
            print(f"  › Status: {resp.status_code}")
            
            resp.raise_for_status()
            
            data = resp.json()
            
            # Pull out events array from whichever shape the API returned
            events = data.get("events", [])
            if not events and "sportItem" in data:
                for tour in data["sportItem"].get("tournaments", []):
                    events.extend(tour.get("events", []))
                    
            print(f"  → Found {len(events)} events at this endpoint")
            
            for ev in events:
                ev_id = ev.get("id")
                if not ev_id or ev_id in seen_ids:
                    continue
                    
                seen_ids.add(ev_id)
                
                # Build a minimal match record
                home = ev.get("homeTeam", {}).get("name", "Unknown")
                away = ev.get("awayTeam", {}).get("name", "Unknown")
                tour = ev.get("tournament", {}).get("name", "Unknown")
                ts   = ev.get("startTimestamp")
                start = (
                    datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    if isinstance(ts, (int, float)) else "Unknown"
                )
                status = ev.get("status", {}).get("description", "Scheduled")
                
                matches.append({
                    "url": f"https://www.sofascore.com/event/{ev_id}",
                    "home_team": home,
                    "away_team": away,
                    "tournament": tour,
                    "start_time": start,
                    "status": status
                })
                
                if len(matches) >= limit:
                    return matches
        except Exception as e:
            print(f"  › Error fetching {endpoint}: {e}")
            continue
                
    return matches

if __name__ == "__main__":
    print("Starting SofaScore match extraction…")
    results = fetch_live_and_upcoming_matches(limit=5)
    
    if not results:
        print("❌ No matches found! SofaScore API may have changed.")
    else:
        print(f"✅ Collected {len(results)} matches:")
        for i, m in enumerate(results, 1):
            print(f"\nMatch {i}:")
            print(f"  • URL:        {m['url']}")
            print(f"  • Teams:      {m['home_team']} vs {m['away_team']}")
            print(f"  • Tournament: {m['tournament']}")
            print(f"  • Start time: {m['start_time']}")
            print(f"  • Status:     {m['status']}")