from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

import s2sphere


class ExternalDataError(Exception):
    """Base class for errors related to external data fetching or processing."""

    pass


class ExternalDataConnectionError(ExternalDataError):
    """Raised when there's an issue connecting to or fetching data from the external source."""

    def __init__(self, source_url: str, original_exception: Optional[Exception] = None):
        self.source_url = source_url
        self.original_exception = original_exception
        super().__init__(
            f"Connection or fetch error for external data source: {source_url}"
            + (f" (Original error: {original_exception})" if original_exception else "")
        )


class ExternalDataParsingError(ExternalDataError):
    """Raised when the fetched external data cannot be parsed or does not match expected format."""

    def __init__(self, source_url: str, message: str, original_exception: Optional[Exception] = None):
        self.source_url = source_url
        self.message = message
        self.original_exception = original_exception
        super().__init__(
            f"Parsing error for external data source: {source_url}. Message: {message}"
            + (f" (Original error: {original_exception})" if original_exception else "")
        )


class ExternalGeoClient(ABC):
    """
    Abstract base class for clients that fetch and process geospatial data
    from external sources.
    """

    @abstractmethod
    def get_raw_features(
        self, source_url: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetches raw geospatial features from the specified source URL.

        Args:
            source_url: The URL from which to fetch the GeoJSON data.
            params: Optional dictionary of parameters to include in the request
                    (e.g., for interpretation rules if the server supports them).

        Returns:
            A dictionary representing the GeoJSON FeatureCollection.

        Raises:
            ExternalDataConnectionError: If there's an issue fetching data from the source.
            ExternalDataParsingError: If the fetched data is not valid GeoJSON or
                                     cannot be parsed as expected.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_test_points(
        self, source_url: str, params: Optional[Dict[str, Any]] = None
    ) -> List[s2sphere.LatLng]:
        """
        Fetches geospatial features from the source URL and computes their centroids
        to be used as test points.

        Args:
            source_url: The URL from which to fetch the GeoJSON data.
            params: Optional dictionary of parameters (e.g., interpretation_rule).
                    The primary interpretation rule used by this method is to
                    treat all valid geometries as areas/points for which centroids
                    are to be calculated.

        Returns:
            A list of s2sphere.LatLng objects representing the centroids.

        Raises:
            ExternalDataConnectionError: If there's an issue fetching data from the source.
            ExternalDataParsingError: If the fetched data is not valid GeoJSON,
                                     if the GeoJSON structure is not a FeatureCollection,
                                     or if features cannot be processed.
        """
        raise NotImplementedError()
