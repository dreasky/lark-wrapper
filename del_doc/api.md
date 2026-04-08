# 新建文件夹

该接口用于在用户云空间指定文件夹中创建一个空文件夹。

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)
Content-Type | string | 是 | **固定值**："application/json; charset=utf-8"

### 请求体

名称 | 类型 | 必填 | 描述
---|---|---|---
name | string | 是 | 文件夹名称<br>**长度限制**： 1~256 个字节<br>**示例值**："产品优化项目"
folder_token | string | 是 | 父文件夹的 token。参数为空字符串时，表示在根目录下创建文件夹。你可参考[获取文件夹中的文件清单](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/file/list)获取某个文件夹的 token。了解更多，参考[文件夹概述](https://open.feishu.cn/document/ukTMukTMukTM/ugTNzUjL4UzM14CO1MTN/folder-overview)。<br>**示例值**："fldbcO1UuPz8VwnpPx5a92abcef"

### 请求体示例
```json
{
    "name": "产品优化项目",
    "folder_token": "fldbcO1UuPz8VwnpPx5a92abcef"
}
```

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-
token | string | 新建的文件夹的 token
url | string | 新建的文件夹的 URL 链接

### 响应体示例
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "token": "fldbcddUuPz8VwnpPx5oc2abcef",
        "url": "https://feishu.cn/drive/folder/fldbcddUuPz8VwnpPx5oc2abcef"
    }
}
```
