#!/usr/bin/env python3
"""
SofaScore Football Match Scraping Modules
"""

# This file makes the scrapers directory a Python package
# It can be empty, but we'll add some useful imports for convenience

from scrapers.api_scraper import fetch_live_and_upcoming_matches
from scrapers.browser_scraper import fetch_matches_with_browser 
from scrapers.network_capture import fetch_matches_with_cookies