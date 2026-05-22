from typing import Optional
from urllib.parse import urlparse
from implicitdict import ImplicitDict


class ExternalGeoSourceConfiguration(ImplicitDict):
    """Configuration for an external geospatial data source."""

    source_url: str
    """URL of the GeoJSON feed (mandatory)."""

    source_type: Optional[str] = "geojson"
    """Type of the source data (e.g., "geojson"). Defaults to "geojson".
    This field can be used for validation or to select different parsing strategies in the future.
    """

    interpretation_rule: Optional[str] = None
    """Placeholder for future use, e.g., to specify how to interpret features
    from non-homogeneous sources or sources not strictly adhering to a specific profile.
    Example: "treat_all_as_restrictions".
    """

    timeout_seconds: Optional[float] = None
    """Timeout in seconds for HTTP requests to the source_url.
    If None, the underlying HTTP client's default timeout will be used.
    """

    # Optional participant_id for associating this source with a logical entity,
    # useful for reporting or if the source represents a specific participant's data.
    # If not provided, the source_url might be used for identification.
    participant_id: Optional[str] = None
    """An optional identifier for the entity providing or represented by this data source."""


    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if not hasattr(self, "source_url") or not self.source_url:
            raise ValueError("ExternalGeoSourceConfiguration.source_url must be specified.")
        try:
            parsed_url = urlparse(self.source_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format.")
        except ValueError as e:
            raise ValueError(
                f"ExternalGeoSourceConfiguration.source_url ('{self.source_url}') must be a valid URL: {e}"
            )

        if hasattr(self, "source_type") and self.source_type:
            if self.source_type.lower() != "geojson":
                # For now, we only explicitly support "geojson".
                # This can be expanded later.
                raise ValueError(
                    f"ExternalGeoSourceConfiguration.source_type: unsupported type '{self.source_type}'. Currently, only 'geojson' is supported."
                )
        else:
            # Default to "geojson" if not specified or None/empty
            self.source_type = "geojson"


class ExternalGeoSourceSpecification(ImplicitDict):
    """Specification for an external geospatial data source resource."""

    external_geo_source: ExternalGeoSourceConfiguration
    """Configuration details for the external geospatial data source."""
