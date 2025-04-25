#!/usr/bin/env python3
"""
Utility modules for SofaScore scraper
"""

# This file makes the utils directory a Python package
# It can be empty, but we'll add some useful imports for convenience

from utils.captcha_handler import is_captcha_present, wait_for_captcha_solution, handle_captcha
from utils.extractors import extract_matches_from_page, extract_matches_from_api_response, save_extracted_data
from utils.page_interactions import human_scroll, interact_with_page, random_mouse_movement