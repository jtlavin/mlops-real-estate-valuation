"""Utility functions for file I/O and URL building."""

import os
import pandas as pd
from typing import List
from .config import URL_TEMPLATES
from .models import Property


def normalize_comuna_name(comuna: str) -> str:
    """Normalize comuna name to URL-friendly format.

    Converts comuna names to lowercase and replaces spaces with hyphens.

    Parameters
    ----------
    comuna : str
        Comuna name (e.g., "Las Condes", "Providencia")

    Returns
    -------
    str
        Normalized comuna name (e.g., "las-condes", "providencia")

    Examples
    --------
    >>> normalize_comuna_name("Las Condes")
    'las-condes'
    >>> normalize_comuna_name("SANTIAGO")
    'santiago'
    """
    return comuna.strip().lower().replace(' ', '-')


def build_search_url(comuna: str, property_type: str = "departamento") -> str:
    """Build search URL for Portal Inmobiliario.

    Constructs the URL following the pattern:
    https://www.portalinmobiliario.com/venta/{property_type}/{comuna}-metropolitana

    Parameters
    ----------
    comuna : str
        Comuna name (will be normalized)
    property_type : str, optional
        Type of property: "departamento" or "casa" (default: "departamento")

    Returns
    -------
    str
        Full search URL

    Examples
    --------
    >>> build_search_url("las-condes")
    'https://www.portalinmobiliario.com/venta/departamento/las-condes-metropolitana'
    >>> build_search_url("providencia", "casa")
    'https://www.portalinmobiliario.com/venta/casa/providencia-metropolitana'
    """
    normalized_comuna = normalize_comuna_name(comuna)
    return URL_TEMPLATES['search'].format(
        property_type=property_type,
        comuna=normalized_comuna
    )


def save_to_csv(properties: List[Property], filepath: str = 'data/property_basic_info.csv'):
    """Save property information to a CSV file.

    Creates the output directory if it doesn't exist. Converts Property objects
    to dictionaries and saves them using pandas.

    Parameters
    ----------
    properties : List[Property]
        List of Property objects to save
    filepath : str, optional
        Path to output CSV file (default: 'data/property_basic_info.csv')

    Raises
    ------
    Exception
        If there's an error creating directory or writing file
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Convert Property objects to dictionaries
        property_dicts = [prop.to_dict() for prop in properties]

        # Create DataFrame
        df = pd.DataFrame(property_dicts)

        # Reorder columns
        columns_order = ['url', 'dormitorios', 'banos', 'superficie', 'ubicacion']
        df = df[columns_order]

        # Save to CSV
        df.to_csv(filepath, index=False, encoding='utf-8')

        print(f"💾 Data saved to CSV: {filepath}")
        print(f"   Columns: {', '.join(df.columns.tolist())}")
        print(f"   Total rows: {len(df)}")

    except Exception as e:
        print(f"⚠️ Error saving CSV: {e}")


def save_urls_to_file(urls: List[str], filepath: str = 'data/property_urls.txt'):
    """Save property URLs to a text file (one per line).

    Creates the output directory if it doesn't exist.

    Parameters
    ----------
    urls : List[str]
        List of property URLs to save
    filepath : str, optional
        Path to output text file (default: 'data/property_urls.txt')

    Raises
    ------
    Exception
        If there's an error creating directory or writing file
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")

        print(f"💾 URLs saved to: {filepath}")

    except Exception as e:
        print(f"⚠️ Error saving file: {e}")
