import sys
import requests
from pathlib import Path
from lark_oapi.api.drive.v1 import (
    ListFileRequest,
    ListFileResponseBody,
    ListFileResponse,
    UploadAllMediaRequestBody,
    UploadAllMediaResponseBody,
    UploadAllMediaRequest,
    MediaUploadInfo,
    UploadPrepareMediaRequest,
    UploadPrepareMediaResponseBody,
    FileUploadInfo,
    UploadPrepareFileRequest,
    UploadPrepareFileResponseBody,
    CreateImportTaskRequest,
    CreateImportTaskResponseBody,
    GetImportTaskRequest,
    ListFileCommentRequest,
    ListFileCommentResponse,
    CreateImportTaskResponse,
    GetImportTaskResponse,
    UploadPartMediaRequest,
    UploadPartMediaRequestBody,
    UploadFinishMediaRequest,
    UploadFinishMediaRequestBody,
    UploadFinishMediaResponseBody,
    UploadPartFileRequest,
    UploadPartFileRequestBody,
    UploadFinishFileRequest,
    UploadFinishFileRequestBody,
    UploadFinishFileResponseBody,
    CreateFolderFileRequestBody,
    CreateFolderFileRequest,
    CreateFolderFileResponseBody,
)
from lark_oapi.api.docx.v1 import (
    Document,
    CreateDocumentRequest,
    CreateDocumentRequestBody,
)
import lark_oapi as lark
from .wrapper_entity import *
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError
from typing import List, IO


def _get_status_text(job_status: int | None) -> str:
    if job_status is not None:
        return {0: "导入成功", 1: "初始化", 2: "处理中", 3: "内部错误"}.get(
            job_status,
            f"job_status={job_status}, 查阅https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/get",
        )
    else:
        return "未知状态"


