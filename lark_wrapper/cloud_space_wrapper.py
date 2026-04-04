import json
import requests
from pathlib import Path
from lark_oapi.api.drive.v1 import (
    ListFileRequest,
    ListFileResponse,
    UploadAllMediaRequestBody,
    UploadAllMediaRequest,
    MediaUploadInfo,
    UploadPrepareMediaRequest,
    FileUploadInfo,
    UploadPrepareFileRequest,
    CreateImportTaskRequest,
    GetImportTaskRequest,
    ListFileCommentRequest,
    ListFileCommentResponse,
    CreateImportTaskResponse,
    GetImportTaskResponse,
    UploadPartMediaRequest,
    UploadPartMediaRequestBody,
    UploadFinishMediaRequest,
    UploadFinishMediaRequestBody,
    UploadPartFileRequest,
    UploadPartFileRequestBody,
    UploadFinishFileRequest,
    UploadFinishFileRequestBody,
)
from lark_oapi.api.docx.v1 import (
    CreateDocumentRequest,
    CreateDocumentRequestBody,
)
from .wrapper_entity import *
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError
from typing import List, IO


class CloudSpaceWrapper(BaseWrapper):
    """飞书云文档 API 封装类"""

    def root_folder(self) -> RootFolderResult:
        """
        获取我的空间（根文件夹）元数据
        https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/get-root-folder-meta
        """
        url = self.base_url + "/drive/explorer/v2/root_folder/meta"
        headers = {"Authorization": f"Bearer {self._tenant_access_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        resp_json = response.json()

        # 处理失败返回
        if resp_json.get("code") != 0:
            raise WrapperError(method="root_folder", resp=resp_json)

        # 处理业务结果
        data = resp_json.get("data", {})

        result = RootFolderResult(
            token=data.get("token"),
            id=data.get("id"),
            user_id=data.get("user_id"),
        )
        print(f"✅ root_folder success", result.model_dump_json(indent=2))
        return result

    def list_file(self, folder_token: str = "") -> ListFileResult:
        """
        获取文件夹中的文件清单
        https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/list
        """
        request: ListFileRequest = (
            ListFileRequest.builder().folder_token(folder_token).build()
        )
        response: ListFileResponse = self._client.drive.v1.file.list(request)

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="list_file",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(method="method_name", detail="response.data is null")

        if response.data.files is None:
            raise WrapperError(
                method="method_name", detail="response.data.files is null"
            )

        # 处理业务结果
        items = [FileWrapper(f) for f in response.data.files]
        result = ListFileResult(file_count=len(items), items=items)
        print(f"✅ list_file success", result.model_dump_json(indent=2))
        return result

    def create_document(self, folder_token: str, title: str) -> CreateDocumentResult:
        """
        创建文档
        https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create
        """

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
        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="create_document",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )
        if response.data is None:
            raise WrapperError(method="create_document", detail="response.data is null")
        if response.data.document is None:
            raise WrapperError(
                method="create_document", detail="response.data.document is null"
            )

        # 处理业务结果
        result = CreateDocumentResult(item=DocumentWapper(response.data.document))
        print(f"✅ create_document success", result.model_dump_json(indent=2))
        return result

    # 导入文件概述: https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/import-user-guide
    def upload_all_media(
        self,
        file_path: Path,
        file_name: str,
        file_size: int,
        extra: str,
    ) -> UploadMediaResult:
        """
        上传素材 (20M以内)
        https://open.feishu.cn/document/server-docs/docs/drive-v1/media/upload_all
        extra:
        txt、docx、md -> docx
        xlsx -> sheet
        """

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

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="upload_all_media",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(
                method="upload_all_media", detail="response.data is null"
            )

        if response.data.file_token is None:
            raise WrapperError(
                method="upload_all_media", detail="response.data.file_token is null"
            )

        # 处理业务结果
        result = UploadMediaResult(
            file_token=response.data.file_token, file_name=file_name
        )
        print(f"✅ upload_all_media success", result.model_dump_json(indent=2))
        return result

    def create_import_task(
        self,
        mount_key: str,
        file_extension: str,
        file_token: str,
        type: str,
        file_name: str,
    ) -> ImportTaskTicket:
        """
        创建导入任务
        https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/create
        """
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

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="create_import_task",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(
                method="create_import_task", detail="response.data is null"
            )

        if response.data.ticket is None:
            raise WrapperError(
                method="create_import_task", detail="response.data.ticket is null"
            )

        # 处理业务结果
        result = ImportTaskTicket(ticket=response.data.ticket)
        print(f"✅ create_import_task success", result.model_dump_json(indent=2))
        return result

    def get_import_task(self, ticket: str) -> ImportTaskResult:
        """
        查询导入任务结果
        https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/get
        """
        request: GetImportTaskRequest = (
            GetImportTaskRequest.builder().ticket(ticket).build()
        )
        response: GetImportTaskResponse = self._client.drive.v1.import_task.get(request)
        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="get_import_task",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(method="get_import_task", detail="response.data is null")

        if response.data.result is None:
            raise WrapperError(
                method="get_import_task", detail="response.data.result is null"
            )

        item = ImportTaskWapper(response.data.result)
        status_text = item.get_status_text()

        result = ImportTaskResult(status_text=status_text, item=item)
        print(f"✅ get_import_task success", result.model_dump_json(indent=2))
        return result

    def upload_prepare_media(
        self,
        file_name: str,
        parent_type: str,
        file_size: int,
        parent_node: Optional[str] = None,
        extra: Optional[str] = None,
    ) -> UploadPrepareMediaResult:
        """
        分片上传素材-预上传
        https://open.feishu.cn/document/server-docs/docs/drive-v1/media/multipart-upload-media/upload_prepare
        """
        print(f"file_name: {file_name}")
        print(f"file_size: {file_size}")
        print(f"extra: {extra}")

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
        # 构造请求对象
        request = UploadPrepareMediaRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.media.upload_prepare(request)

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="upload_prepare_media",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )
        if response.data is None:
            raise WrapperError(
                method="upload_prepare_media", detail="response.data is null"
            )
        if response.data.upload_id is None:
            raise WrapperError(
                method="upload_prepare_media", detail="response.data.upload_id is null"
            )
        if response.data.block_size is None:
            raise WrapperError(
                method="upload_prepare_media", detail="response.data.block_size is null"
            )
        if response.data.block_num is None:
            raise WrapperError(
                method="upload_prepare_media", detail="response.data.block_num is null"
            )

        # 处理业务结果
        result = UploadPrepareMediaResult(
            upload_id=response.data.upload_id,
            block_size=response.data.block_size,
            block_num=response.data.block_num,
        )

        print(f"✅ upload_prepare_media success", result.model_dump_json(indent=2))
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
        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="upload_part_media",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        print(f"✅ upload_part_media success, upload_id: {upload_id}, seq: {seq}")

    def upload_finish_media(
        self, upload_id: str, block_num: int
    ) -> UploadFinishMediaResult:
        """
        分片上传素材-完成上传
        https://open.feishu.cn/document/server-docs/docs/drive-v1/media/multipart-upload-media/upload_finish
        """
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
        # 处理失败返回
        if not response.success():

            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="upload_finish_media",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )
        if response.data is None:
            raise WrapperError(
                method="upload_finish_media", detail="response.data is null"
            )
        if response.data.file_token is None:
            raise WrapperError(
                method="upload_finish_media", detail="response.data.file_token is null"
            )

        result = UploadFinishMediaResult(file_token=response.data.file_token)
        print(f"✅ upload_finish_media success", result.model_dump_json(indent=2))
        return result

    def upload_prepare_file(
        self,
        file_name: str,
        parent_type: str,
        parent_node: str,
        file_size: int,
    ) -> UploadPrepareFileResult:
        """
        分片上传文件-预上传
        https://open.feishu.cn/document/server-docs/docs/drive-v1/upload/multipart-upload-file-/upload_prepare
        """
        request_body = (
            FileUploadInfo.builder()
            .file_name(file_name)
            .parent_type(parent_type)
            .parent_node(parent_node)
            .size(file_size)
            .build()
        )

        # 构造请求对象
        request = UploadPrepareFileRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.file.upload_prepare(request)

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="upload_prepare_file",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )
        if response.data is None:
            raise WrapperError(
                method="upload_prepare_file", detail="response.data is null"
            )
        if response.data.upload_id is None:
            raise WrapperError(
                method="upload_prepare_file", detail="response.data.upload_id is null"
            )
        if response.data.block_size is None:
            raise WrapperError(
                method="upload_prepare_file", detail="response.data.block_size is null"
            )
        if response.data.block_num is None:
            raise WrapperError(
                method="upload_prepare_file", detail="response.data.block_num is null"
            )

        # 处理业务结果
        result = UploadPrepareFileResult(
            upload_id=response.data.upload_id,
            block_size=response.data.block_size,
            block_num=response.data.block_num,
        )

        print(f"✅ upload_prepare_file success", result.model_dump_json(indent=2))
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
        print("upload_id:", upload_id)
        print("seq:", seq)
        print("size:", size)
        print("file_part:", file_part)

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
        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="upload_part_file",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        print(f"✅ upload_part_file success, upload_id: {upload_id}, seq: {seq}")

    def upload_finish_file(
        self, upload_id: str, block_num: int
    ) -> UploadFinishFileResult:
        """
        分片上传文件-完成上传
        https://open.feishu.cn/document/server-docs/docs/drive-v1/upload/multipart-upload-file-/upload_finish
        """
        request_body = (
            UploadFinishFileRequestBody.builder()
            .upload_id(upload_id)
            .block_num(block_num)
            .build()
        )

        request = UploadFinishFileRequest.builder().request_body(request_body).build()

        # 发起请求
        response = self._client.drive.v1.file.upload_finish(request)
        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="upload_finish_file",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )
        if response.data is None:
            raise WrapperError(
                method="upload_finish_file", detail="response.data is null"
            )
        if response.data.file_token is None:
            raise WrapperError(
                method="upload_finish_file", detail="response.data.file_token is null"
            )

        result = UploadFinishFileResult(file_token=response.data.file_token)
        print(f"✅ upload_finish_file success", result.model_dump_json(indent=2))
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

            if not response.success():
                resp_data = (
                    json.loads(response.raw.content)
                    if response.raw and response.raw.content
                    else {}
                )
                raise WrapperError(
                    method="list_comments",
                    code=response.code,
                    msg=response.msg,
                    log_id=response.get_log_id(),
                    resp=resp_data,
                )

            if response.data is None:
                raise WrapperError(
                    method="list_comments", detail="response.data is null"
                )

            if response.data.items is None:
                raise WrapperError(
                    method="list_comments", detail="response.data.items is null"
                )

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
            print(f"✅ list_comments saved to: {comment_file}")

        print(f"✅ list_comments success, total: {len(all_items)} comments")
        return result
