"""Data models for real estate properties."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Property:
    """Represents a real estate property listing from Portal Inmobiliario.

    Attributes
    ----------
    url : str
        Full URL to the property listing page
    dormitorios : Optional[int]
        Number of bedrooms (dormitorios in Spanish)
    banos : Optional[int]
        Number of bathrooms (baños in Spanish)
    superficie : Optional[str]
        Surface area with unit (e.g., "120 m²")
    ubicacion : Optional[str]
        Location/address of the property (ubicación in Spanish)
    """

    url: str
    dormitorios: Optional[int] = None
    banos: Optional[int] = None
    superficie: Optional[str] = None
    ubicacion: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert property to dictionary format for CSV export.

        Returns
        -------
        dict
            Dictionary with property attributes
        """
        return {
            'url': self.url,
            'dormitorios': self.dormitorios,
            'banos': self.banos,
            'superficie': self.superficie,
            'ubicacion': self.ubicacion,
        }
