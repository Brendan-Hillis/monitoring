import unittest
from unittest.mock import MagicMock

from monitoring.uss_qualifier.resources.geospatial_info.geospatial_info_providers import (
    GeospatialInfoProviderConfiguration,
    GeospatialInfoProviderResource, # For context, not directly tested here
    GeospatialInfoProviderSpecification,
)
from monitoring.monitorlib.clients.geospatial_info.client_geospatial_map import (
    GeospatialMapClient,
)
from monitoring.monitorlib.infrastructure import AuthAdapter


class TestGeospatialInfoProviderConfiguration(unittest.TestCase):
    def test_init_valid_static_url(self):
        try:
            GeospatialInfoProviderConfiguration(
                participant_id="test_participant",
                geospatial_map_v1_base_url="http://example.com/api/v1",
            )
        except ValueError:
            self.fail(
                "ValueError raised unexpectedly for valid geospatial_map_v1_base_url"
            )

    def test_init_invalid_static_url(self):
        with self.assertRaises(ValueError) as context:
            GeospatialInfoProviderConfiguration(
                participant_id="test_participant",
                geospatial_map_v1_base_url="not a valid url",
            )
        self.assertIn(
            "GeospatialInfoProviderConfiguration.geospatial_map_v1_base_url must be a URL",
            str(context.exception),
        )

    def test_to_client_static_only_success(self):
        mock_auth_adapter = MagicMock(spec=AuthAdapter)
        config = GeospatialInfoProviderConfiguration(
            participant_id="test_static_provider",
            geospatial_map_v1_base_url="http://static.example.com/api/v1",
        )
        client = config.to_client(mock_auth_adapter)
        self.assertIsInstance(client, GeospatialMapClient)
        self.assertEqual(client.participant_id, "test_static_provider")
        self.assertEqual(client._session.base_url, "http://static.example.com/api/v1")
        # Ensure no dynamic attributes are set on the client
        self.assertFalse(hasattr(client, "_dynamic_source_url"))
        self.assertFalse(hasattr(client, "_dynamic_source_type"))
        self.assertFalse(hasattr(client, "_dynamic_source_interpretation_rule"))


    def test_to_client_missing_static_url_raises_error(self):
        mock_auth_adapter = MagicMock(spec=AuthAdapter)
        # Configuration without geospatial_map_v1_base_url
        config_dict = {"participant_id": "test_missing_url_provider"}
        config = GeospatialInfoProviderConfiguration(**config_dict)

        # Explicitly ensure the field is absent if ImplicitDict adds it as None by default from Optional
        if hasattr(config, "geospatial_map_v1_base_url"):
             delattr(config, "geospatial_map_v1_base_url")

        with self.assertRaises(ValueError) as context:
            config.to_client(mock_auth_adapter)
        self.assertIn(
            "Could not construct GeospatialInfoClient from provided configuration: geospatial_map_v1_base_url was not specified or is invalid.",
            str(context.exception),
        )

    def test_to_client_empty_static_url_raises_error(self):
        mock_auth_adapter = MagicMock(spec=AuthAdapter)
        # Configuration with empty geospatial_map_v1_base_url
        config = GeospatialInfoProviderConfiguration(
            participant_id="test_empty_url_provider",
            geospatial_map_v1_base_url="", # Empty URL
        )

        with self.assertRaises(ValueError) as context:
            config.to_client(mock_auth_adapter)
        self.assertIn(
            "Could not construct GeospatialInfoClient from provided configuration: geospatial_map_v1_base_url was not specified or is invalid.",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
