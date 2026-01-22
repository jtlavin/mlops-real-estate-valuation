# MLOps Real Estate Valuation

A modular, production-ready web scraper for real estate property listings from [Portal Inmobiliario](https://www.portalinmobiliario.com) (Chile). Designed for MLOps pipelines with parameterizable location and pagination.

## Features

- **Parameterizable API**: Easily scrape different comunas (districts) and control page count
- **Modular Architecture**: Clean separation of concerns across 7 focused modules
- **Type-Safe**: Uses dataclasses and type hints throughout
- **Flexible Output**: Return as list of objects or pandas DataFrame
- **Smart Filtering**: Automatically excludes projects and multi-unit listings
- **Production-Ready**: Comprehensive error handling and logging
- **Well-Documented**: Full docstrings in English with examples

## Installation

```bash
# Clone the repository
git clone https://github.com/jtlavin/mlops-real-estate-valuation.git
cd mlops-real-estate-valuation

# Install dependencies (using uv)
uv sync

# Or using pip
pip install -e .
```

## Quick Start

### Basic Usage

```python
from scraper import scrape_properties

# Scrape Las Condes apartments (3 pages)
properties = scrape_properties("las-condes", max_pages=3)
print(f"Found {len(properties)} properties")

# Access property data
for prop in properties[:5]:
    print(f"{prop.dormitorios} bedrooms, {prop.banos} bathrooms")
    print(f"Surface: {prop.superficie}")
    print(f"Location: {prop.ubicacion}")
    print(f"URL: {prop.url}")
    print("-" * 40)
```

### Change Location

```python
# Scrape different comunas
properties = scrape_properties("providencia", max_pages=5)
properties = scrape_properties("santiago", max_pages=2)
properties = scrape_properties("vitacura", max_pages=3)

# Scrape multiple locations
comunas = ["las-condes", "providencia", "vitacura"]
all_properties = []
for comuna in comunas:
    props = scrape_properties(comuna, max_pages=2)
    all_properties.extend(props)
    print(f"{comuna}: {len(props)} properties")
```

### Get DataFrame for Analysis

```python
import pandas as pd
from scraper import scrape_properties

# Return as DataFrame
df = scrape_properties("las-condes", max_pages=3, return_dataframe=True)

# Analyze the data
print(df.describe())
print(df[['dormitorios', 'banos']].value_counts())

# Filter properties
luxury = df[df['dormitorios'] >= 3]
print(f"Found {len(luxury)} luxury properties")
```

### Debug Mode

```python
# Run with visible browser for debugging
properties = scrape_properties("nunoa", max_pages=1, headless=False)
```

### Scrape Houses Instead of Apartments

```python
# Change property type to "casa" (house)
properties = scrape_properties("vitacura", property_type="casa", max_pages=2)
```

### Control File Saving

```python
# Only get data without saving files
properties = scrape_properties(
    "las-condes",
    max_pages=3,
    save_csv=False,
    save_urls=False
)

# Save to custom directory
properties = scrape_properties(
    "providencia",
    max_pages=2,
    output_dir="output/scraped_data"
)
```

## API Reference

### `scrape_properties()`

Main function to scrape property listings.

```python
def scrape_properties(
    comuna: str,                    # Required: comuna name
    max_pages: int = 3,             # Number of pages to scrape
    property_type: str = "departamento",  # "departamento" or "casa"
    headless: bool = True,          # Run browser in headless mode
    output_dir: str = "data",       # Output directory
    save_csv: bool = True,          # Save CSV file
    save_urls: bool = True,         # Save URLs text file
    return_dataframe: bool = False  # Return DataFrame vs List[Property]
) -> Union[List[Property], pd.DataFrame]
```

**Parameters:**
- `comuna`: Comuna name (e.g., "las-condes", "providencia"). Spaces and mixed case are normalized automatically.
- `max_pages`: Maximum number of pages to scrape. Each page has ~40-50 properties.
- `property_type`: Type of property - "departamento" (apartment) or "casa" (house).
- `headless`: Run browser in headless mode. Set False to see browser (useful for debugging).
- `output_dir`: Directory to save output files. Created if it doesn't exist.
- `save_csv`: Save properties to `{output_dir}/property_basic_info.csv`.
- `save_urls`: Save URLs to `{output_dir}/property_urls.txt`.
- `return_dataframe`: Return pandas DataFrame instead of list.

**Returns:**
- `List[Property]` if `return_dataframe=False`
- `pd.DataFrame` if `return_dataframe=True`

### Property Object

```python
@dataclass
class Property:
    url: str                        # Full URL to property listing
    dormitorios: Optional[int]      # Number of bedrooms
    banos: Optional[int]            # Number of bathrooms
    superficie: Optional[str]       # Surface area (e.g., "120 m²")
    ubicacion: Optional[str]        # Location/address
```

## Project Structure

```
mlops-real-estate-valuation/
├── scraper/                    # Main package
│   ├── __init__.py            # Public API: scrape_properties()
│   ├── config.py              # Configuration constants
│   ├── models.py              # Property dataclass
│   ├── scraper.py             # PortalInmobiliarioScraper class
│   ├── extractors.py          # PropertyExtractor class
│   ├── browser.py             # Browser automation utilities
│   └── utils.py               # File I/O and URL builders
├── scraper_simple.py          # Original implementation (reference)
├── test_scraper.py            # Test/verification script
├── data/                      # Output directory
│   ├── property_basic_info.csv
│   └── property_urls.txt
├── pyproject.toml             # Project dependencies
└── README.md                  # This file
```

## Module Overview

### `scraper/__init__.py`
Public API with the main `scrape_properties()` function. This is the only module users need to import.

### `scraper/config.py`
Configuration constants including:
- Browser settings (timeouts, user agent, delays)
- CSS selectors for page elements
- URL templates
- Extraction settings

### `scraper/models.py`
`Property` dataclass representing a real estate listing with type hints and conversion methods.

### `scraper/scraper.py`
`PortalInmobiliarioScraper` class that orchestrates:
- Browser initialization
- Page navigation
- Multi-page scraping
- Result aggregation

### `scraper/extractors.py`
`PropertyExtractor` class that handles:
- Finding property elements
- Filtering projects/multi-unit listings
- Extracting attributes (bedrooms, bathrooms, etc.)
- URL deduplication

### `scraper/browser.py`
Browser automation utilities:
- `scroll_to_bottom()`: Load lazy-loaded content
- `close_popups_and_modals()`: Handle popups
- `go_to_next_page()`: Navigate pagination

### `scraper/utils.py`
Utility functions:
- `build_search_url()`: Construct search URLs
- `normalize_comuna_name()`: Format comuna names
- `save_to_csv()`: Export to CSV
- `save_urls_to_file()`: Export URLs

## Running Tests

```bash
# Run the test script
python test_scraper.py

# Or run individual tests by uncommenting them in test_scraper.py
```

## Output Files

By default, the scraper saves two files:

1. **property_basic_info.csv**: Property data in CSV format
   ```csv
   url,dormitorios,banos,superficie,ubicacion
   https://...,3,2,120 m²,Las Condes
   ```

2. **property_urls.txt**: One URL per line
   ```
   https://www.portalinmobiliario.com/MLC-...
   https://www.portalinmobiliario.com/MLC-...
   ```

## Technical Details

### Filtering Logic

The scraper automatically filters out:
- Properties marked as "PROYECTO" (development projects)
- Properties with "X unidades disponibles" (multiple units available)

This ensures you get individual property listings only.

### Extracted Attributes

For each property, the scraper extracts:
- URL (required)
- Number of bedrooms (dormitorios)
- Number of bathrooms (baños)
- Surface area (superficie in m²)
- Location (ubicación)

Attribute names are kept in Spanish to match the source website.

### Pagination Strategy

1. Loads page and scrolls to bottom (loads lazy content)
2. Extracts all visible properties
3. Scrolls to pagination section
4. Clicks "Next" button if available
5. Repeats until max_pages reached or no more pages

### Error Handling

- Graceful degradation: continues on individual property errors
- Browser cleanup in finally blocks
- Detailed error messages and stack traces
- Validates input parameters

## Dependencies

- **playwright**: Browser automation
- **pandas**: Data manipulation and CSV export
- **Python 3.8+**: Modern Python features

See `pyproject.toml` for full dependency list.

## Migration from Old Code

### Before (scraper_simple.py)
```python
if __name__ == "__main__":
    url = "https://www.portalinmobiliario.com/venta/departamento/las-condes-metropolitana"
    scrape_portal_inmobiliario(url, max_pages=3, headless=False)
```

### After (new API)
```python
from scraper import scrape_properties
properties = scrape_properties("las-condes", max_pages=3)
```

The old `scraper_simple.py` is kept as reference but the new API is recommended for all use cases.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with Claude Code for automated refactoring and documentation generation.
