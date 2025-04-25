#!/usr/bin/env python3
"""
Utilities for realistic human-like page interactions to avoid bot detection.
"""

import time
import random
import os
import sys
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BROWSER_CONFIG

def human_scroll(page, iterations=None, screenshot_prefix=None):
    """
    Perform human-like scrolling on a page.
    
    Args:
        page: Playwright page object
        iterations: Number of scroll actions (defaults to config value)
        screenshot_prefix: If provided, save screenshots with this prefix
        
    Returns:
        None
    """
    # Get config values
    config = BROWSER_CONFIG["scroll_behavior"]
    scroll_count = iterations if iterations is not None else config["count"]
    base_distance = config["distance"]
    variance = config["variance"] 
    base_delay = config["delay"]
    delay_variance = config["delay_variance"]
    
    print(f"Scrolling page gradually ({scroll_count} iterations)...")
    
    for i in range(scroll_count):
        # Calculate random scroll distance
        distance = base_distance + random.randint(-variance, variance)
        if distance < 50:  # Ensure minimum effective scroll
            distance = 50
            
        # Execute scroll
        page.evaluate(f"window.scrollBy(0, {distance})")
        
        # Save screenshot if requested
        if screenshot_prefix:
            screenshot_path = f"data/screenshots/{screenshot_prefix}_scroll_{i+1}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            page.screenshot(path=screenshot_path)
        
        # Random delay between scrolls
        delay = base_delay + (random.random() * delay_variance)
        time.sleep(delay)
    
    # Occasionally scroll back up a bit (like a human looking for something)
    if random.random() < 0.3:
        up_distance = random.randint(100, 300)
        page.evaluate(f"window.scrollBy(0, -{up_distance})")
        time.sleep(base_delay)

def random_mouse_movement(page, min_movements=3, max_movements=8):
    """
    Perform random mouse movements to appear more human-like.
    
    Args:
        page: Playwright page object
        min_movements: Minimum number of mouse movements
        max_movements: Maximum number of mouse movements
        
    Returns:
        None
    """
    viewport = BROWSER_CONFIG["viewport"]
    width, height = viewport["width"], viewport["height"]
    
    movements = random.randint(min_movements, max_movements)
    
    for _ in range(movements):
        # Generate random coordinates within viewport
        x = random.randint(10, width - 10)
        y = random.randint(10, height - 10)
        
        # Move mouse
        page.mouse.move(x, y)
        
        # Random pause
        time.sleep(0.1 + (random.random() * 0.3))
    
    # Occasionally do a click
    if random.random() < 0.2:
        safe_click_random(page)

def safe_click_random(page, avoid_links=True):
    """
    Perform a safe click at a random position that won't navigate away.
    
    Args:
        page: Playwright page object
        avoid_links: If True, try to avoid clicking on links
        
    Returns:
        None
    """
    viewport = BROWSER_CONFIG["viewport"]
    width, height = viewport["width"], viewport["height"]
    
    # Try to find a safe area to click
    max_attempts = 5
    for _ in range(max_attempts):
        # Generate random coordinates within viewport
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        
        if avoid_links:
            # Check if there's a link at this position
            element = page.evaluate(f"""() => {{
                const element = document.elementFromPoint({x}, {y});
                if (element) {{
                    const isLink = element.tagName === 'A' || 
                                  element.closest('a') !== null;
                    return isLink ? 'link' : 'safe';
                }}
                return 'unknown';
            }}""")
            
            if element == 'safe':
                page.mouse.click(x, y)
                return
        else:
            # Just click
            page.mouse.click(x, y)
            return
    
    # If we couldn't find a safe spot, click in the middle of the page
    page.mouse.click(width // 2, height // 2)

def interact_with_page(page, save_screenshots=True):
    """
    Perform a series of human-like interactions with the page.
    
    Args:
        page: Playwright page object
        save_screenshots: Whether to save screenshots
        
    Returns:
        None
    """
    print("Interacting with page naturally...")
    
    # Initial wait for page to stabilize
    time.sleep(1 + (random.random() * 2))
    
    # Initial screenshot
    if save_screenshots:
        page.screenshot(path="data/screenshots/before_interaction.png")
    
    # Scroll down gradually
    human_scroll(page, screenshot_prefix="interaction" if save_screenshots else None)
    
    # Try clicking on navigation elements or tabs that won't navigate away
    selectors_to_try = [
        "nav a[href='#']",
        ".tabs button",
        ".tab-content",
        "div[role='tab']",
        ".sports-filter",
        ".tournament-filter",
        "[data-sport='football']",
        ".tournament-page-tab"
    ]
    
    # Try clicking a few navigation elements
    clicks = 0
    max_clicks = 3
    
    for selector in selectors_to_try:
        elements = page.query_selector_all(selector)
        for i, element in enumerate(elements[:2]):  # Try first 2 elements only
            try:
                # Check if this element will cause navigation
                will_navigate = page.evaluate("""(element) => {
                    return element.tagName === 'A' && 
                           element.href && 
                           !element.href.includes('#') &&
                           !element.target;
                }""", element)
                
                if not will_navigate:
                    print(f"Clicking on {selector} element {i}")
                    element.click()
                    time.sleep(1 + (random.random() * 2))
                    
                    if save_screenshots:
                        page.screenshot(path=f"data/screenshots/after_click_{clicks}.png")
                    
                    clicks += 1
                    if clicks >= max_clicks:
                        break
            except Exception as e:
                print(f"Error clicking element: {e}")
        
        if clicks >= max_clicks:
            break
    
    # Random mouse movements
    random_mouse_movement(page)
    
    # Final scroll with different pattern
    if random.random() < 0.5:
        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        
        # Then scroll down again
        human_scroll(page, iterations=2)
    else:
        # Scroll a bit more
        human_scroll(page, iterations=2)
    
    # Final screenshot
    if save_screenshots:
        page.screenshot(path="data/screenshots/after_interaction.png")
    
    # Wait for any triggered content to load
    time.sleep(3 + (random.random() * 2))