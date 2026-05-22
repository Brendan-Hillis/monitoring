import unittest
from unittest.mock import patch, MagicMock

import s2sphere # type: ignore[import-untyped]
import requests
import geojson # type: ignore[import-untyped]

from monitoring.monitorlib.clients.external_data.http_client import (
    HttpGeoSourceClient,
    ExternalDataConnectionError,
    ExternalDataParsingError,
)


class TestHttpGeoSourceClient(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock(spec=requests.Session)
        self.client_with_mock_session = HttpGeoSourceClient(session=self.mock_session)
        self.client_default_session = HttpGeoSourceClient() # Test with default session

        self.test_source_url = "http://example.com/data.geojson"
        self.sample_geojson_fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
                    "properties": {"id": "poly1"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [2, 2]}, # lon, lat
                    "properties": {"id": "point1"},
                },
            ],
        }

    def test_init_with_session(self):
        self.assertIs(self.client_with_mock_session._session, self.mock_session)

    def test_init_default_session(self):
        self.assertIsInstance(self.client_default_session._session, requests.Session)

    # --- Tests for get_raw_features ---
    def test_get_raw_features_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_geojson_fc
        mock_response.status_code = 200
        self.mock_session.get.return_value = mock_response

        features = self.client_with_mock_session.get_raw_features(self.test_source_url)
        self.assertEqual(features, self.sample_geojson_fc)
        self.mock_session.get.assert_called_once_with(self.test_source_url, params=None)
        mock_response.raise_for_status.assert_called_once()

    def test_get_raw_features_invalid_json(self):
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.status_code = 200
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(ExternalDataParsingError) as context:
            self.client_with_mock_session.get_raw_features(self.test_source_url)
        self.assertIn("Failed to decode JSON response", str(context.exception))
        self.assertEqual(context.exception.source_url, self.test_source_url)

    def test_get_raw_features_request_exception(self):
        self.mock_session.get.side_effect = requests.exceptions.Timeout("Connection timeout")

        with self.assertRaises(ExternalDataConnectionError) as context:
            self.client_with_mock_session.get_raw_features(self.test_source_url)
        self.assertIn("Connection or fetch error", str(context.exception))
        self.assertEqual(context.exception.source_url, self.test_source_url)
        self.assertIsInstance(context.exception.original_exception, requests.exceptions.Timeout)

    def test_get_raw_features_http_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Not Found", response=mock_response
        )
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(ExternalDataConnectionError) as context:
            self.client_with_mock_session.get_raw_features(self.test_source_url)
        self.assertIn("Connection or fetch error", str(context.exception))
        self.assertEqual(context.exception.source_url, self.test_source_url)
        self.assertIsInstance(context.exception.original_exception, requests.exceptions.HTTPError)

    # --- Tests for get_test_points ---
    @patch.object(HttpGeoSourceClient, "get_raw_features")
    def test_get_test_points_success(self, mock_get_raw_features):
        mock_get_raw_features.return_value = self.sample_geojson_fc

        points = self.client_with_mock_session.get_test_points(self.test_source_url)

        self.assertEqual(len(points), 2)
        # Polygon centroid (0.5, 0.5) -> s2sphere LatLng(0.5, 0.5)
        self.assertIsInstance(points[0], s2sphere.LatLng)
        self.assertAlmostEqual(points[0].lat().degrees, 0.5)
        self.assertAlmostEqual(points[0].lng().degrees, 0.5)
        # Point (2, 2) -> s2sphere LatLng(2, 2)
        self.assertIsInstance(points[1], s2sphere.LatLng)
        self.assertAlmostEqual(points[1].lat().degrees, 2.0) # lat is y
        self.assertAlmostEqual(points[1].lng().degrees, 2.0) # lon is x
        mock_get_raw_features.assert_called_once_with(self.test_source_url, None)

    @patch.object(HttpGeoSourceClient, "get_raw_features")
    def test_get_test_points_no_features(self, mock_get_raw_features):
        empty_fc = {"type": "FeatureCollection", "features": []}
        mock_get_raw_features.return_value = empty_fc

        points = self.client_with_mock_session.get_test_points(self.test_source_url)
        self.assertEqual(len(points), 0)

    @patch.object(HttpGeoSourceClient, "get_raw_features")
    def test_get_test_points_not_feature_collection(self, mock_get_raw_features):
        invalid_fc = {"type": "NotAFeatureCollection", "features": []}
        mock_get_raw_features.return_value = invalid_fc

        with self.assertRaises(ExternalDataParsingError) as context:
            self.client_with_mock_session.get_test_points(self.test_source_url)
        self.assertIn("Expected GeoJSON 'type' to be 'FeatureCollection'", str(context.exception))

    @patch.object(HttpGeoSourceClient, "get_raw_features")
    def test_get_test_points_features_not_list(self, mock_get_raw_features):
        invalid_fc = {"type": "FeatureCollection", "features": "not-a-list"}
        mock_get_raw_features.return_value = invalid_fc

        with self.assertRaises(ExternalDataParsingError) as context:
            self.client_with_mock_session.get_test_points(self.test_source_url)
        self.assertIn("Expected GeoJSON 'features' to be a list", str(context.exception))


    @patch.object(HttpGeoSourceClient, "get_raw_features")
    @patch("builtins.print") # To capture warning prints
    def test_get_test_points_malformed_feature_dict(self, mock_print, mock_get_raw_features):
        malformed_fc = {
            "type": "FeatureCollection",
            "features": [
                "not-a-feature-dict", # Malformed
                self.sample_geojson_fc["features"][0] # Valid
            ],
        }
        mock_get_raw_features.return_value = malformed_fc

        points = self.client_with_mock_session.get_test_points(self.test_source_url)
        self.assertEqual(len(points), 1) # Only the valid feature should be processed
        mock_print.assert_any_call("Warning: Skipping feature at index 0 due to malformed structure (not a Feature dictionary).")

    @patch.object(HttpGeoSourceClient, "get_raw_features")
    @patch("builtins.print")
    def test_get_test_points_feature_no_geometry(self, mock_print, mock_get_raw_features):
        fc_no_geom = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"id": "no_geom"}}, # No geometry
                self.sample_geojson_fc["features"][1] # Valid point
            ],
        }
        mock_get_raw_features.return_value = fc_no_geom

        points = self.client_with_mock_session.get_test_points(self.test_source_url)
        self.assertEqual(len(points), 1)
        mock_print.assert_any_call("Warning: Skipping feature at index 0 (id: no_geom) as it has no geometry.")


    @patch.object(HttpGeoSourceClient, "get_raw_features")
    @patch("builtins.print")
    def test_get_test_points_invalid_geometry_for_centroid(self, mock_print, mock_get_raw_features):
        # Shapely might raise an error for truly malformed or unprocessable geometry strings
        # geojson.GeoJSON.to_instance might catch it first if geometry is not even valid GeoJSON.
        fc_bad_geom = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": "bad_coords"}, "properties": {"id": "bad_geom"}},
                self.sample_geojson_fc["features"][1] # Valid point
            ],
        }
        mock_get_raw_features.return_value = fc_bad_geom

        points = self.client_with_mock_session.get_test_points(self.test_source_url)
        self.assertEqual(len(points), 1) # Only the valid point
        # geojson.errors.InvalidCoordinatesError / ValueError from geojson lib
        mock_print.assert_any_call("Warning: Could not calculate centroid for feature 'bad_geom'. Error: The geometry has no valid coordinates")


    @patch.object(HttpGeoSourceClient, "get_raw_features")
    def test_get_test_points_propagates_get_raw_features_error(self, mock_get_raw_features):
        mock_get_raw_features.side_effect = ExternalDataConnectionError(source_url=self.test_source_url)
        with self.assertRaises(ExternalDataConnectionError):
            self.client_with_mock_session.get_test_points(self.test_source_url)

if __name__ == "__main__":
    unittest.main()
