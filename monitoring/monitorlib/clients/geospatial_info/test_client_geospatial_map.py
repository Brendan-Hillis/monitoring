import unittest
from unittest.mock import patch, MagicMock

import s2sphere
import requests
from shapely.geometry import Polygon, Point as ShapelyPoint
import geojson

from monitoring.monitorlib.clients.geospatial_info.client_geospatial_map import (
    GeospatialMapClient,
    GeospatialInfoError,
)
from monitoring.monitorlib.infrastructure import UTMClientSession


class MockUTMClientSession(UTMClientSession):
    def __init__(self, base_url="http://dummy.com"):
        super().__init__(base_url, MagicMock()) # MagicMock for auth_adapter
        # Mock the underlying client used by self.get(), self.post(), etc.
        self.client = MagicMock(spec=requests.Session)


class TestGeospatialMapClient(unittest.TestCase):
    def setUp(self):
        self.mock_session = MockUTMClientSession()
        self.participant_id = "test_participant"
        self.client = GeospatialMapClient(self.mock_session, self.participant_id)
        # self.test_geojson_fc remains for potential future tests if query_geospatial_features
        # is tested in this file. For now, it's unused after removing dynamic tests.
        # self.test_geojson_fc = {
        #     "type": "FeatureCollection",
        #     "features": [
        #         {
        #             "type": "Feature",
        #             "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
        #             "properties": {},
        #         },
        #         {
        #             "type": "Feature",
        #             "geometry": {"type": "Point", "coordinates": [2, 2]},
        #             "properties": {},
        #         },
        #     ],
        # }

    # All test_get_dynamic_features_* and test_get_dynamic_test_points_* methods
    # are removed as these functionalities are no longer part of GeospatialMapClient.

    # Example: If query_geospatial_features were to be tested here, a test might look like:
    # def test_query_geospatial_features_success(self):
    #     # Mock self.mock_session.post() or relevant method used by query_geospatial_features
    #     # Setup request data and expected response
    #     # Call self.client.query_geospatial_features(...)
    #     # Assert outcomes
    #     pass

    # For now, this class will be empty of tests if query_geospatial_features is tested elsewhere.
    # If it's the sole test class for GeospatialMapClient and query_geospatial_features is not
    # covered in another file, this test class should be updated or removed.
    # Assuming for this task, the focus is only on removing dynamic tests.
    pass


if __name__ == "__main__":
    unittest.main()
