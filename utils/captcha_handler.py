#!/usr/bin/env python3
"""
CAPTCHA detection and handling utilities for SofaScore scraper.
"""

import time
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SELECTORS

def is_captcha_present(page):
    """
    Check if a CAPTCHA is present on the page using multiple detection methods.
    
    Args:
        page: Playwright page object
        
    Returns:
        bool: True if CAPTCHA is detected, False otherwise
    """
    # Check for common CAPTCHA elements using selectors from config
    for selector in SELECTORS["captcha"]:
        if page.query_selector(selector):
            return True
    
    # Check page title for CAPTCHA-related text
    title = page.title().lower()
    captcha_title_terms = ["captcha", "security check", "cloudflare", "human verification"]
    if any(term in title for term in captcha_title_terms):
        return True
        
    # Check page content for CAPTCHA-related text
    content = page.content().lower()
    captcha_content_terms = [
        "captcha", 
        "security check", 
        "cloudflare", 
        "verify you are human", 
        "bot protection",
        "prove you are human",
        "complete the security check",
        "access denied",
        "ddos protection"
    ]
    if any(term in content for term in captcha_content_terms):
        return True
        
    return False

def wait_for_captcha_solution(page, captcha_timeout=300):
    """
    Wait for the user to solve a CAPTCHA.
    
    Args:
        page: Playwright page object
        captcha_timeout: Maximum time to wait for CAPTCHA solution in seconds
        
    Returns:
        bool: True if CAPTCHA was solved, False if timeout occurred
    """
    print("\n*** CAPTCHA detected! ***")
    print("Please solve the CAPTCHA in the browser window.")
    
    # Take a screenshot of the CAPTCHA
    screenshot_path = "data/screenshots/captcha.png"
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
    page.screenshot(path=screenshot_path)
    print(f"CAPTCHA screenshot saved to {screenshot_path}")
    
    # Prompt user to solve the CAPTCHA
    print("Press Enter when you've completed the CAPTCHA... ", end="")
    
    # Set up timeout for input
    result = {"solved": False}
    
    def input_thread():
        input()  # Wait for Enter key
        result["solved"] = True
    
    # Start input thread
    import threading
    t = threading.Thread(target=input_thread)
    t.daemon = True
    t.start()
    
    # Wait for input or timeout
    start_time = time.time()
    while time.time() - start_time < captcha_timeout:
        if result["solved"]:
            print("CAPTCHA solution confirmed.")
            
            # Wait for page to update after CAPTCHA
            time.sleep(2)
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Verify CAPTCHA is actually solved
            if is_captcha_present(page):
                print("⚠️  CAPTCHA still detected. Please try again.")
                return wait_for_captcha_solution(page, captcha_timeout - (time.time() - start_time))
            
            return True
        time.sleep(0.1)
    
    print("\n⚠️  Timeout waiting for CAPTCHA solution.")
    return False

def handle_captcha(page, max_attempts=3):
    """
    Complete CAPTCHA handling process with verification and retries.
    
    Args:
        page: Playwright page object
        max_attempts: Maximum number of CAPTCHA solving attempts
        
    Returns:
        bool: True if CAPTCHA was successfully solved, False otherwise
    """
    attempts = 0
    
    while attempts < max_attempts:
        if not is_captcha_present(page):
            return True
            
        attempts += 1
        print(f"CAPTCHA solving attempt {attempts}/{max_attempts}")
        
        if wait_for_captcha_solution(page):
            # Take a screenshot after solving
            page.screenshot(path=f"data/screenshots/after_captcha_{attempts}.png")
            
            # Verify CAPTCHA is solved by checking if we can access content
            time.sleep(3)  # Wait for any redirects
            
            # Check if we still have a CAPTCHA
            if not is_captcha_present(page):
                print("✓ CAPTCHA successfully solved!")
                return True
            else:
                print("⚠️  CAPTCHA solution didn't work. Let's try again.")
        else:
            print("⚠️  Failed to solve CAPTCHA in time.")
    
    print(f"❌ Failed to solve CAPTCHA after {max_attempts} attempts.")
    return False