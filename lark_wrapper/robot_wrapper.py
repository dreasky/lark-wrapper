import sys
import requests

from .base_wrapper import BaseWrapper
from .wrapper_entity import GetBotInfoResult
from .wrapper_error import WrapperError


class RobotWrapper(BaseWrapper):
    """飞书机器人 API 封装
    https://open.feishu.cn/document/server-docs/bot-v3/bot/get
    """

    def get_bot_info(self) -> GetBotInfoResult:
        """
        获取机器人信息
        https://open.feishu.cn/document/server-docs/bot-v3/bot/get
        """
        fn = sys._getframe(0).f_code.co_name

        url = f"{self.base_url}/bot/v3/info"
        headers = {"Authorization": f"Bearer {self._tenant_access_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        resp_json = response.json()

        if resp_json.get("code") != 0:
            raise WrapperError(method=fn, detail=resp_json)

        if resp_json["bot"].get("open_id") is None:
            raise WrapperError(method=fn, detail=resp_json)

        bot = resp_json["bot"]
        result = GetBotInfoResult(
            open_id=bot.get("open_id"),
            app_name=bot.get("app_name"),
            avatar_url=bot.get("avatar_url"),
            activate_status=bot.get("activate_status"),
            ip_white_list=bot.get("ip_white_list", []),
        )
        print(f"✅ {fn} success", result.model_dump_json(indent=2))
        return result
