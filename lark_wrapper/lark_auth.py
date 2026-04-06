import os
import time
import json
import requests
import lark_oapi as lark
from dotenv import load_dotenv
from pathlib import Path


class LarkAuth:
    """飞书认证管理类，负责提供 client 和 tenant_access_token(单例模式)"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if LarkAuth._initialized:
            return

        load_dotenv()

        self._app_id = os.environ["FEISHU_APP_ID"]
        self._app_secret = os.environ["FEISHU_APP_SECRET"]
        self._base_url = os.environ["FEISHU_BASE_URL"]

        if not self._app_id or not self._app_secret:
            raise EnvironmentError(
                """
                ❌ 错误：未找到飞书应用凭证, 请访问 https://open.feishu.cn/获取应用凭证
                在项目根目录创建 .env 文件, 并设置 FEISHU_APP_ID、FEISHU_APP_SECRET 和 FEISHU_BASE_URL
                可参考 .env.example 文件
                """
            )

        self._client = None
        self._ws_client = None
        self._ws_client_handler = None

        self._token_cache_file = Path.home() / ".cache" / "lark_wrapper" / ".tenant_access_token.json"

        LarkAuth._initialized = True

    @classmethod
    def reset(cls):
        """重置单例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False

    def get_client(self) -> lark.Client:
        if self._client is None:
            self._client = (
                lark.Client.builder()
                .app_id(self._app_id)
                .app_secret(self._app_secret)
                .log_level(lark.LogLevel.INFO)
                .build()
            )
        return self._client

    def get_ws_client(self, event_handler: lark.EventDispatcherHandler) -> lark.ws.Client:
        if self._ws_client is None or self._ws_client_handler is not event_handler:
            self._ws_client = lark.ws.Client(
                self._app_id,
                self._app_secret,
                event_handler=event_handler,
                log_level=lark.LogLevel.INFO,
            )
            self._ws_client_handler = event_handler
        return self._ws_client

    def get_tenant_access_token(self) -> str | None:
        """获取 Tenant Access Token，带缓存机制，自动处理过期"""
        token_file = self._token_cache_file
        token_file.parent.mkdir(parents=True, exist_ok=True)

        api_url = self._base_url + "/auth/v3/tenant_access_token/internal"

        if token_file.exists():
            try:
                with open(token_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    token = cache_data.get("tenant_access_token")
                    expire = cache_data.get("expire", 0)
            except Exception as e:
                print(f"读取token失败: {e}")
                token = None
                expire = 0
        else:
            token = None
            expire = 0

        if token and time.time() < expire:
            return token

        response = requests.post(
            api_url, json={"app_id": self._app_id, "app_secret": self._app_secret}
        )
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            raise ValueError(result)

        token = result.get("tenant_access_token")
        expire = result.get("expire", 0)

        if token is None:
            raise ValueError(result)

        try:
            with open(token_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "tenant_access_token": token,
                        "expire": int(time.time()) + expire - 10,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            print(f"保存token失败: {e}")
            return None

        return token

    def get_base_url(self):
        return self._base_url
