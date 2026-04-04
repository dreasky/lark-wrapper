from .lark_auth import LarkAuth


class BaseWrapper:
    """飞书API封装基类"""

    def __init__(self):
        self._auth = LarkAuth()
        self._client = self._auth.get_client()
        self._tenant_access_token = self._auth.get_tenant_access_token()
        self.base_url = self._auth.get_base_url()
