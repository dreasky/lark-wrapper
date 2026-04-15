import sys

from lark_oapi.api.docx.v1 import (
    Document,
    CreateDocumentRequest,
    CreateDocumentRequestBody,
)

from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


class CloudDocWrapper(BaseWrapper):
    """飞书云文档-文档 API 封装类"""

    def create_document(self, folder_token: str, title: str) -> Document:
        """
        创建文档
        https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create
        """
        fn = sys._getframe(0).f_code.co_name

        # 构造请求对象
        request_body = (
            CreateDocumentRequestBody.builder()
            .folder_token(folder_token)
            .title(title)
            .build()
        )
        request: CreateDocumentRequest = (
            CreateDocumentRequest.builder().request_body(request_body).build()
        )

        # 发起请求
        response = self._client.docx.v1.document.create(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")
        if response.data.document is None:
            raise WrapperError(method=fn, detail="response.data.document is null")

        # 处理响应成功
        result = response.data.document
        print(f"✅ {fn} success", self.to_json(result))
        return result
