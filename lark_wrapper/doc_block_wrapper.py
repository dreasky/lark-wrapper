import sys
import json
from pathlib import Path
from typing import List, Optional
from lark_oapi.api.docx.v1 import *
from .wrapper_entity import (
    ListBlocksResult,
    BlockWrapper,
    BatchUpdateBlocksResult,
    UpdateBlockResult,
)
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError

# 块过滤列表：文本 Block、标题 1-9 Block、图片 Block
BLOCK_FILTER_LIST = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 27]


class DocBlockWrapper(BaseWrapper):
    """飞书云文档 > 文档 > 块 API 封装类"""

    def list_blocks(
        self,
        document_id: str,
        output_dir: Optional[Path] = None,
        document_revision_id: Optional[int] = None,
        user_id_type: Optional[str] = None,
        is_filter: bool = False,
    ) -> ListBlocksResult:
        """
        获取文档所有块（自动分页）并保存到文件
        https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list
        """
        fn = sys._getframe(0).f_code.co_name

        all_items: List[BlockWrapper] = []
        page_token = None
        page_count = 0

        while True:
            page_count += 1

            # 构建请求
            builder = (
                ListDocumentBlockRequest.builder()
                .document_id(document_id)
                .page_size(500)
            )
            if page_token:
                builder = builder.page_token(page_token)
            if document_revision_id is not None:
                builder = builder.document_revision_id(document_revision_id)
            if user_id_type:
                builder = builder.user_id_type(user_id_type)

            request: ListDocumentBlockRequest = builder.build()
            response: ListDocumentBlockResponse = (
                self._client.docx.v1.document_block.list(request)
            )

            if not response.success():
                raise WrapperError(method=fn, response=response)

            if response.data is None:
                raise WrapperError(method=fn, detail="response.data is null")

            if response.data.items is None:
                raise WrapperError(method=fn, detail="response.data.items is null")

            items = [BlockWrapper(b) for b in response.data.items]

            # 解析块列表
            if is_filter:
                items = [b for b in items if b.block_type in BLOCK_FILTER_LIST]

            all_items.extend(items)

            print(
                f"📄 Page {page_count}: {len(items or [])} blocks, total: {len(all_items)}"
            )

            # 通过 has_more 和 page_token 判断是否有更多分页
            if not response.data.has_more:
                break
            page_token = response.data.page_token
            if not page_token:
                break

        result = ListBlocksResult(
            document_id=document_id,
            total_blocks=len(all_items),
            items=all_items,
        )

        # 保存到文件
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            blocks_file = output_dir / "blocks.json"
            blocks_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            print(f"✅ {fn} saved to: {blocks_file}")

        print(f"✅ {fn} success, total: {len(all_items)} blocks")
        return result

    def batch_update_blocks(
        self,
        document_id: str,
        requests: List[UpdateBlockRequest],
        output_dir: Optional[Path] = None,
        document_revision_id: Optional[int] = None,
        client_token: Optional[str] = None,
        user_id_type: Optional[str] = None,
    ) -> BatchUpdateBlocksResult:
        """
        批量更新块的富文本内容
        https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/batch_update

        Args:
            document_id: 文档的唯一标识
            requests: 更新请求列表，每个请求包含 block_id 和具体更新操作
            output_dir: 输出文件目录
            document_revision_id: 要操作的文档版本，-1 表示最新版本
            client_token: 操作的唯一标识，用于幂等更新
            user_id_type: 用户 ID 类型
        """
        fn = sys._getframe(0).f_code.co_name

        # 构建请求体
        body_builder = BatchUpdateDocumentBlockRequestBody.builder().requests(requests)
        request_builder = (
            BatchUpdateDocumentBlockRequest.builder()
            .document_id(document_id)
            .request_body(body_builder.build())
        )

        if document_revision_id is not None:
            request_builder = request_builder.document_revision_id(document_revision_id)
        if client_token:
            request_builder = request_builder.client_token(client_token)
        if user_id_type:
            request_builder = request_builder.user_id_type(user_id_type)

        request: BatchUpdateDocumentBlockRequest = request_builder.build()
        response: BatchUpdateDocumentBlockResponse = (
            self._client.docx.v1.document_block.batch_update(request)
        )

        if not response.success():
            raise WrapperError(method=fn, response=response)

        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        if response.data.blocks is None:
            raise WrapperError(method=fn, detail="response.data.blocks is null")

        items = [BlockWrapper(b) for b in response.data.blocks]

        result = BatchUpdateBlocksResult(
            document_id=document_id,
            client_token=response.data.client_token,
            revision_id=response.data.document_revision_id,
            block_count=len(items),
            items=items,
        )

        # 保存到文件
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            result_file = output_dir / f"{fn}.json"
            result_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            print(f"✅ {fn} saved to: {result_file}")

        print(f"✅ {fn} success, revision_id: {result.revision_id}")
        return result

    def update_block(
        self,
        document_id: str,
        block_id: str,
        request_body: UpdateBlockRequest,
        output_dir: Optional[Path] = None,
        document_revision_id: Optional[int] = None,
        client_token: Optional[str] = None,
        user_id_type: Optional[str] = None,
    ) -> UpdateBlockResult:
        """
        更新指定块的内容
        https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/patch

        Args:
            document_id: 文档的唯一标识
            block_id: Block 的唯一标识
            request_body: 更新请求体，包含具体更新操作
            output_dir: 输出文件目录
            document_revision_id: 要操作的文档版本，-1 表示最新版本
            client_token: 操作的唯一标识，用于幂等更新
            user_id_type: 用户 ID 类型
        """
        fn = sys._getframe(0).f_code.co_name

        request_builder = (
            PatchDocumentBlockRequest.builder()
            .document_id(document_id)
            .block_id(block_id)
            .request_body(request_body)
        )

        if document_revision_id is not None:
            request_builder = request_builder.document_revision_id(document_revision_id)
        if client_token:
            request_builder = request_builder.client_token(client_token)
        if user_id_type:
            request_builder = request_builder.user_id_type(user_id_type)

        request: PatchDocumentBlockRequest = request_builder.build()
        response: PatchDocumentBlockResponse = (
            self._client.docx.v1.document_block.patch(request)
        )

        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(method=fn, response=response)

        if response.data is None:
            raise WrapperError(method=fn, detail="response.data is null")

        block = BlockWrapper(response.data.block) if response.data.block else None

        result = UpdateBlockResult(
            document_id=document_id,
            block_id=block_id,
            client_token=response.data.client_token,
            revision_id=response.data.document_revision_id,
            block=block,
        )

        # 保存到文件
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            result_file = output_dir / f"{fn}.json"
            result_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            print(f"✅ {fn} saved to: {result_file}")

        print(f"✅ {fn} success, block_id: {block_id}")
        return result
