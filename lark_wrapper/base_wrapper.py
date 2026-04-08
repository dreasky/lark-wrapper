import json
from typing import Any

from .lark_auth import LarkAuth


class BaseWrapper:
    """飞书API封装基类"""

    def __init__(self):
        self._auth = LarkAuth()
        self._client = self._auth.get_client()
        self._tenant_access_token = self._auth.get_tenant_access_token()
        self.base_url = self._auth.get_base_url()

    def to_json(self, obj: Any, indent: int = 2) -> str:
        """
        通用对象转 JSON 字符串工具。
        利用 json.loads 自动处理 bytes/str，利用 default 处理自定义对象。
        """

        def _default_serializer(o):
            # 优先处理 Pydantic V2 模型
            if hasattr(o, "model_dump"):
                return o.model_dump()
            # 处理普通类实例
            if hasattr(o, "__dict__"):
                return o.__dict__
            return str(o)

        try:
            obj = json.loads(obj)
        except (TypeError, json.JSONDecodeError):
            pass

        # 统一序列化
        return json.dumps(
            obj, indent=indent, ensure_ascii=False, default=_default_serializer
        )
