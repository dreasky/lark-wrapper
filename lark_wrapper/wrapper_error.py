from typing import Optional


class WrapperError(Exception):
    """飞书 API 调用异常，结构化存储错误详情。"""

    def __init__(
        self,
        method: str,
        code: Optional[int] = None,
        msg: Optional[str] = None,
        log_id: Optional[str] = None,
        resp: Optional[dict] = None,
        detail: Optional[str] = None,
    ):
        self.method = method
        self.code = code
        self.msg = msg
        self.log_id = log_id
        self.resp = resp
        self.detail = detail

        parts = [f"❌ {method} failed"]
        if code is not None:
            parts.append(f"code={code}")
        if msg:
            parts.append(f"msg={msg}")
        if log_id:
            parts.append(f"log_id={log_id}")
        if detail:
            parts.append(detail)
        super().__init__(", ".join(parts))
