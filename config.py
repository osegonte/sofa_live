#!/usr/bin/env python3
"""
Configuration settings for SofaScore scraper
"""

# API Configuration
API_CONFIG = {
    "base_url": "https://api.sofascore.com/api/v1",
    "endpoints": {
        "live": "/sport/football/events/live",
        "scheduled": "/sport/football/scheduled-events/",
        "tournament": "/sport/football/tournament/{tournament_id}/season/{season_id}/matches",
        "match": "/event/{event_id}"
    },
    "timeout": 10,  # seconds
    "retry_attempts": 3,
    "retry_delay": 2  # seconds
}

# Browser Configuration
BROWSER_CONFIG = {
    "url": "https://www.sofascore.com/football",
    "timeout": {
        "navigation": 60000,  # ms
        "element": 30000,     # ms
        "captcha_wait": 300   # seconds (5 min max)
    },
    "user_agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "viewport": {
        "width": 1280,
        "height": 800
    },
    "scroll_behavior": {
        "count": 5,           # number of scrolls
        "distance": 300,      # base scroll distance in pixels
        "variance": 100,      # random variance added to distance
        "delay": 1.5,         # base delay between scrolls
        "delay_variance": 1.0 # random variance added to delay
    }
}

# CSS Selectors for match extraction
SELECTORS = {
    "captcha": [
        "iframe[src*='captcha']",
        "iframe[src*='recaptcha']",
        "iframe[src*='cloudflare']",
        ".captcha-container",
        "#captcha",
        "div.g-recaptcha",
        "div[class*='captcha']"
    ],
    "match_containers": [
        "a[href*='/event/']",
        "div[data-id]",
        "li.event-list__item",
        ".event-block",
        "[data-tournament]"
    ],
    "team_names": [
        ".teamName", 
        ".team-name", 
        "[data-home-team]", 
        "[data-away-team]", 
        ".participant__participantName"
    ],
    "tournament": [
        ".tournament", 
        ".tournament-name", 
        "[data-tournament]", 
        ".event__title--name"
    ],
    "start_time": [
        ".time", 
        ".event__time", 
        "[data-starttime]"
    ],
    "status": [
        ".status", 
        ".event__status", 
        "[data-status]"
    ]
}

# Path Configuration
PATHS = {
    "cookies": "data/cookies/sofascore_cookies.json",
    "api_requests": "data/api_requests/sofascore_api_requests.json",
    "matches": "data/matches/",
    "screenshots": "data/screenshots/"
}

# Default scraping parameters
DEFAULT_CONFIG = {
    "method": "browser",  # "api", "browser", or "network"
    "limit": 5,           # Number of matches to fetch
    "headless": False,    # Run browser in headless mode
    "save_to_file": True  # Save results to file
}