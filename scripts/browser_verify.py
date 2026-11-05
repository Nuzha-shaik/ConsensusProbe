#!/usr/bin/env python3
"""Run automated browser inspection with Playwright to verify UI and catch console errors."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = ROOT / "results" / "browser_screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def run_browser_verification():
    from playwright.sync_api import sync_playwright

    print("=" * 60)
    print("Launching Playwright Chromium browser...")
    print("=" * 60)

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        # 1. Open Landing Page
        print("Navigating to http://127.0.0.1:5173...")
        page.goto("http://127.0.0.1:5173", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOTS_DIR / "01_landing_hero.png"))
        print(f"Captured: {SCREENSHOTS_DIR / '01_landing_hero.png'}")

        # 2. Check if Hero strip and samples are visible
        hero_text = page.locator("text=Three AI cleaners propose").count()
        print(f"Hero pitch found: {hero_text > 0}")

        # 3. Test Clean Sample Button
        clean_sample_btn = page.locator("button:has-text('retail_clean.csv')")
        if clean_sample_btn.count() > 0:
            print("Clicking Clean Sample button...")
            clean_sample_btn.first.click()
            time.sleep(2)
            page.screenshot(path=str(SCREENSHOTS_DIR / "02_clean_sample_profile.png"))
            print(f"Captured: {SCREENSHOTS_DIR / '02_clean_sample_profile.png'}")

        # 4. Click Run ConsensusGate
        run_gate_btn = page.locator("button:has-text('Run ConsensusGate')")
        if run_gate_btn.count() > 0:
            print("Clicking Run ConsensusGate...")
            run_gate_btn.first.click()
            time.sleep(2)
            page.screenshot(path=str(SCREENSHOTS_DIR / "03_swarm_command_center.png"))
            print(f"Captured: {SCREENSHOTS_DIR / '03_swarm_command_center.png'}")

        # 5. Check Threshold Simulator
        slider = page.locator("input[type='range']")
        print(f"Threshold slider found: {slider.count() > 0}")

        browser.close()

    print("=" * 60)
    print("Browser Verification Summary:")
    print(f"Console errors/warnings caught: {len(console_errors)}")
    for err in console_errors:
        print(f"  {err}")
    print(f"Page uncaught exceptions: {len(page_errors)}")
    for err in page_errors:
        print(f"  {err}")
    print("=" * 60)

    return 0 if len(page_errors) == 0 else 1

if __name__ == "__main__":
    sys.exit(run_browser_verification())
