from typing import List
from pydantic import BaseModel


# === 云文档相关实体 ===
class RootFolderResult(BaseModel):
    token: str
    id: str
    user_id: str


# === 机器人信息实体 ===
class GetBotInfoResult(BaseModel):
    open_id: str
    app_name: str
    avatar_url: str
    activate_status: int
    ip_white_list: List[str]
