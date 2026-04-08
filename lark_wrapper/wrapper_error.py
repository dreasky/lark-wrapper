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
        self.method = method
        self.code: Optional[int] = None
        self.msg: Optional[str] = None
        self.log_id: Optional[str] = None
        self.resp: Dict[str, Any] = {}
        self.detail: Optional[str] = detail

        if response:
            # 修复：去掉了多余的逗号，避免变成元组
            self.code = response.code
            self.msg = response.msg
            self.log_id = response.get_log_id()

            # 安全解析 JSON
            try:
                if response.raw and response.raw.content:
                    self.resp = json.loads(response.raw.content)
            except (json.JSONDecodeError, AttributeError):
                self.resp = {}

        self.detail = detail

        parts = [f"❌ {method} failed"]
        if self.code is not None:
            parts.append(f"code={self.code}")
        if self.msg:
            parts.append(f"msg={self.msg}")
        if self.log_id:
            parts.append(f"log_id={self.log_id}")
        if self.detail:
            parts.append(self.detail)

        super().__init__(", ".join(parts))
