"""Browser automation helper functions for web scraping."""

import time
from .config import BROWSER_CONFIG, SELECTORS, EXTRACTION_CONFIG


def scroll_to_bottom(page, pause_time: float = None):
    """Scroll to the bottom of the page gradually to load lazy-loaded content.

    This function performs incremental scrolling to trigger lazy-loading of
    content on the page. It continues scrolling until the page height stops
    changing or the maximum number of attempts is reached.

    Parameters
    ----------
    page : Page
        Playwright page object to scroll
    pause_time : float, optional
        Time to pause between scroll attempts (default: from config)
    """
    if pause_time is None:
        pause_time = BROWSER_CONFIG['scroll_pause']

    last_height = page.evaluate("document.body.scrollHeight")
    scroll_attempts = 0
    max_attempts = EXTRACTION_CONFIG['max_scroll_attempts']

    while scroll_attempts < max_attempts:
        # Scroll down to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pause_time)

        # Get new height
        new_height = page.evaluate("document.body.scrollHeight")

        # If height hasn't changed, we've reached the bottom
        if new_height == last_height:
            break

        last_height = new_height
        scroll_attempts += 1

    # Scroll back to top
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.3)


def close_popups_and_modals(page):
    """Close popups, modals, and banners that may be blocking the page.

    Attempts to find and click various close buttons using selectors from
    the configuration. Silently continues if no popups are found.

    Parameters
    ----------
    page : Page
        Playwright page object
    """
    for selector in SELECTORS['popup_closers']:
        try:
            button = page.locator(selector).first
            if button.is_visible(timeout=BROWSER_CONFIG['timeout_popup']):
                button.click()
                print(f"   ✓ Popup/modal closed with: {selector}")
                time.sleep(0.5)
        except Exception:
            continue


def go_to_next_page(page) -> bool:
    """Find and click the 'Next' button to navigate to the next page.

    Tries multiple selector strategies to find the pagination next button.
    Verifies the button is not disabled before clicking.

    Parameters
    ----------
    page : Page
        Playwright page object

    Returns
    -------
    bool
        True if successfully navigated to next page, False otherwise
    """
    for selector in SELECTORS['next_button']:
        try:
            next_button = page.locator(selector).first
            if next_button.is_visible(timeout=BROWSER_CONFIG['timeout_button']):
                # Check if button is disabled
                is_disabled = next_button.evaluate('''(el) => {
                    const parent = el.closest('li');
                    return el.classList.contains('disabled') ||
                           el.getAttribute('aria-disabled') === 'true' ||
                           el.hasAttribute('disabled') ||
                           (parent && (parent.classList.contains('disabled') ||
                                      parent.classList.contains('andes-pagination__button--disabled')));
                }''')

                if not is_disabled:
                    print(f"   ✓ Button found with selector: {selector}")
                    # Scroll to button if needed
                    next_button.scroll_into_view_if_needed()
                    time.sleep(BROWSER_CONFIG['click_wait'])
                    # Click and wait for page load
                    next_button.click()
                    page.wait_for_load_state('domcontentloaded', timeout=10000)
                    return True
                else:
                    print(f"   ⚠️ Button found but is disabled (last page)")
        except Exception:
            continue

    return False
