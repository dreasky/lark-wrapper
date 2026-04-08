import json
from typing import Optional, Dict, Any

from lark_oapi.core.model import BaseResponse


class WrapperError(Exception):
    """飞书 API 调用异常，结构化存储错误详情。"""

    def __init__(
        self,
        method: str,
        response: Optional[BaseResponse] = None,
        detail: Optional[str] = None,
    ):
        self.method = method
        self.resp: Dict[str, Any] = {}
        self.detail: Optional[str] = detail

        if response:
            # 安全解析 JSON
            try:
                if response.raw and response.raw.content:
                    self.resp = json.loads(response.raw.content)
            except (json.JSONDecodeError, AttributeError):
                self.resp = {}

        parts = [f"❌ {method} failed"]
        if self.detail:
            parts.append(self.detail)
        if self.resp:
            parts.append(str(self.resp))

        super().__init__(", ".join(parts))