class CloudSpaceWrapper(BaseWrapper):
    """飞书云文档 API 封装类"""

    def root_folder(self) -> RootFolderResult:
        """
        获取我的空间（根文件夹）元数据
        https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/get-root-folder-meta
        """
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
            token=data.get("token"),
            id=data.get("id"),
            user_id=data.get("user_id"),
        )
        print(f"✅ {fn} success", result.model_dump_json(indent=2))
        return result

    def create_folder(
        self, name: str, folder_token: str
    ) -> CreateFolderFileResponseBody:
        """
        新建文件夹
        https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/create_folder
        """
        # 动态获取当前函数名
        fn = sys._getframe(0).f_code.co_name

        request_body = (
            CreateFolderFileRequestBody.builder()
            .name(name)
            .folder_token(folder_token)
            .build()
        )
        request = CreateFolderFileRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.file.create_folder(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def list_file(self, folder_token: str = "") -> ListFileResponseBody:
        """
        获取文件夹中的文件清单
        https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/list
        """
        # 动态获取当前函数名
        fn = sys._getframe(0).f_code.co_name

        # 构造请求
        request: ListFileRequest = (
            ListFileRequest.builder().folder_token(folder_token).build()
        )

        # 发送请求
        response: ListFileResponse = self._client.drive.v1.file.list(request)

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

    def create_document(self, folder_token: str, title: str) -> Document:
        """
        创建文档
        https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create
        """
        fn = sys._getframe(0).f_code.co_name

        # 构造请求对象
        request_body = (
            CreateDocumentRequestBody.builder()
            .folder_token(folder_token)
            .title(title)
            .build()
        )
        request: CreateDocumentRequest = (
            CreateDocumentRequest.builder().request_body(request_body).build()
        )

        # 发起请求
        response = self._client.docx.v1.document.create(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")
        if response.data.document is None:
            raise WrapperError(method=fn, detail="response.data.document is null")

        # 处理响应成功
        result = response.data.document
        print(f"✅ {fn} success", self.to_json(result))
        return result

    #  === 导入文件 star ===

    # 导入文件概述: https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/import-user-guide
    def upload_all_media(
        self,
        file_path: Path,
        file_name: str,
        file_size: int,
        extra: str,
    ) -> UploadAllMediaResponseBody:
        """
        上传素材 (20M以内)
        https://open.feishu.cn/document/server-docs/docs/drive-v1/media/upload_all
        extra:
        txt、docx、md -> docx
        xlsx -> sheet
        """
        fn = sys._getframe(0).f_code.co_name

        with file_path.open("rb") as file:
            request_body = (
                UploadAllMediaRequestBody.builder()
                .file_name(file_name)
                .parent_type("ccm_import_open")
                .size(file_size)
                .extra(extra)
                .file(file)
                .build()
            )
            request = UploadAllMediaRequest.builder().request_body(request_body).build()
            response = self._client.drive.v1.media.upload_all(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")
        if response.data.file_token is None:
            raise WrapperError(method=fn, detail="response.data.file_token is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def create_import_task(
        self,
        mount_key: str,
        file_extension: str,
        file_token: str,
        type: str,
        file_name: str,
    ) -> CreateImportTaskResponseBody:
        """
        创建导入任务
        https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/create
        """
        fn = sys._getframe(0).f_code.co_name

        point = (
            ImportTaskMountPoint.builder().mount_type(1).mount_key(mount_key).build()
        )

        request_body = (
            ImportTask.builder()
            .file_extension(file_extension)
            .file_token(file_token)
            .type(type)
            .file_name(file_name)
            .point(point)
            .build()
        )

        request: CreateImportTaskRequest = (
            CreateImportTaskRequest.builder().request_body(request_body).build()
        )
        response: CreateImportTaskResponse = self._client.drive.v1.import_task.create(
            request
        )

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")
        if response.data.ticket is None:
            raise WrapperError(method=fn, detail="response.data.ticket is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def get_import_task(self, ticket: str) -> ImportTask:
        """
        查询导入任务结果
        https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/get
        """
        fn = sys._getframe(0).f_code.co_name

        request: GetImportTaskRequest = (
            GetImportTaskRequest.builder().ticket(ticket).build()
        )
        response: GetImportTaskResponse = self._client.drive.v1.import_task.get(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")
        if response.data.result is None:
            raise WrapperError(method=fn, detail="response.data.result is null")

        # 处理响应成功
        result = response.data.result
        status_text = _get_status_text(result.job_status)
        print(f"✅ {fn} {status_text}", self.to_json(result))
        return result

    def upload_prepare_media(
        self,
        file_name: str,
        parent_type: str,
        file_size: int,
        parent_node: Optional[str] = None,
        extra: Optional[str] = None,
    ) -> UploadPrepareMediaResponseBody:
        """
        分片上传素材-预上传
        https://open.feishu.cn/document/server-docs/docs/drive-v1/media/multipart-upload-media/upload_prepare
        """
        fn = sys._getframe(0).f_code.co_name

        builder = (
            MediaUploadInfo.builder()
            .file_name(file_name)
            .parent_type(parent_type)
            .size(file_size)
        )
        if parent_node:
            builder = builder.parent_node(parent_node)
        if extra:
            builder = builder.extra(extra)

        request_body = builder.build()
        request = UploadPrepareMediaRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.media.upload_prepare(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def upload_part_media(
        self,
        upload_id: str,
        seq: int,
        size: int,
        file_part,
    ):
        """
        分片上传素材-上传分片
        https://open.feishu.cn/document/server-docs/docs/drive-v1/media/multipart-upload-media/upload_part
        """
        fn = sys._getframe(0).f_code.co_name

        request_body = (
            UploadPartMediaRequestBody.builder()
            .upload_id(upload_id)
            .seq(seq)
            .size(size)
            .file(file_part)
            .build()
        )

        request = UploadPartMediaRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.media.upload_part(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)

        print(f"✅ {fn} success, upload_id: {upload_id}, seq: {seq}")

    def upload_finish_media(
        self, upload_id: str, block_num: int
    ) -> UploadFinishMediaResponseBody:
        """
        分片上传素材-完成上传
        https://open.feishu.cn/document/server-docs/docs/drive-v1/media/multipart-upload-media/upload_finish
        """
        fn = sys._getframe(0).f_code.co_name

        request_body = (
            UploadFinishMediaRequestBody.builder()
            .upload_id(upload_id)
            .block_num(block_num)
            .build()
        )

        request: UploadFinishMediaRequest = (
            UploadFinishMediaRequest.builder().request_body(request_body).build()
        )

        # 发起请求
        response = self._client.drive.v1.media.upload_finish(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")
        if response.data.file_token is None:
            raise WrapperError(method=fn, detail="response.data.file_token is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def upload_prepare_file(
        self,
        file_name: str,
        parent_type: str,
        parent_node: str,
        file_size: int,
    ) -> UploadPrepareFileResponseBody:
        """
        分片上传文件-预上传
        https://open.feishu.cn/document/server-docs/docs/drive-v1/upload/multipart-upload-file-/upload_prepare
        """
        fn = sys._getframe(0).f_code.co_name

        request_body = (
            FileUploadInfo.builder()
            .file_name(file_name)
            .parent_type(parent_type)
            .parent_node(parent_node)
            .size(file_size)
            .build()
        )

        request = UploadPrepareFileRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.file.upload_prepare(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def upload_part_file(
        self,
        upload_id: str,
        seq: int,
        size: int,
        file_part: IO[bytes],
    ):
        """
        分片上传文件-上传分片
        https://open.feishu.cn/document/server-docs/docs/drive-v1/upload/multipart-upload-file-/upload_part
        """
        fn = sys._getframe(0).f_code.co_name

        request_body = (
            UploadPartFileRequestBody.builder()
            .upload_id(upload_id)
            .seq(seq)
            .size(size)
            .file(file_part)
            .build()
        )

        request = UploadPartFileRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.file.upload_part(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)

        print(f"✅ {fn} success, upload_id: {upload_id}, seq: {seq}")

    def upload_finish_file(
        self, upload_id: str, block_num: int
    ) -> UploadFinishFileResponseBody:
        """
        分片上传文件-完成上传
        https://open.feishu.cn/document/server-docs/docs/drive-v1/upload/multipart-upload-file-/upload_finish
        """
        fn = sys._getframe(0).f_code.co_name

        request_body = (
            UploadFinishFileRequestBody.builder()
            .upload_id(upload_id)
            .block_num(block_num)
            .build()
        )

        request = UploadFinishFileRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.file.upload_finish(request)

        # 处理响应失败
        if not response.success():
            raise WrapperError(method=fn, response=response)
        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        # 处理响应成功
        result = response.data
        print(f"✅ {fn} success", self.to_json(result))
        return result

    def list_comments(
        self,
        file_token: str,
        file_type: str,
        output_dir: Optional[Path] = None,
        is_whole: Optional[bool] = None,
        is_solved: Optional[bool] = None,
        user_id_type: Optional[str] = None,
    ) -> ListCommentsResult:
        """
        获取云文档所有评论并保存到文件
        https://open.feishu.cn/document/server-docs/docs/CommentAPI/list
        """
        fn = sys._getframe(0).f_code.co_name

        all_items: List[FileCommentWrapper] = []
        page_token = None
        page_count = 0

        while True:
            page_count += 1

            builder = (
                ListFileCommentRequest.builder()
                .file_token(file_token)
                .file_type(file_type)
                .page_size(50)
            )

            if is_whole is not None:
                builder = builder.is_whole(is_whole)
            if is_solved is not None:
                builder = builder.is_solved(is_solved)
            if page_token:
                builder = builder.page_token(page_token)
            if user_id_type:
                builder = builder.user_id_type(user_id_type)

            request: ListFileCommentRequest = builder.build()
            response: ListFileCommentResponse = self._client.drive.v1.file_comment.list(
                request
            )

            # 处理响应失败
            if not response.success():
                raise WrapperError(method=fn, response=response)
            if response.data is None:
                raise WrapperError(method=fn, detail="response.data is null")
            if response.data.items is None:
                raise WrapperError(method=fn, detail="response.data.items is null")

            comments = response.data.items or []
            page_items = [
                (c if isinstance(c, FileCommentWrapper) else FileCommentWrapper(c))
                for c in comments
            ]
            all_items.extend(page_items)

            print(
                f"📄 Page {page_count}: {len(comments)} comments, total: {len(all_items)}"
            )

            # 通过 has_more 和 page_token 判断是否有更多分页
            if not response.data.has_more:
                break
            page_token = response.data.page_token
            if not page_token:
                break

        # 处理响应成功
        result = ListCommentsResult(
            file_token=file_token,
            total_comments=len(all_items),
            items=all_items,
        )
        # 保存到文件
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            comment_file = output_dir / "comments.json"
            comment_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            print(f"✅ {fn} saved to: {comment_file}")

        print(f"✅ {fn} success, total: {len(all_items)} comments")
        return result
