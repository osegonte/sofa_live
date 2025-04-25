#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import json
import os

def fetch_matches_with_browser(limit=5):
    """
    Fetch football matches by controlling a browser with Playwright.
    Pauses for manual CAPTCHA solving when needed.
    """
    matches = []
    
    with sync_playwright() as p:
        # Launch the browser visibly
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        print("Opening SofaScore website...")
        
        try:
            # Navigate to SofaScore
            page.goto("https://www.sofascore.com/football", timeout=60000)
            
            # Check if CAPTCHA is present and wait for manual solving
            if is_captcha_present(page):
                print("\n*** CAPTCHA detected! ***")
                print("Please solve the CAPTCHA in the browser window.")
                input("Press Enter when you've completed the CAPTCHA... ")
                print("Continuing...")
            
            # Wait for page to be fully loaded
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Take a screenshot
            page.screenshot(path="sofascore_after_captcha.png")
            print("Page loaded, screenshot saved")
            
            # Scroll gently to load content
            print("Scrolling to load content...")
            for i in range(3):
                page.evaluate("window.scrollBy(0, 300)")
                time.sleep(2)
            
            # Wait for any potential API responses to load
            time.sleep(5)
            
            # Extract match data using JavaScript
            print("Extracting match data...")
            matches_data = extract_matches_from_page(page)
            
            if matches_data:
                print(f"Found {len(matches_data)} matches on page")
                matches.extend(matches_data[:limit])
                
                # Save raw data for debugging
                with open("matches_raw_data.json", "w") as f:
                    json.dump(matches_data, f, indent=2)
                print("Raw match data saved to matches_raw_data.json")
            else:
                print("No matches found in page content")
                page.screenshot(path="no_matches_found.png")
        
        except Exception as e:
            print(f"Error during browsing: {e}")
            page.screenshot(path="error_state.png")
        
        finally:
            # Ask if user wants to keep browser open
            keep_open = input("Keep browser open for manual inspection? (y/n): ").lower() == 'y'
            if not keep_open:
                browser.close()
            else:
                print("Browser left open. Close it manually when finished.")
                # Keep script running until user decides to close
                input("Press Enter to end the script...")
                try:
                    browser.close()
                except:
                    pass
    
    return matches

def is_captcha_present(page):
    """Check if a CAPTCHA is present on the page"""
    # Check for common CAPTCHA elements
    captcha_selectors = [
        "iframe[src*='captcha']",
        "iframe[src*='recaptcha']",
        "iframe[src*='cloudflare']",
        ".captcha-container",
        "#captcha",
        "div.g-recaptcha",
        "div[class*='captcha']",
        "div[id*='captcha']",
        "cloudflare-challenge"
    ]
    
    for selector in captcha_selectors:
        if page.query_selector(selector):
            return True
    
    # Also check page title and content for CAPTCHA-related text
    title = page.title().lower()
    if "captcha" in title or "security check" in title or "cloudflare" in title:
        return True
        
    # Check page content for CAPTCHA-related text
    content = page.content().lower()
    captcha_terms = ["captcha", "security check", "cloudflare", "verify you are human", "bot protection"]
    if any(term in content for term in captcha_terms):
        return True
        
    return False

def extract_matches_from_page(page):
    """Use JavaScript to extract match data from the page"""
    return page.evaluate("""() => {
        // Helper function to extract text safely
        const getText = (element) => {
            return element ? element.textContent.trim() : "Unknown";
        };
        
        // Look for matches using various selectors
        const matchContainers = [
            ...document.querySelectorAll('a[href*="/event/"]'),
            ...document.querySelectorAll('div[data-id]'),
            ...document.querySelectorAll('li.event-list__item'),
            ...document.querySelectorAll('.event-block'),
            ...document.querySelectorAll('[data-tournament]')
        ];
        
        console.log(`Potential match containers found: ${matchContainers.length}`);
        
        const matches = [];
        const seen = new Set();
        
        for (const container of matchContainers) {
            try {
                // Try to find the link
                let url;
                if (container.tagName === 'A' && container.href.includes('/event/')) {
                    url = container.href;
                } else {
                    const link = container.querySelector('a[href*="/event/"]');
                    if (link) {
                        url = link.href;
                    }
                }
                
                if (!url || seen.has(url)) continue;
                seen.add(url);
                
                // Debug what we found
                console.log(`Found match link: ${url}`);
                
                // Find team names
                let homeTeam = "Unknown";
                let awayTeam = "Unknown";
                
                // Try multiple approaches to find team names
                const teamElements = container.querySelectorAll('.teamName, .team-name, [data-home-team], [data-away-team], .participant__participantName');
                if (teamElements.length >= 2) {
                    homeTeam = getText(teamElements[0]);
                    awayTeam = getText(teamElements[1]);
                }
                
                // Try to find tournament name
                let tournament = "Unknown";
                const tournamentEl = container.querySelector('.tournament, .tournament-name, [data-tournament], .event__title--name');
                if (tournamentEl) {
                    tournament = getText(tournamentEl);
                }
                
                // Try to find match time
                let startTime = "Unknown";
                const timeEl = container.querySelector('.time, .event__time, [data-starttime]');
                if (timeEl) {
                    startTime = getText(timeEl);
                }
                
                // Try to find match status
                let status = "Scheduled";
                const statusEl = container.querySelector('.status, .event__status, [data-status]');
                if (statusEl) {
                    status = getText(statusEl);
                }
                
                matches.push({
                    url,
                    home_team: homeTeam,
                    away_team: awayTeam,
                    tournament,
                    start_time: startTime,
                    status
                });
            } catch (e) {
                console.error(`Error processing match: ${e.message}`);
            }
        }
        
        return matches;
    }""")

if __name__ == "__main__":
    print("Starting SofaScore match extraction with manual CAPTCHA handling...\n")
    matches = fetch_matches_with_browser(5)
    
    if not matches:
        print("\n❌ No matches found!")
        print("Check the screenshots to see what's happening")
    else:
        print(f"\n✅ Successfully found {len(matches)} matches:")
        for i, m in enumerate(matches, 1):
            print(f"\nMatch {i}:")
            print(f"  • URL:        {m['url']}")
            print(f"  • Teams:      {m['home_team']} vs {m['away_team']}")
            print(f"  • Tournament: {m['tournament']}")
            print(f"  • Start time: {m['start_time']}")
            print(f"  • Status:     {m['status']}")
    
    # Save results to file
    with open("sofascore_matches.json", "w") as f:
        json.dump(matches, f, indent=2)
    print("\nResults saved to sofascore_matches.json")