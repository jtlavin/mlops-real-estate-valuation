"""Main scraper orchestration for Portal Inmobiliario."""

import time
from typing import List
from playwright.sync_api import sync_playwright
from .config import BROWSER_CONFIG, SELECTORS
from .models import Property
from .extractors import PropertyExtractor
from .browser import scroll_to_bottom, close_popups_and_modals, go_to_next_page
from .utils import normalize_comuna_name, build_search_url


class PortalInmobiliarioScraper:
    """Orchestrates the scraping of Portal Inmobiliario property listings.

    This class manages the browser automation, page navigation, and property
    extraction process for a specific comuna and property type.

    Attributes
    ----------
    comuna : str
        Normalized comuna name (e.g., "las-condes")
    property_type : str
        Type of property: "departamento" or "casa"
    url : str
        Full search URL for the specified comuna and property type
    headless : bool
        Whether to run browser in headless mode
    browser : Browser
        Playwright browser instance (initialized during scraping)
    page : Page
        Playwright page instance (initialized during scraping)
    extractor : PropertyExtractor
        Property extraction handler
    """

    def __init__(self, comuna: str, property_type: str = "departamento", headless: bool = True):
        """Initialize the scraper for a specific comuna.

        Parameters
        ----------
        comuna : str
            Comuna name (e.g., "las-condes", "providencia")
        property_type : str, optional
            Type of property: "departamento" or "casa" (default: "departamento")
        headless : bool, optional
            Run browser in headless mode (default: True)
        """
        self.comuna = normalize_comuna_name(comuna)
        self.property_type = property_type
        self.url = build_search_url(self.comuna, property_type)
        self.headless = headless
        self.browser = None
        self.page = None
        self.extractor = PropertyExtractor()

    def scrape(self, max_pages: int) -> List[Property]:
        """Execute the scraping process.

        Navigates through pages, extracts property information, and returns
        all collected properties. Automatically handles browser cleanup.

        Parameters
        ----------
        max_pages : int
            Maximum number of pages to scrape

        Returns
        -------
        List[Property]
            List of all extracted Property objects

        Raises
        ------
        Exception
            If there's an error during scraping (logged and returns empty list)
        """
        try:
            self._setup_browser()
            return self._scrape_pages(max_pages)
        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self._cleanup()

    def _setup_browser(self):
        """Initialize Playwright browser and navigate to first page.

        Sets up the browser context with user agent and loads the initial
        search page. Also closes any popups that may appear.
        """
        print(f"\n{'='*60}")
        print(f"Starting scraper for: {self.url}")
        print(f"{'='*60}\n")

        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=self.headless)
        context = self.browser.new_context(
            user_agent=BROWSER_CONFIG['user_agent']
        )
        self.page = context.new_page()

        # Navigate to first page
        print("📄 Loading page...")
        self.page.goto(
            self.url,
            wait_until='domcontentloaded',
            timeout=BROWSER_CONFIG['timeout_default']
        )
        time.sleep(BROWSER_CONFIG['page_load_wait'])

        # Close any initial popups
        close_popups_and_modals(self.page)

    def _scrape_pages(self, max_pages: int) -> List[Property]:
        """Iterate through pages and collect all properties.

        Parameters
        ----------
        max_pages : int
            Maximum number of pages to scrape

        Returns
        -------
        List[Property]
            All collected Property objects from all pages
        """
        all_properties = []
        current_page = 1

        for page_num in range(1, max_pages + 1):
            current_page = page_num
            print(f"\n{'─'*60}")
            print(f"PAGE {page_num}")
            print(f"{'─'*60}")

            # Process current page
            page_properties = self._process_single_page()
            all_properties.extend(page_properties)

            print(f"✓ Valid properties found on this page: {len(page_properties)}")
            print(f"✓ Total accumulated: {len(all_properties)}\n")

            # Navigate to next page if not last
            if page_num < max_pages:
                if not self._navigate_to_next_page():
                    print("⚠️ Next button not found or last page reached")
                    break

        # Print final summary
        self._print_summary(all_properties, current_page)

        return all_properties

    def _process_single_page(self) -> List[Property]:
        """Process the current page: scroll, extract, and return properties.

        Returns
        -------
        List[Property]
            Properties extracted from the current page
        """
        # Scroll to load all lazy-loaded content
        print("📜 Scrolling to bottom...")
        scroll_to_bottom(self.page)
        print("✓ Scroll completed\n")

        # Extract property information
        print("📊 Extracting property information...")
        properties = self.extractor.extract_properties(self.page)

        return properties

    def _navigate_to_next_page(self) -> bool:
        """Navigate to the next page of results.

        Returns
        -------
        bool
            True if successfully navigated, False otherwise
        """
        print("🔄 Looking for 'Next' button...")

        # Close any popups that may have appeared
        close_popups_and_modals(self.page)

        # Find and scroll to pagination
        print("   Looking for pagination on the page...")
        try:
            # Try to find pagination container
            for selector in SELECTORS['pagination_container']:
                try:
                    pagination = self.page.locator(selector).first
                    if pagination.is_visible(timeout=2000):
                        pagination.scroll_into_view_if_needed()
                        print("   ✓ Pagination found and visible")
                        time.sleep(BROWSER_CONFIG['pagination_wait'])
                        break
                except Exception:
                    continue
            else:
                # If pagination not found, scroll up a bit
                print("   Scrolling up...")
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight - 1500)")
                time.sleep(BROWSER_CONFIG['pagination_wait'])
        except Exception:
            pass

        # Try to click next button
        if go_to_next_page(self.page):
            print("✓ Navigated to next page\n")
            time.sleep(BROWSER_CONFIG['after_navigation_wait'])
            return True

        return False

    def _print_summary(self, properties: List[Property], pages_processed: int):
        """Print extraction summary and sample properties.

        Parameters
        ----------
        properties : List[Property]
            All extracted properties
        pages_processed : int
            Number of pages that were processed
        """
        print(f"\n{'='*60}")
        print("✅ Scraping completed!")
        print(f"{'='*60}\n")

        print(f"📋 EXTRACTION SUMMARY:")
        print(f"   Total properties found: {len(properties)}")
        print(f"   Pages processed: {pages_processed}\n")

        # Show first few properties as examples
        if properties:
            print("📊 First properties extracted (sample):")
            for i, prop in enumerate(properties[:5], 1):
                ubicacion = prop.ubicacion or 'N/A'
                ubicacion_short = ubicacion[:50] if len(ubicacion) > 50 else ubicacion
                print(f"   {i}. {prop.dormitorios or 'N/A'} bedrooms | "
                      f"{prop.banos or 'N/A'} bathrooms | "
                      f"{prop.superficie or 'N/A'} | "
                      f"{ubicacion_short}...")
            if len(properties) > 5:
                print(f"   ... and {len(properties) - 5} more\n")
            else:
                print()

    def _cleanup(self):
        """Close browser and clean up resources."""
        if self.browser:
            self.browser.close()
