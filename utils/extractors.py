#!/usr/bin/env python3
"""
Data extraction utilities for SofaScore scraper.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SELECTORS

def extract_matches_from_page(page):
    """
    Extract match information from the page using JavaScript.
    
    Args:
        page: Playwright page object
        
    Returns:
        list: List of match dictionaries
    """
    # Get selectors from config
    match_containers_selectors = SELECTORS["match_containers"]
    team_names_selectors = SELECTORS["team_names"]
    tournament_selectors = SELECTORS["tournament"]
    start_time_selectors = SELECTORS["start_time"]
    status_selectors = SELECTORS["status"]
    
    # Convert selector lists to JS arrays
    match_containers_js = json.dumps(match_containers_selectors)
    team_names_js = json.dumps(team_names_selectors)
    tournament_js = json.dumps(tournament_selectors)
    start_time_js = json.dumps(start_time_selectors)
    status_js = json.dumps(status_selectors)
    
    # Execute JavaScript to extract match data
    return page.evaluate(f"""() => {{
        // Helper function to extract text safely
        const getText = (element) => {{
            return element ? element.textContent.trim() : "Unknown";
        }};
        
        // Helper function to try multiple selectors
        const trySelectors = (container, selectors) => {{
            for (const selector of selectors) {{
                const elements = container.querySelectorAll(selector);
                if (elements && elements.length > 0) {{
                    return elements;
                }}
            }}
            return [];
        }};
        
        // Find match containers with various selectors
        const matchContainerSelectors = {match_containers_js};
        const allContainers = [];
        
        for (const selector of matchContainerSelectors) {{
            const containers = document.querySelectorAll(selector);
            if (containers.length > 0) {{
                console.log(`Found ${containers.length} containers with selector ${selector}`);
                allContainers.push(...containers);
            }}
        }}
        
        console.log(`Total potential match containers found: ${allContainers.length}`);
        
        const matches = [];
        const seen = new Set();
        
        for (const container of allContainers) {{
            try {{
                // Try to find the link
                let url;
                if (container.tagName === 'A' && container.href && container.href.includes('/event/')) {{
                    url = container.href;
                }} else {{
                    const link = container.querySelector('a[href*="/event/"]');
                    if (link) {{
                        url = link.href;
                    }}
                }}
                
                if (!url || seen.has(url)) continue;
                seen.add(url);
                
                // Find team names using multiple selector approaches
                let homeTeam = "Unknown";
                let awayTeam = "Unknown";
                
                const teamElements = trySelectors(container, {team_names_js});
                if (teamElements.length >= 2) {{
                    homeTeam = getText(teamElements[0]);
                    awayTeam = getText(teamElements[1]);
                }}
                
                // Try to find tournament name
                let tournament = "Unknown";
                const tournamentSelectors = {tournament_js};
                for (const selector of tournamentSelectors) {{
                    const el = container.querySelector(selector);
                    if (el) {{
                        tournament = getText(el);
                        break;
                    }}
                }}
                
                // Try to find match time
                let startTime = "Unknown";
                const timeSelectors = {start_time_js};
                for (const selector of timeSelectors) {{
                    const el = container.querySelector(selector);
                    if (el) {{
                        startTime = getText(el);
                        break;
                    }}
                }}
                
                // Try to find match status
                let status = "Scheduled";
                const statusSelectors = {status_js};
                for (const selector of statusSelectors) {{
                    const el = container.querySelector(selector);
                    if (el) {{
                        status = getText(el);
                        break;
                    }}
                }}
                
                matches.push({{
                    url,
                    home_team: homeTeam,
                    away_team: awayTeam,
                    tournament,
                    start_time: startTime,
                    status
                }});
            }} catch (e) {{
                console.error(`Error processing match container: ${e.message}`);
            }}
        }}
        
        return matches;
    }}""")

def extract_matches_from_api_response(response_data):
    """
    Extract match information from SofaScore API response data.
    
    Args:
        response_data: JSON data from SofaScore API
        
    Returns:
        list: List of match dictionaries
    """
    matches = []
    seen_ids = set()
    
    # Try to extract events from various API response formats
    events = []
    
    # Pattern 1: Direct events array
    if "events" in response_data:
        events.extend(response_data["events"])
        
    # Pattern 2: Nested within sportItem > tournaments
    elif "sportItem" in response_data and "tournaments" in response_data["sportItem"]:
        for tournament in response_data["sportItem"].get("tournaments", []):
            if "events" in tournament:
                events.extend(tournament["events"])
    
    # Process events
    for ev in events:
        ev_id = ev.get("id")
        if not ev_id or ev_id in seen_ids:
            continue
            
        seen_ids.add(ev_id)
        
        # Extract match info
        home = ev.get("homeTeam", {}).get("name", "Unknown")
        away = ev.get("awayTeam", {}).get("name", "Unknown")
        tour = ev.get("tournament", {}).get("name", "Unknown")
        
        # Handle timestamp
        ts = ev.get("startTimestamp")
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
            
    return matches

def parse_network_requests(captured_requests):
    """
    Analyze captured network requests to identify API patterns.
    
    Args:
        captured_requests: List of captured request objects
        
    Returns:
        dict: Analysis of request patterns
    """
    analysis = {
        "endpoints": {},
        "common_headers": {},
        "request_rate": 0
    }
    
    if not captured_requests:
        return analysis
    
    # Analyze endpoints
    for req in captured_requests:
        url = req.get("url", "")
        if url:
            # Extract endpoint path
            parts = url.split("/api/")
            if len(parts) > 1:
                endpoint = "/api/" + parts[1]
                analysis["endpoints"][endpoint] = analysis["endpoints"].get(endpoint, 0) + 1
    
    # Find common headers
    if captured_requests:
        # Start with all headers from first request
        common_headers = dict(captured_requests[0].get("headers", {}))
        
        # Find intersection with all other requests
        for req in captured_requests[1:]:
            headers = req.get("headers", {})
            # Keep only headers that appear in this request too
            for key in list(common_headers.keys()):
                if key not in headers or headers[key] != common_headers[key]:
                    common_headers.pop(key, None)
        
        analysis["common_headers"] = common_headers
    
    # Calculate request rate (requests per second)
    if len(captured_requests) > 1:
        try:
            first_time = datetime.fromisoformat(captured_requests[0].get("timestamp", ""))
            last_time = datetime.fromisoformat(captured_requests[-1].get("timestamp", ""))
            duration = (last_time - first_time).total_seconds()
            if duration > 0:
                analysis["request_rate"] = len(captured_requests) / duration
        except (ValueError, TypeError):
            pass
    
    return analysis

def save_extracted_data(matches, filename):
    """
    Save extracted match data to a file.
    
    Args:
        matches: List of match dictionaries
        filename: Path to save the data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save data
        with open(filename, "w") as f:
            json.dump(matches, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")
        return False