import json
from typing import List
from lark_oapi.api.drive.v1 import (
    BaseMember,
    CreatePermissionMemberRequest,
    CreatePermissionMemberResponse,
    BatchCreatePermissionMemberRequest,
    BatchCreatePermissionMemberRequestBody,
    BatchCreatePermissionMemberResponse,
)
from .wrapper_entity import (
    PermissionMemberResult,
    BatchPermissionMemberResult,
    BaseMemberWrapper,
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
    ) -> PermissionMemberResult:
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
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="create_permission_member",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(
                method="create_permission_member", detail="response.data is null"
            )

        if response.data.member is None:
            raise WrapperError(
                method="create_permission_member",
                detail="response.data.member is null",
            )

        item = BaseMemberWrapper(response.data.member)

        # 处理业务结果
        result = PermissionMemberResult(item=item)
        print(f"✅ create_permission_member success", result.model_dump_json(indent=2))
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
    ) -> BatchPermissionMemberResult:
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
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="batch_create_permission_member",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(
                method="batch_create_permission_member", detail="response.data is null"
            )

        if response.data.members is None:
            raise WrapperError(
                method="batch_create_permission_member",
                detail="response.data.members is null",
            )

        items = [BaseMemberWrapper(m) for m in response.data.members]

        # 处理业务结果
        result = BatchPermissionMemberResult(
            member_count=len(member_id_list), items=items
        )
        print(
            f"✅ batch_create_permission_member success",
            result.model_dump_json(indent=2),
        )
        return result
