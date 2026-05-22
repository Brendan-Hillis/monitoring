import unittest

from monitoring.uss_qualifier.resources.external_data.configuration import (
    ExternalGeoSourceConfiguration,
    ExternalGeoSourceSpecification, # For completeness, though not directly tested with complex logic
)


class TestExternalGeoSourceConfiguration(unittest.TestCase):
    def test_valid_configuration_minimal(self):
        try:
            config = ExternalGeoSourceConfiguration(source_url="http://example.com/data.geojson")
            self.assertEqual(config.source_url, "http://example.com/data.geojson")
            self.assertEqual(config.source_type, "geojson") # Default
            self.assertIsNone(config.interpretation_rule)
            self.assertIsNone(config.timeout_seconds)
            self.assertIsNone(config.participant_id)
        except ValueError as e:
            self.fail(f"ValueError raised unexpectedly for minimal valid configuration: {e}")

    def test_valid_configuration_all_fields(self):
        try:
            config = ExternalGeoSourceConfiguration(
                source_url="https://secure.example.com/another.geojson",
                source_type="geojson", # Explicitly set
                interpretation_rule="treat_as_utm_zones",
                timeout_seconds=30.5,
                participant_id="test_participant_123",
            )
            self.assertEqual(config.source_url, "https://secure.example.com/another.geojson")
            self.assertEqual(config.source_type, "geojson")
            self.assertEqual(config.interpretation_rule, "treat_as_utm_zones")
            self.assertEqual(config.timeout_seconds, 30.5)
            self.assertEqual(config.participant_id, "test_participant_123")
        except ValueError as e:
            self.fail(f"ValueError raised unexpectedly for full valid configuration: {e}")

    def test_missing_source_url(self):
        with self.assertRaises(ValueError) as context:
            # source_url is mandatory, so init without it (if ImplicitDict allows) or with None should fail
            # For ImplicitDict, if a non-Optional field has no default, it must be provided.
            # Let's try by providing it as None, though __init__ should catch it.
            ExternalGeoSourceConfiguration(**{"source_url": None})
        self.assertIn("ExternalGeoSourceConfiguration.source_url must be specified.", str(context.exception))

        with self.assertRaises(KeyError) as context_key_error:
             # Test that it's not implicitly created if missing from kwargs
            ExternalGeoSourceConfiguration(**{"participant_id": "some_id"}) # Missing source_url
        #This check depends on how ImplicitDict handles missing non-optional fields without defaults.
        #The custom __init__ should ideally catch this logic before ImplicitDict's own validation if source_url is truly absent.
        #The current custom __init__ checks `if not hasattr(self, "source_url") or not self.source_url:`,
        # which implies source_url might be an attribute but None/empty.
        # If source_url is truly missing from kwargs, ImplicitDict itself might raise a KeyError or TypeError
        # before our custom __init__ is fully effective in this specific scenario.
        # Let's refine the test to ensure our validation catches it.
        # For now, the None test above is more direct for our custom validation.

    def test_invalid_source_url_format(self):
        invalid_urls = [
            "not_a_url",
            "http//missing_colon.com",
            "ftp://example.com", # Assuming we might restrict schemes later, but valid per urlparse
            "example.com/path", # No scheme
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as context:
                    ExternalGeoSourceConfiguration(source_url=url)
                self.assertIn(f"ExternalGeoSourceConfiguration.source_url ('{url}') must be a valid URL", str(context.exception))

    def test_invalid_source_type(self):
        with self.assertRaises(ValueError) as context:
            ExternalGeoSourceConfiguration(
                source_url="http://example.com/data.json",
                source_type="not-geojson",
            )
        self.assertIn(
            "ExternalGeoSourceConfiguration.source_type: unsupported type 'not-geojson'. Currently, only 'geojson' is supported.",
            str(context.exception),
        )

    def test_source_type_case_insensitivity_and_defaulting(self):
        # Test that "GeoJSON" is accepted and normalized (though current check is str.lower())
        try:
            config_upper = ExternalGeoSourceConfiguration(
                source_url="http://example.com/data.geojson", source_type="GeoJSON"
            )
            self.assertEqual(config_upper.source_type, "geojson") # Assuming it's normalized or check is case-insensitive

            config_empty_type = ExternalGeoSourceConfiguration(
                 source_url="http://example.com/data.geojson", source_type=""
            )
            self.assertEqual(config_empty_type.source_type, "geojson") # Defaults to geojson

            config_none_type = ExternalGeoSourceConfiguration(
                 source_url="http://example.com/data.geojson", source_type=None
            )
            self.assertEqual(config_none_type.source_type, "geojson") # Defaults to geojson

        except ValueError as e:
            self.fail(f"ValueError raised unexpectedly for case/defaulting of source_type: {e}")


class TestExternalGeoSourceSpecification(unittest.TestCase):
    def test_specification_creation(self):
        # This is a very basic test, as ExternalGeoSourceSpecification is a simple container.
        try:
            config = ExternalGeoSourceConfiguration(source_url="http://example.com/spec_data.geojson")
            spec = ExternalGeoSourceSpecification(external_geo_source=config)
            self.assertIs(spec.external_geo_source, config)
        except Exception as e:
            self.fail(f"ExternalGeoSourceSpecification creation failed unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main()
