import sys
import json
from pathlib import Path
from typing import Optional

from lark_oapi.api.im.v1 import (
    CreateMessageRequestBody,
    CreateMessageResponseBody,
    CreateMessageRequest,
    CreateMessageResponse,
    ListMessageRequest,
    ListMessageResponse,
    ListMessageResponseBody,
    GetMessageResourceRequest,
    GetMessageResourceResponse,
    GetMessageRequest,
    GetMessageResponse,
    GetMessageResponseBody,
)

from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


class MessageManageWrapper(BaseWrapper):
    """飞书消息 - 消息管理 API 封装
    https://open.feishu.cn/document/server-docs/im-v1/message/intro
    """

    def send_message(
        self,
        receive_id: str,
        receive_id_type: str,
        message: str,
        msg_type: str,
    ) -> CreateMessageResponseBody:
        """
        发送消息
        https://open.feishu.cn/document/server-docs/im-v1/message/create
        """
        fn = sys._getframe(0).f_code.co_name

        content = json.dumps({msg_type: message}, ensure_ascii=False, indent=2)

        # 构造消息请求体
        create_message_request_body = (
            CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type(msg_type)
            .content(content)
            .build()
        )

        # 构造请求对象
        request: CreateMessageRequest = (
            CreateMessageRequest.builder()
            .receive_id_type(receive_id_type)
            .request_body(create_message_request_body)
            .build()
        )

        # 发起请求
        response: CreateMessageResponse = self._client.im.v1.message.create(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def list_messages(
        self,
        container_id_type: str,
        container_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        sort_type: str = "ByCreateTimeAsc",
        page_size: int = 20,
        page_token: Optional[str] = None,
    ) -> ListMessageResponseBody:
        """
        获取会话历史消息
        https://open.feishu.cn/document/server-docs/im-v1/message/list
        """
        fn = sys._getframe(0).f_code.co_name

        builder = (
            ListMessageRequest.builder()
            .container_id_type(container_id_type)
            .container_id(container_id)
            .sort_type(sort_type)
            .page_size(page_size)
        )
        if start_time is not None:
            builder = builder.start_time(start_time)
        if end_time is not None:
            builder = builder.end_time(end_time)
        if page_token is not None:
            builder = builder.page_token(page_token)

        request: ListMessageRequest = builder.build()
        response: ListMessageResponse = self._client.im.v1.message.list(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def get_message_resource(
        self,
        message_id: str,
        file_key: str,
        type: str,
        output_dir: Path,
    ) -> Path:
        """
        获取消息中的资源文件（图片、音频、视频、文件）
        https://open.feishu.cn/document/server-docs/im-v1/message/get-2
        """
        fn = sys._getframe(0).f_code.co_name
        output_dir.mkdir(parents=True, exist_ok=True)

        request: GetMessageResourceRequest = (
            GetMessageResourceRequest.builder()
            .message_id(message_id)
            .file_key(file_key)
            .type(type)
            .build()
        )
        response: GetMessageResourceResponse = self._client.im.v1.message_resource.get(
            request
        )

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.file is None:
            raise WrapperError(method=fn, detail="response.file is null")
        if response.file_name is None:
            raise WrapperError(method=fn, detail="response.file_name is null")

        # 处理响应成功
        output_file = output_dir / response.file_name
        output_file.write_bytes(response.file.read())
        print(f"✅ {fn} success")
        return output_file

    def get_message_content(
        self,
        message_id: str,
        user_id_type: str = "open_id",
    ) -> GetMessageResponseBody:
        """
        获取指定消息的内容
        https://open.feishu.cn/document/server-docs/im-v1/message/get
        """
        fn = sys._getframe(0).f_code.co_name

        request: GetMessageRequest = (
            GetMessageRequest.builder()
            .message_id(message_id)
            .user_id_type(user_id_type)
            .build()
        )
        response: GetMessageResponse = self._client.im.v1.message.get(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result
