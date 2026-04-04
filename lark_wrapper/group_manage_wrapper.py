import json
from lark_oapi.api.im.v1 import (
    ListChatRequest,
    ListChatResponse,
)
from .wrapper_entity import ListChatResult, ListChatWrapper
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


class GroupManageWrapper(BaseWrapper):
    """飞书群组 - 群组管理 API 封装类
    https://open.feishu.cn/document/server-docs/group/chat/intro
    """

    def list_chat(self) -> ListChatResult:
        """
        获取用户或机器人所在的群列表
        https://open.feishu.cn/document/server-docs/group/chat/list
        """
        request: ListChatRequest = ListChatRequest.builder().build()
        response: ListChatResponse = self._client.im.v1.chat.list(request)

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="list_chat",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(method="method_name", detail="response.data is null")

        if response.data.items is None:
            raise WrapperError(
                method="method_name", detail="response.data.items is null"
            )

        items = [ListChatWrapper(c) for c in response.data.items]

        # 处理业务结果
        result = ListChatResult(chat_count=len(items), items=items)
        print(f"✅ list_chat success", result.model_dump_json(indent=2))
        return result
