import sys
from typing import List
from lark_oapi.api.im.v1 import (
    ListChat,
    ListChatRequest,
    ListChatResponse,
)
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


class GroupManageWrapper(BaseWrapper):
    """飞书群组 - 群组管理 API 封装类
    https://open.feishu.cn/document/server-docs/group/chat/intro
    """

    def list_chat(self) -> List[ListChat]:
        """
        获取用户或机器人所在的群列表
        https://open.feishu.cn/document/server-docs/group/chat/list
        """
        fn = sys._getframe(0).f_code.co_name

        request: ListChatRequest = ListChatRequest.builder().build()
        response: ListChatResponse = self._client.im.v1.chat.list(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")
        if response.data.items is None:
            raise WrapperError(method=fn, detail="response.data.items is null")

        # 处理响应成功
        result = response.data.items
        print(f"✅ {fn} success", self.to_json(result))
        return result
