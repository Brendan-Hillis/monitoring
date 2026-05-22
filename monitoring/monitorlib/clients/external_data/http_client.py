from typing import List, Optional, Dict, Any
import requests
import s2sphere
import geojson # type: ignore[import-untyped] # geojson is untyped
from shapely.geometry import shape, Point # type: ignore[import-untyped] # shapely is untyped

from .client import (
    ExternalGeoClient,
    ExternalDataConnectionError,
    ExternalDataParsingError,
)


class HttpGeoSourceClient(ExternalGeoClient):
    """
    Client for fetching and processing geospatial data from generic HTTP GeoJSON sources.
    """

    _session: requests.Session

    def __init__(self, session: Optional[requests.Session] = None):
        """
        Initializes the client.

        Args:
            session: A requests.Session to use for HTTP calls. If None, a new session is created.
        """
        self._session = session or requests.Session()

    def get_raw_features(
        self, source_url: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetches raw geospatial features from the specified source URL.
        `params` is currently not used for the GET request itself but included for API consistency.
        """
        try:
            response = self._session.get(source_url, params=params) # `params` here are URL query parameters
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        except requests.exceptions.RequestException as e:
            raise ExternalDataConnectionError(source_url=source_url, original_exception=e)

        try:
            return response.json()
        except ValueError as e: # Includes JSONDecodeError
            raise ExternalDataParsingError(
                source_url=source_url,
                message="Failed to decode JSON response",
                original_exception=e,
            )

    def get_test_points(
        self, source_url: str, params: Optional[Dict[str, Any]] = None
    ) -> List[s2sphere.LatLng]:
        """
        Fetches features from a dynamic GeoJSON source and computes their centroids.
        `params` can include 'interpretation_rule', though currently defaults to 'treat_all_as_restrictions'.
        """
        try:
            geojson_data = self.get_raw_features(source_url, params)
        except ExternalDataError as e: # Propagate errors from get_raw_features
            raise e

        if not isinstance(geojson_data, dict):
            raise ExternalDataParsingError(
                source_url=source_url,
                message=f"Expected GeoJSON data to be a dictionary, got {type(geojson_data).__name__}",
            )

        if geojson_data.get("type") != "FeatureCollection":
            raise ExternalDataParsingError(
                source_url=source_url,
                message=f"Expected GeoJSON 'type' to be 'FeatureCollection', got '{geojson_data.get('type')}'",
            )

        features = geojson_data.get("features")
        if not isinstance(features, list):
            raise ExternalDataParsingError(
                source_url=source_url,
                message=f"Expected GeoJSON 'features' to be a list, got {type(features).__name__}",
            )

        centroids: List[s2sphere.LatLng] = []
        # Default interpretation_rule: treat all features as restrictions and extract centroids
        # This could be made more sophisticated using `params` in the future.

        for i, feature_dict in enumerate(features):
            if not isinstance(feature_dict, dict) or feature_dict.get("type") != "Feature":
                # Log or handle malformed feature dictionary if necessary, e.g., print warning
                print(f"Warning: Skipping feature at index {i} due to malformed structure (not a Feature dictionary).")
                continue

            geometry_dict = feature_dict.get("geometry")
            if not geometry_dict:
                # Log or handle feature with no geometry
                print(f"Warning: Skipping feature at index {i} (id: {feature_dict.get('id', 'N/A')}) as it has no geometry.")
                continue

            try:
                # Using geojson library to parse the geometry explicitly first
                # This can help catch errors if the geometry itself is malformed
                # before passing to shapely.
                feature_geojson = geojson.GeoJSON.to_instance(feature_dict)
                geom = shape(feature_geojson.geometry)
                centroid = geom.centroid

                # Ensure coordinates are in (lon, lat) order as expected by s2sphere.LatLng.from_degrees
                # Shapely's Point object has .x (longitude) and .y (latitude)
                centroids.append(s2sphere.LatLng.from_degrees(centroid.y, centroid.x))
            except Exception as e:
                # Log error during centroid calculation for a specific feature
                # For now, we'll skip features that cause errors, with a warning.
                feature_id = feature_dict.get('id', f'index {i}')
                print(
                    f"Warning: Could not calculate centroid for feature '{feature_id}'. Error: {e}"
                ) # TODO: Use proper logging
                continue

        return centroids
