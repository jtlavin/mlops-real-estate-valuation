"""Configuration constants for Portal Inmobiliario scraper."""

# Browser settings
BROWSER_CONFIG = {
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'timeout_default': 30000,  # milliseconds
    'timeout_button': 3000,    # milliseconds for finding buttons
    'timeout_popup': 1000,     # milliseconds for popup detection
    'page_load_wait': 2.0,     # seconds to wait after page load
    'scroll_pause': 0.5,       # seconds between scroll attempts
    'pagination_wait': 0.5,    # seconds after scrolling to pagination
    'click_wait': 0.3,         # seconds before clicking next button
    'after_navigation_wait': 2.0,  # seconds after clicking next page
}

# CSS Selectors (grouped by purpose)
SELECTORS = {
    # Property article/card selectors (tried in order)
    'article_candidates': [
        'article',
        'li[class*="ui-search-layout__item"]',
        'div[class*="ui-search-result"]',
        '.poly-card'
    ],

    # Property link selector
    'property_link': 'a[href*="/MLC-"]',

    # Property attributes
    'attributes_list': '.poly-attributes_list__item',
    'location': '.poly-component__location',

    # Pagination selectors (tried in order)
    'next_button': [
        '.andes-pagination__button--next a',
        'li.andes-pagination__button--next a',
        'a.andes-pagination__link[aria-label*="iguiente"]',
        'a:has-text("Siguiente")',
        'button:has-text("Siguiente")',
        'a[title*="iguiente"]',
        'a[aria-label*="iguiente"]',
        '.ui-search-pagination a[aria-label*="Siguiente"]',
    ],

    # Pagination container selectors
    'pagination_container': [
        '.andes-pagination',
        'nav[aria-label*="pagination"]',
        'nav[aria-label*="Paginación"]'
    ],

    # Popup/modal close button selectors
    'popup_closers': [
        'button:has-text("Entendido")',
        'button:has-text("Aceptar")',
        'button:has-text("Acepto")',
        'button[aria-label="Cerrar"]',
        'button[aria-label="Close"]',
        '[class*="close-button"]',
        '[class*="modal"] button:has-text("×")',
        '.ad-banner button',
        '[class*="banner"] button[class*="close"]',
    ],

    # Project/multi-unit markers (used for filtering)
    'project_markers': {
        'pill_class': 'poly-pill__pill',
        'pill_text': 'PROYECTO',
        'available_units': 'poly-component__available-units',
        'available_units_text': 'unidades disponibles',
    }
}

# URL patterns
URL_TEMPLATES = {
    'base': 'https://www.portalinmobiliario.com',
    'search': 'https://www.portalinmobiliario.com/venta/{property_type}/{comuna}-metropolitana',
}

# Output files
OUTPUT_FILES = {
    'csv': 'property_basic_info.csv',
    'urls': 'property_urls.txt',
}

# Extraction settings
EXTRACTION_CONFIG = {
    'max_scroll_attempts': 10,  # Maximum number of scroll attempts
    'min_articles_threshold': 5,  # Minimum articles needed to consider selector valid
}
