# 飞书 API Wrapper 开发规范

## 文件结构

```text
lark_wrapper/
├── __init__.py               # 导出
├── base_wrapper.py           # 基类（不添加业务方法）
├── lark_auth.py              # 鉴权（不修改）
├── wrapper_entity.py         # 实体类
├── wrapper_error.py          # 异常类
└── {module}_wrapper.py       # API 封装
    
```

---

## 实体类（wrapper_entity.py）

创建至`wrapper_entity.py`

### 命名规则

| 类型 | 格式 | 示例 |
| -- | -- | -- |
| Wrapper | `{Entity}Wrapper` | `BlockWrapper` |
| Result | `{Action}Result` | `ListBlocksResult` |
| 内部属性 | `_{entity}` | `_block`, `_comment` |

---

## Wrapper 文件

### 提供了SDK用法

```python
class XxxWrapper(BaseWrapper):
    def do_something(self, param: str) -> "response.data的具体类型，非None":
        """方法说明\nhttps://open.feishu.cn/document/..."""
        # 动态获取当前函数名
        fn = sys._getframe(0).f_code.co_name

        # 构造请求
        request = XxxRequest.builder().param(param).build()

        # 发送请求
        response = self._client.xxx.v1.yyy.zzz(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")
        if response.data.files is None:
            raise WrapperError(method=fn, detail="response.data.files is null")

        # 处理响应成功
        print(f"✅ {fn} success", self.to_json(response.data))
        return response.data
```

### 原始HTTP请求

```python
def do_something(self) -> XxxResult:
    """方法说明\nhttps://open.feishu.cn/document/..."""
    # 动态获取当前函数名
    fn = sys._getframe(0).f_code.co_name

    # 构造请求
    url = self.base_url + "/drive/explorer/v2/root_folder/meta"
    headers = {"Authorization": f"Bearer {self._tenant_access_token}"}

    # 发送请求
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    resp_json = response.json()

    # 处理响应失败
    if resp_json.get("code") != 0:
        raise WrapperError(method=fn, detail=resp_json)

    # 处理响应成功
    data = resp_json.get("data", {})
    result = RootFolderResult(
        xxx=data.get("xxx"),
        ...
    )
    print(f"✅ {fn} success", result.model_dump_json(indent=2))
    return result
```
