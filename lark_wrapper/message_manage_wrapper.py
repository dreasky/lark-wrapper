import json
from pathlib import Path
from lark_oapi.api.im.v1 import (
    CreateMessageRequestBody,
    CreateMessageRequest,
    CreateMessageResponse,
    ListMessageRequest,
    ListMessageResponse,
    GetMessageResourceRequest,
    GetMessageResourceResponse,
    GetMessageRequest,
    GetMessageResponse,
)
from .wrapper_entity import *
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
    ) -> SendMessageResult:
        """
        发送消息
        https://open.feishu.cn/document/server-docs/im-v1/message/create
        """
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

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="send_message",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        result = SendMessageResult(
            receive_id_type=receive_id_type,
            receive_id=receive_id,
            msg_type=msg_type,
        )

        print(f"✅ send_message success", result.model_dump_json(indent=2))
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
    ) -> ListMessageResult:
        """
        获取会话历史消息
        https://open.feishu.cn/document/server-docs/im-v1/message/list
        """
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

        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="list_messages",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(method="list_messages", detail="response.data is null")
        if response.data.items is None:
            raise WrapperError(
                method="list_messages", detail="response.data.items is null"
            )

        items = [MessageWrapper(m) for m in response.data.items]

        result = ListMessageResult(
            items=items,
            has_more=response.data.has_more or False,
            page_token=response.data.page_token,
        )
        print(f"✅ list_messages success", result.model_dump_json(indent=2))
        return result

    def get_message_resource(
        self,
        message_id: str,
        file_key: str,
        type: str,
        output_dir: Path,
    ) -> GetMessageResourceResult:
        """
        获取消息中的资源文件（图片、音频、视频、文件）
        https://open.feishu.cn/document/server-docs/im-v1/message/get-2
        """
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

        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="get_message_resource",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.file is None:
            raise WrapperError(
                method="get_message_resource", detail="response.file is null"
            )

        if response.file_name is None:
            raise WrapperError(
                method="get_message_resource", detail="response.file_name is null"
            )

        save_path = output_dir / response.file_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(response.file.read())

        result = GetMessageResourceResult(
            file_name=response.file_name,
            file_path=str(save_path),
        )
        print(f"✅ get_message_resource success", result.model_dump_json(indent=2))
        return result

    def get_message_content(
        self,
        message_id: str,
        user_id_type: str = "open_id",
    ) -> GetMessageContentResult:
        """
        获取指定消息的内容
        https://open.feishu.cn/document/server-docs/im-v1/message/get
        """
        request: GetMessageRequest = (
            GetMessageRequest.builder()
            .message_id(message_id)
            .user_id_type(user_id_type)
            .build()
        )
        response: GetMessageResponse = self._client.im.v1.message.get(request)

        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="get_message_content",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(
                method="get_message_content", detail="response.data is null"
            )

        if response.data.items is None:
            raise WrapperError(
                method="get_message_content", detail="response.data.items is null"
            )

        items = [MessageWrapper(m) for m in response.data.items]

        result = GetMessageContentResult(items=items)
        print(f"✅ get_message_content success", result.model_dump_json(indent=2))
        return result
