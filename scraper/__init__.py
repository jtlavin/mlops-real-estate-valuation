"""Portal Inmobiliario property scraper.

This package provides a simple, parameterizable API for scraping real estate
property listings from Portal Inmobiliario (Chile).

Example usage:
    >>> from scraper import scrape_properties
    >>> properties = scrape_properties("las-condes", max_pages=3)
    >>> print(f"Found {len(properties)} properties")
"""

from typing import List, Union
import pandas as pd
from .models import Property
from .scraper import PortalInmobiliarioScraper
from .utils import save_to_csv, save_urls_to_file
from .config import OUTPUT_FILES

__version__ = "1.0.0"
__all__ = ['scrape_properties', 'Property']


def scrape_properties(
    comuna: str,
    max_pages: int = 3,
    property_type: str = "departamento",
    headless: bool = True,
    output_dir: str = "data",
    save_csv: bool = True,
    save_urls: bool = True,
    return_dataframe: bool = False
) -> Union[List[Property], pd.DataFrame]:
    """Scrape real estate properties from Portal Inmobiliario.

    This is the main entry point for the scraper. It navigates through
    property listings for a specified comuna (district) in Santiago, Chile,
    and extracts property information.

    The scraper automatically:
    - Scrolls pages to load lazy-loaded content
    - Filters out projects and multi-unit listings
    - Extracts bedrooms, bathrooms, surface area, and location
    - Handles pagination to scrape multiple pages
    - Saves results to CSV and/or text files

    Parameters
    ----------
    comuna : str
        Comuna name (e.g., "las-condes", "providencia", "santiago").
        Can include spaces and mixed case - will be normalized automatically.
    max_pages : int, optional
        Maximum number of pages to scrape (default: 3).
        Each page typically contains 40-50 properties.
    property_type : str, optional
        Type of property to search for (default: "departamento").
        Options: "departamento" (apartment) or "casa" (house).
    headless : bool, optional
        Run browser in headless mode (default: True).
        Set to False to see the browser in action (useful for debugging).
    output_dir : str, optional
        Directory to save output files (default: "data").
        Will be created if it doesn't exist.
    save_csv : bool, optional
        Save properties to CSV file (default: True).
        File: {output_dir}/property_basic_info.csv
    save_urls : bool, optional
        Save property URLs to text file (default: True).
        File: {output_dir}/property_urls.txt
    return_dataframe : bool, optional
        Return pandas DataFrame instead of list (default: False).
        If False, returns List[Property].

    Returns
    -------
    Union[List[Property], pd.DataFrame]
        If return_dataframe=False: List of Property objects
        If return_dataframe=True: pandas DataFrame with property data

    Raises
    ------
    ValueError
        If comuna parameter is empty or invalid

    Examples
    --------
    Basic usage:
    >>> properties = scrape_properties("las-condes", max_pages=3)
    >>> print(f"Found {len(properties)} properties")

    Change location:
    >>> properties = scrape_properties("providencia", max_pages=5)

    Get DataFrame for analysis:
    >>> df = scrape_properties("santiago", max_pages=3, return_dataframe=True)
    >>> print(df[['dormitorios', 'banos', 'superficie']].describe())

    Debug mode (visible browser):
    >>> properties = scrape_properties("nunoa", max_pages=1, headless=False)

    Scrape houses instead of apartments:
    >>> properties = scrape_properties("vitacura", property_type="casa")

    Only get data without saving files:
    >>> properties = scrape_properties("las-condes", save_csv=False, save_urls=False)

    Notes
    -----
    - Property attribute names (dormitorios, banos, ubicacion) are kept in
      Spanish to match the source website
    - The scraper respects the website's structure and applies reasonable delays
    - Projects and multi-unit listings are automatically filtered out
    - Duplicate URLs are automatically removed
    """
    # Validate parameters
    if not comuna or not comuna.strip():
        raise ValueError("comuna parameter cannot be empty")

    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")

    if property_type not in ["departamento", "casa"]:
        raise ValueError("property_type must be 'departamento' or 'casa'")

    # Execute scraping
    scraper = PortalInmobiliarioScraper(comuna, property_type, headless)
    properties = scraper.scrape(max_pages)

    # Save outputs if requested
    if properties:
        if save_csv:
            filepath = f"{output_dir}/{OUTPUT_FILES['csv']}"
            save_to_csv(properties, filepath)

        if save_urls:
            urls = [p.url for p in properties]
            filepath = f"{output_dir}/{OUTPUT_FILES['urls']}"
            save_urls_to_file(urls, filepath)

    # Return in requested format
    if return_dataframe:
        return pd.DataFrame([p.to_dict() for p in properties])

    return properties
