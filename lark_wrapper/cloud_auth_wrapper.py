import sys
from typing import List
from lark_oapi.api.drive.v1 import (
    BaseMember,
    CreatePermissionMemberRequest,
    CreatePermissionMemberResponse,
    BatchCreatePermissionMemberRequest,
    BatchCreatePermissionMemberRequestBody,
    BatchCreatePermissionMemberResponse,
)
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


class CloudAuthWrapper(BaseWrapper):
    """飞书云文档 - 权限 API 封装类"""

    def create_permission_member(
        self,
        member_type: str,
        member_id: str,
        perm: str,
        perm_type: str,
        type: str,
        file_token: str,
        file_type: str,
        need_notification: bool = False,
    ) -> BaseMember:
        """增加协作者权限
        https://open.feishu.cn/document/server-docs/docs/permission/permission-member/create

        Args:
            member_type (str): 协作者 ID 类型, 与协作者 ID 需要对应
            member_id (str): 协作者 ID, 该 ID 的类型与 member_type 指定的值需要保持一致
            perm (str, optional): 协作者对应的权限角色
            perm_type (str, optional): 协作者的权限角色类型。当云文档类型为 wiki 即知识库节点时, 该参数有效
            type (str, optional): 协作者类型

            file_type (str): 云文档类型, 需要与云文档的 token 相匹配
            file_token (str): 云文档的 token, 需要与 type 参数指定的云文档类型相匹配
            need_notification (bool): 添加权限后是否通知对方, 默认 false 不通知
        """
        # 动态获取当前函数名
        fn = sys._getframe(0).f_code.co_name

        # 构造请求
        member = (
            BaseMember.builder()
            .member_type(member_type)
            .member_id(member_id)
            .perm(perm)
            .perm_type(perm_type)
            .type(type)
            .build()
        )
        request: CreatePermissionMemberRequest = (
            CreatePermissionMemberRequest.builder()
            .type(file_type)
            .token(file_token)
            .need_notification(need_notification)
            .request_body(member)
            .build()
        )

        # 发起请求
        response: CreatePermissionMemberResponse = (
            self._client.drive.v1.permission_member.create(request)
        )

        # 处理失败返回
        if not response.success():
            raise WrapperError(method=fn, response=response)

        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        if response.data.member is None:
            raise WrapperError(method=fn, detail="response.data.member is null")

        # 处理成功返回
        result = response.data.member
        print(f"✅ create_permission_member success", self.to_json(result))
        return result

    def batch_create_permission_member(
        self,
        member_type: str,
        member_id_list: List[str],
        perm: str,
        perm_type: str,
        type: str,
        file_token: str,
        file_type: str,
        need_notification: bool = False,
    ) -> List[BaseMember]:
        """批量增加协作者权限
        https://open.feishu.cn/document/docs/permission/permission-member/batch_create

        Args:
            member_type (str): 协作者 ID 类型, 与协作者 ID 需要对应
            member_id_list (List[str]): 协作者 ID 列表
            perm (str): 协作者对应的权限角色
            perm_type (str): 协作者的权限角色类型。当云文档类型为 wiki 即知识库节点时, 该参数有效
            type (str): 协作者类型

            file_type (str): 云文档类型, 需要与云文档的 token 相匹配
            file_token (str): 云文档的 token, 需要与 type 参数指定的云文档类型相匹配
            need_notification (bool): 添加权限后是否通知对方, 默认 false 不通知
        """
        fn = sys._getframe(0).f_code.co_name

        member_list = [
            BaseMember.builder()
            .member_type(member_type)
            .member_id(i)
            .perm(perm)
            .perm_type(perm_type)
            .type(type)
            .build()
            for i in member_id_list
        ]
        request: BatchCreatePermissionMemberRequest = (
            BatchCreatePermissionMemberRequest.builder()
            .type(file_type)
            .token(file_token)
            .need_notification(need_notification)
            .request_body(
                BatchCreatePermissionMemberRequestBody.builder()
                .members(member_list)
                .build()
            )
            .build()
        )

        response: BatchCreatePermissionMemberResponse = (
            self._client.drive.v1.permission_member.batch_create(request)
        )

        # 处理失败返回
        if not response.success():
            raise WrapperError(method=fn, response=response)

        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        if response.data.members is None:
            raise WrapperError(method=fn, detail="response.data.members is null")

        result = response.data.members

        print(f"✅ {fn} success", self.to_json(result))
        return result
