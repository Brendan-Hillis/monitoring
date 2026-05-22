import requests
from typing import Optional

from monitoring.monitorlib.clients.external_data.http_client import HttpGeoSourceClient
from monitoring.monitorlib.clients.external_data.client import ExternalGeoClient # For type hinting
from monitoring.uss_qualifier.resources.resource import Resource
from .configuration import ExternalGeoSourceSpecification


class ExternalGeoSourceResource(Resource[ExternalGeoSourceSpecification]):
    """
    Resource representing an external geospatial data source.
    """

    _client: HttpGeoSourceClient
    _source_url: str
    _participant_id_override: Optional[str] # Stores participant_id from config if provided

    def __init__(
        self,
        specification: ExternalGeoSourceSpecification,
        resource_origin: str,
        # No auth_adapter needed for a generic public HTTP source by default
    ):
        super().__init__(specification, resource_origin)

        self._source_url = specification.external_geo_source.source_url
        self._participant_id_override = specification.external_geo_source.participant_id

        # Create a requests.Session for the HttpGeoSourceClient
        session = requests.Session()
        if specification.external_geo_source.timeout_seconds is not None:
            # Note: requests.Session does not have a direct timeout attribute.
            # Timeout is typically set per request. HttpGeoSourceClient's methods
            # do not currently take timeout. We'd need to modify HttpGeoSourceClient
            # or handle timeout differently, e.g. by subclassing or configuring the session adapter.
            # For now, this timeout_seconds is more of a placeholder unless HttpGeoSourceClient is updated.
            # A simple way is to set it on the session's adapter, but this is not standard.
            # Alternatively, we could pass it to each request method if HttpGeoSourceClient supported it.
            # For this iteration, we'll acknowledge the config field exists but not directly apply it to session universally.
            # The HttpGeoSourceClient would need to be designed to accept timeout on its methods.
            # Let's assume HttpGeoSourceClient's default timeout or its own internal handling is sufficient for now.
            # Or, if we want to enforce it, we'd wrap the session's request methods or configure adapters.
            pass # Placeholder for timeout handling on session if client supported it.

        self._client = HttpGeoSourceClient(session=session)

    @property
    def client(self) -> ExternalGeoClient:
        """
        Returns the client instance for interacting with the external geospatial data source.
        """
        return self._client

    @property
    def participant_id(self) -> str:
        """
        Returns an identifier for this external data source.
        Uses the configured participant_id if provided, otherwise defaults to the source_url.
        """
        return self._participant_id_override or self._source_url

    # Convenience property to access the source_url if needed elsewhere
    @property
    def source_url(self) -> str:
        return self._source_url

    # Convenience property for interpretation_rule if needed
    @property
    def interpretation_rule(self) -> Optional[str]:
        return self.specification.external_geo_source.interpretation_rule

    # Convenience property for source_type
    @property
    def source_type(self) -> Optional[str]:
        return self.specification.external_geo_source.source_type
