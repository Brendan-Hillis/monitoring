import unittest
from unittest.mock import patch, MagicMock

from monitoring.uss_qualifier.resources.external_data.resource import (
    ExternalGeoSourceResource,
)
from monitoring.uss_qualifier.resources.external_data.configuration import (
    ExternalGeoSourceConfiguration,
    ExternalGeoSourceSpecification,
)
from monitoring.monitorlib.clients.external_data.http_client import HttpGeoSourceClient


class TestExternalGeoSourceResource(unittest.TestCase):
    @patch("monitoring.uss_qualifier.resources.external_data.resource.requests.Session")
    def test_init_successful_creation(self, mock_requests_session_cls):
        mock_session_instance = MagicMock()
        mock_requests_session_cls.return_value = mock_session_instance

        config = ExternalGeoSourceConfiguration(
            source_url="http://example.com/data.geojson",
            participant_id="test_participant",
            source_type="geojson", # Ensure valid type
            interpretation_rule="test_rule",
            timeout_seconds=45.0,
        )
        specification = ExternalGeoSourceSpecification(external_geo_source=config)
        resource_origin = "test_origin"

        try:
            resource = ExternalGeoSourceResource(specification, resource_origin)
            self.assertIsInstance(resource.client, HttpGeoSourceClient)
            # Verify the session passed to HttpGeoSourceClient is the one we mocked
            # HttpGeoSourceClient's constructor is HttpGeoSourceClient(session=session)
            # So, the first positional argument to its __init__ (after self) is the session.
            # We can check if our mocked session instance was used.
            # This requires HttpGeoSourceClient to store the session, e.g. as self._session
            self.assertIs(resource.client._session, mock_session_instance)

            self.assertEqual(resource.participant_id, "test_participant")
            self.assertEqual(resource.source_url, "http://example.com/data.geojson")
            self.assertEqual(resource.interpretation_rule, "test_rule")
            self.assertEqual(resource.source_type, "geojson")

        except Exception as e:
            self.fail(f"ExternalGeoSourceResource creation failed unexpectedly: {e}")

        mock_requests_session_cls.assert_called_once() # Ensure a new session was requested


    @patch("monitoring.uss_qualifier.resources.external_data.resource.requests.Session")
    def test_participant_id_defaults_to_source_url(self, mock_requests_session_cls):
        mock_requests_session_cls.return_value = MagicMock() # Mock the session instance

        config = ExternalGeoSourceConfiguration(source_url="http://another.example.com/data.json") # participant_id is None
        specification = ExternalGeoSourceSpecification(external_geo_source=config)

        resource = ExternalGeoSourceResource(specification, "test_origin_2")
        self.assertEqual(resource.participant_id, "http://another.example.com/data.json")

    # Test for timeout_seconds application would be more involved as requests.Session
    # itself doesn't take a global timeout. HttpGeoSourceClient would need to implement
    # per-request timeouts and this test would mock that client's methods.
    # Given the current HttpGeoSourceClient, we can only test that the resource construction
    # doesn't fail with timeout_seconds present.
    @patch("monitoring.uss_qualifier.resources.external_data.resource.requests.Session")
    def test_init_with_timeout(self, mock_requests_session_cls):
        mock_requests_session_cls.return_value = MagicMock()

        config = ExternalGeoSourceConfiguration(
            source_url="http://example.com/timeout.geojson",
            timeout_seconds=10.0
        )
        specification = ExternalGeoSourceSpecification(external_geo_source=config)
        try:
            ExternalGeoSourceResource(specification, "test_origin_timeout")
            # Test passes if no error during construction
        except Exception as e:
            self.fail(f"ExternalGeoSourceResource creation with timeout_seconds failed: {e}")


if __name__ == "__main__":
    unittest.main()
