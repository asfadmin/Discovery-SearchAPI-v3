from typing import List
from asf_search import ASFSession


class SearchAPISession(ASFSession):
    def __init__(
        self,
        edl_host: str = None,
        edl_client_id: str = None,
        asf_auth_host: str = None,
        cmr_host: str = None,
        cmr_collections: str = None,
        auth_domains: List[str] = None,
        auth_cookie_names: List[str] = None,
    ):
        super().__init__(
            edl_host,
            edl_client_id,
            asf_auth_host,
            cmr_host,
            cmr_collections,
            auth_domains,
            auth_cookie_names,
        )

        self.headers.update({'Client-Id': f'SearchAPI_{self.headers.get("Client-Id")}'})