"""Property information extraction from Portal Inmobiliario pages."""

import re
from typing import List, Optional, Dict
from .config import SELECTORS, EXTRACTION_CONFIG
from .models import Property


class PropertyExtractor:
    """Extracts property data from Portal Inmobiliario listing pages.

    This class handles the extraction of individual property information from
    the HTML page, including filtering out projects and multi-unit listings.
    """

    def __init__(self):
        """Initialize the property extractor."""
        self.seen_urls = set()

    def extract_properties(self, page) -> List[Property]:
        """Extract all valid properties from the current page.

        Filters out:
        - Properties marked as "PROYECTO" (projects)
        - Properties with "X unidades disponibles" (multiple units available)

        Extracts:
        - URL
        - Number of bedrooms (dormitorios)
        - Number of bathrooms (baños)
        - Surface area (superficie in m²)
        - Location (ubicación)

        Parameters
        ----------
        page : Page
            Playwright page object

        Returns
        -------
        List[Property]
            List of valid Property objects found on the page
        """
        properties = []

        # Find property article elements
        articles = self._find_articles(page)
        if not articles:
            print("   ⚠️ No property articles found")
            return properties

        # Track extraction statistics
        total_analyzed = 0
        skipped_proyecto = 0
        skipped_unidades = 0
        added = 0

        for article in articles:
            total_analyzed += 1

            try:
                # Get article HTML content
                html_content = article.inner_html()

                # Filter out projects
                if self._is_project(html_content):
                    skipped_proyecto += 1
                    continue

                # Filter out multi-unit properties
                if self._is_multi_unit(html_content):
                    skipped_unidades += 1
                    continue

                # Extract property URL
                url = self._extract_url(article)
                if not url:
                    continue

                # Extract property attributes
                attributes = self._extract_attributes(article)

                # Extract location
                location = self._extract_location(article)

                # Create Property object
                property_obj = Property(
                    url=url,
                    dormitorios=attributes.get('dormitorios'),
                    banos=attributes.get('banos'),
                    superficie=attributes.get('superficie'),
                    ubicacion=location
                )

                properties.append(property_obj)
                added += 1

            except Exception:
                continue

        # Print extraction statistics
        print(f"   📊 Analysis: {total_analyzed} articles | "
              f"Projects: {skipped_proyecto} | "
              f"Multi-unit: {skipped_unidades} | "
              f"✓ Valid: {added}")

        return properties

    def _find_articles(self, page):
        """Find property article elements using selector strategies.

        Tries multiple selectors in order and returns the first one that finds
        a sufficient number of articles.

        Parameters
        ----------
        page : Page
            Playwright page object

        Returns
        -------
        list or None
            List of article elements, or None if not found
        """
        for selector in SELECTORS['article_candidates']:
            try:
                found = page.locator(selector).all()
                if found and len(found) >= EXTRACTION_CONFIG['min_articles_threshold']:
                    print(f"   Using selector: {selector} ({len(found)} elements)")
                    return found
            except Exception:
                continue
        return None

    def _is_project(self, html_content: str) -> bool:
        """Check if property is marked as a project (has PROYECTO tag).

        Parameters
        ----------
        html_content : str
            Inner HTML of the property article

        Returns
        -------
        bool
            True if property is a project
        """
        markers = SELECTORS['project_markers']
        return (markers['pill_class'] in html_content and
                markers['pill_text'] in html_content.upper())

    def _is_multi_unit(self, html_content: str) -> bool:
        """Check if property has multiple units available.

        Parameters
        ----------
        html_content : str
            Inner HTML of the property article

        Returns
        -------
        bool
            True if property has multiple units
        """
        markers = SELECTORS['project_markers']
        return (markers['available_units'] in html_content or
                markers['available_units_text'] in html_content.lower())

    def _extract_url(self, article) -> Optional[str]:
        """Extract property URL from article element.

        Looks for links containing "/MLC-" and builds the full URL.
        Deduplicates URLs using the seen_urls set.

        Parameters
        ----------
        article : Locator
            Playwright locator for the article element

        Returns
        -------
        Optional[str]
            Full property URL, or None if not found or duplicate
        """
        links = article.locator(SELECTORS['property_link']).all()

        for link in links:
            try:
                href = link.get_attribute('href')
                if not href:
                    continue

                # Build full URL
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = f"https://www.portalinmobiliario.com{href}"
                else:
                    full_url = f"https://www.portalinmobiliario.com/{href}"

                # Avoid duplicates
                if full_url not in self.seen_urls:
                    self.seen_urls.add(full_url)
                    return full_url

            except Exception:
                continue

        return None

    def _extract_attributes(self, article) -> Dict[str, Optional[str]]:
        """Extract property attributes (bedrooms, bathrooms, surface area).

        Parameters
        ----------
        article : Locator
            Playwright locator for the article element

        Returns
        -------
        Dict[str, Optional[str]]
            Dictionary with 'dormitorios', 'banos', and 'superficie' keys
        """
        attributes = {
            'dormitorios': None,
            'banos': None,
            'superficie': None
        }

        try:
            attribute_elements = article.locator(SELECTORS['attributes_list']).all()
            for attr in attribute_elements:
                text = attr.inner_text().strip()

                # Extract number of bedrooms
                if 'dormitorio' in text.lower():
                    match = re.search(r'(\d+)', text)
                    if match:
                        attributes['dormitorios'] = match.group(1)

                # Extract number of bathrooms
                elif 'baño' in text.lower():
                    match = re.search(r'(\d+)', text)
                    if match:
                        attributes['banos'] = match.group(1)

                # Extract surface area
                elif 'm²' in text or 'm2' in text.lower():
                    match = re.search(r'(\d+(?:\.\d+)?)\s*m', text)
                    if match:
                        attributes['superficie'] = f"{match.group(1)} m²"

        except Exception:
            pass

        return attributes

    def _extract_location(self, article) -> Optional[str]:
        """Extract location/address from article element.

        Parameters
        ----------
        article : Locator
            Playwright locator for the article element

        Returns
        -------
        Optional[str]
            Location string, or None if not found
        """
        try:
            location_elem = article.locator(SELECTORS['location']).first
            if location_elem.is_visible():
                return location_elem.inner_text().strip()
        except Exception:
            pass

        return None
