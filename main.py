#!/usr/bin/env python3
"""
SofaScore Football Match Scraper - Main Entry Point

This script provides a command line interface to run different scraping methods
for retrieving football match data from SofaScore.
"""

import argparse
import os
import sys
import json
from datetime import datetime
from scrapers.api_scraper import fetch_live_and_upcoming_matches
from scrapers.browser_scraper import fetch_matches_with_browser
from scrapers.network_capture import fetch_matches_with_cookies

# Add parent directory to path to allow imports from modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import scrapers
from scrapers.api_scraper import fetch_live_and_upcoming_matches
from scrapers.browser_scraper import fetch_matches_with_browser
from scrapers.network_capture import fetch_matches_with_cookies

def setup_directories():
    """Create necessary directories if they don't exist"""
    dirs = [
        "data",
        "data/cookies",
        "data/api_requests",
        "data/matches"
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)

def save_results(matches, method):
    """Save match results to file with timestamp"""
    if not matches:
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/matches/sofascore_matches_{method}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(matches, f, indent=2)
    
    print(f"\nResults saved to {filename}")
    return filename

def print_results(matches):
    """Print match results to console"""
    if not matches:
        print("\n❌ No matches found!")
        return
        
    print(f"\n✅ Found {len(matches)} matches:")
    for i, m in enumerate(matches, 1):
        print(f"\nMatch {i}:")
        print(f"  • URL:        {m['url']}")
        print(f"  • Teams:      {m['home_team']} vs {m['away_team']}")
        print(f"  • Tournament: {m['tournament']}")
        print(f"  • Start time: {m['start_time']}")
        print(f"  • Status:     {m['status']}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SofaScore Football Match Scraper")
    parser.add_argument(
        "--method", "-m",
        choices=["api", "browser", "network"],
        default="browser",
        help="Scraping method to use (default: browser)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=5,
        help="Maximum number of matches to retrieve (default: 5)"
    )
    parser.add_argument(
        "--headless", 
        action="store_true",
        help="Run browser in headless mode (browser/network methods only)"
    )
    parser.add_argument(
        "--save-only",
        action="store_true",
        help="Save results to file without printing to console"
    )
    
    args = parser.parse_args()
    setup_directories()
    
    print(f"Starting SofaScore match extraction using {args.method} method...")
    matches = []
    
    try:
        if args.method == "api":
            matches = fetch_live_and_upcoming_matches(limit=args.limit)
        elif args.method == "browser":
            matches = fetch_matches_with_browser(limit=args.limit, headless=args.headless)
        elif args.method == "network":
            matches = fetch_matches_with_cookies(limit=args.limit, headless=args.headless)
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    # Save results
    saved_file = save_results(matches, args.method)
    
    # Print results if not save-only mode
    if not args.save_only:
        print_results(matches)
    else:
        if saved_file:
            print(f"Results saved to {saved_file}")
        else:
            print("No results to save")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())