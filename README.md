# lark_wrapper

飞书 (Lark/Feishu) Open API 的 Python 封装库，基于官方 `lark-oapi` SDK，提供更简洁的调用接口和结构化返回值。

## 安装

```bash
# 作为 git submodule 安装（推荐）
git submodule add https://github.com/dreasky/lark_wrapper.git libs/lark_wrapper
pip install -e libs/lark_wrapper

# 直接从 GitHub 安装
pip install git+https://github.com/dreasky/lark_wrapper.git
```

## 配置

在项目根目录创建 `.env` 文件（参考 `.env.example`）：

```text
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_BASE_URL=https://open.feishu.cn/open-apis
```

## 使用

```python
from lark_wrapper import CloudSpaceWrapper, MessageManageWrapper

# 列出云空间文件
space = CloudSpaceWrapper()
root = space.root_folder()
files = space.list_file(root.token)

# 发送消息
msg = MessageManageWrapper()
msg.send_message(receive_id_type="open_id", receive_id="ou_xxx", msg_type="text", content='{"text":"hello"}')
```

## 包含的 Wrapper

| 类 | 功能 |
|---|---|
| `CloudSpaceWrapper` | 云空间文件管理、文档创建、文件上传/导入 |
| `CloudAuthWrapper` | 文档权限管理 |
| `DocBlockWrapper` | 文档块读写 |
| `GroupManageWrapper` | 群组管理 |
| `MessageManageWrapper` | 消息收发 |
| `RobotWrapper` | 机器人信息 |

## 更新 submodule

```bash
git submodule update --remote
```
