#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
import json
import os
from datetime import datetime

def fetch_matches_with_cookies(limit=5):
    """
    Advanced approach that:
    1. Lets you solve the CAPTCHA manually
    2. Captures all network requests to find API endpoints
    3. Saves cookies for future use
    4. Attempts to reuse successful request patterns
    """
    matches = []
    captured_requests = []
    
    with sync_playwright() as p:
        # Launch browser with visible UI
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # Create a page and set up request logging
        page = context.new_page()
        
        # Log all requests for analysis
        def capture_request(request):
            if "api.sofascore.com" in request.url and "/football/" in request.url:
                captured_requests.append({
                    "url": request.url,
                    "method": request.method,
                    "headers": request.headers,
                    "timestamp": datetime.now().isoformat()
                })
                print(f"Captured request to: {request.url}")
        
        page.on("request", capture_request)
        
        # Navigate to SofaScore
        print("Opening SofaScore website...")
        page.goto("https://www.sofascore.com/football", timeout=60000)
        
        # Check if CAPTCHA is present
        if is_captcha_present(page):
            print("\n*** CAPTCHA detected! ***")
            print("Please solve the CAPTCHA in the browser window.")
            input("Press Enter when you've completed the CAPTCHA... ")
        
        # Wait for page to load
        page.wait_for_load_state("networkidle", timeout=30000)
        page.screenshot(path="after_captcha.png")
        
        # Interact with the page to trigger API requests
        print("Interacting with page to trigger API requests...")
        interact_with_page(page)
        
        # Extract matches from the page content
        print("Attempting to extract matches from page content...")
        page_matches = extract_matches_from_page(page)
        if page_matches:
            print(f"Found {len(page_matches)} matches on page")
            matches.extend(page_matches)
        
        # Save captured request details for future use
        if captured_requests:
            print(f"Captured {len(captured_requests)} API requests")
            with open("sofascore_api_requests.json", "w") as f:
                json.dump(captured_requests, f, indent=2)
            print("API request details saved to sofascore_api_requests.json")
        
        # Save cookies for future use
        cookies = context.cookies()
        with open("sofascore_cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        print("Cookies saved to sofascore_cookies.json")
        
        # Ask user if they want to keep browser open
        keep_open = input("Keep browser open for inspection? (y/n): ").lower() == 'y'
        if keep_open:
            print("Browser kept open. Close it manually when done.")
            print("Examine the Network tab in DevTools to see API requests.")
            input("Press Enter to end the script...")
        
        browser.close()
    
    # Remove duplicates and limit results
    unique_matches = []
    seen_urls = set()
    
    for match in matches:
        if match["url"] not in seen_urls:
            seen_urls.add(match["url"])
            unique_matches.append(match)
            if len(unique_matches) >= limit:
                break
    
    return unique_matches

def is_captcha_present(page):
    """Check if a CAPTCHA is present on the page"""
    captcha_selectors = [
        "iframe[src*='captcha']",
        "iframe[src*='recaptcha']",
        "iframe[src*='cloudflare']",
        ".captcha-container",
        "#captcha",
        "div.g-recaptcha",
        "div[class*='captcha']"
    ]
    
    for selector in captcha_selectors:
        if page.query_selector(selector):
            return True
    
    title = page.title().lower()
    if "captcha" in title or "security check" in title:
        return True
    
    content = page.content().lower()
    captcha_terms = ["captcha", "security check", "cloudflare", "verify you are human"]
    if any(term in content for term in captcha_terms):
        return True
    
    return False

def interact_with_page(page):
    """Interact with the page naturally to trigger API requests"""
    # Scroll down slowly
    for i in range(5):
        page.evaluate(f"window.scrollBy(0, {100 + (i * 50)})")
        time.sleep(1 + (time.time() % 1))
    
    # Try clicking on tabs or navigation elements
    selectors_to_try = [
        "a[href='/football/']",
        ".tabs a",
        "nav a",
        "[data-sport='football']",
        ".tournament-page-tab"
    ]
    
    for selector in selectors_to_try:
        elements = page.query_selector_all(selector)
        for i, element in enumerate(elements[:3]):  # Try first 3 elements only
            try:
                print(f"Clicking on {selector} element {i}")
                element.click()
                time.sleep(2)
                page.screenshot(path=f"after_click_{i}.png")
            except Exception as e:
                print(f"Error clicking element: {e}")
    
    # Final scroll to see more content
    page.evaluate("window.scrollTo(0, 0)")  # Back to top
    time.sleep(1)
    page.evaluate("window.scrollBy(0, 500)")  # Down again
    time.sleep(3)  # Wait for any API calls to complete

def extract_matches_from_page(page):
    """Extract match information from the page content"""
    return page.evaluate("""() => {
        // Try multiple selectors to find match elements
        const matchElements = [
            ...document.querySelectorAll('a[href*="/event/"]'),
            ...document.querySelectorAll('div[data-id]'),
            ...document.querySelectorAll('li.event-list__item'),
            ...document.querySelectorAll('.event-block')
        ];
        
        console.log(`Found ${matchElements.length} potential match elements`);
        
        // Helper function to safely extract text
        const getText = (element) => element ? element.textContent.trim() : "Unknown";
        
        const matches = [];
        const seen = new Set();
        
        for (const element of matchElements) {
            try {
                // Extract URL
                let url;
                if (element.tagName === 'A' && element.href.includes('/event/')) {
                    url = element.href;
                } else {
                    const link = element.querySelector('a[href*="/event/"]');
                    if (link) url = link.href;
                }
                
                if (!url || seen.has(url)) continue;
                seen.add(url);
                
                // Try to find team names
                let homeTeam = "Unknown";
                let awayTeam = "Unknown";
                
                const teamElements = element.querySelectorAll('.teamName, .team-name, [data-home-team], [data-away-team], .participant__participantName');
                if (teamElements.length >= 2) {
                    homeTeam = getText(teamElements[0]);
                    awayTeam = getText(teamElements[1]);
                }
                
                // Find tournament name
                let tournament = "Unknown";
                const tournamentEl = element.querySelector('.tournament, .tournament-name, [data-tournament], .event__title--name');
                if (tournamentEl) {
                    tournament = getText(tournamentEl);
                }
                
                // Find match time
                let startTime = "Unknown";
                const timeEl = element.querySelector('.time, .event__time, [data-starttime]');
                if (timeEl) {
                    startTime = getText(timeEl);
                }
                
                // Find match status
                let status = "Scheduled";
                const statusEl = element.querySelector('.status, .event__status, [data-status]');
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
                console.error(`Error processing element: ${e.message}`);
            }
        }
        
        return matches;
    }""")

if __name__ == "__main__":
    print("Starting advanced SofaScore match extraction...")
    matches = fetch_matches_with_cookies(5)
    
    if not matches:
        print("\n❌ No matches found!")
        print("Check the generated screenshots and network captures for debugging")
    else:
        print(f"\n✅ Found {len(matches)} matches:")
        for i, m in enumerate(matches, 1):
            print(f"\nMatch {i}:")
            print(f"  • URL:        {m['url']}")
            print(f"  • Teams:      {m['home_team']} vs {m['away_team']}")
            print(f"  • Tournament: {m['tournament']}")
            print(f"  • Start time: {m['start_time']}")
            print(f"  • Status:     {m['status']}")
    
    # Save results
    with open("sofascore_matches.json", "w") as f:
        json.dump(matches, f, indent=2)
    print("\nResults saved to sofascore_matches.json")