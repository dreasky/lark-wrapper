import sys
from pathlib import Path
from typing import List, Optional

from lark_oapi.api.drive.v1 import (
    ListFileCommentRequest,
    ListFileCommentResponse,
    FileComment,
)

from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


class CloudCommentWrapper(BaseWrapper):
    """飞书云空间-评论 API 封装类"""

    def list_comments(
        self,
        file_token: str,
        file_type: str,
        output_dir: Optional[Path] = None,
        is_whole: Optional[bool] = None,
        is_solved: Optional[bool] = None,
        user_id_type: Optional[str] = None,
    ) -> List[FileComment]:
        """
        获取云文档所有评论并保存到文件
        https://open.feishu.cn/document/server-docs/docs/CommentAPI/list
        """
        fn = sys._getframe(0).f_code.co_name

        result: List[FileComment] = []
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
            result.extend(comments)

            print(
                f"📄 Page {page_count}: {len(comments)} comments, total: {len(result)}"
            )

            # 通过 has_more 和 page_token 判断是否有更多分页
            if not response.data.has_more:
                break
            page_token = response.data.page_token
            if not page_token:
                break

        # 保存到文件
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            comment_file = output_dir / "comments.json"
            comment_file.write_text(self.to_json(result), encoding="utf-8")
            print(f"✅ {fn} saved to: {comment_file}")

        print(f"✅ {fn} success, total: {len(result)} comments")
        return result
