from typing import List, Optional, Any, Set
from pydantic import BaseModel, field_serializer
from lark_oapi.api.docx.v1 import (
    # 基础类型
    Block,
    Text,
    # 复杂内容类型
    Bitable,
    Callout,
    ChatCard,
    Diagram,
    Divider,
    File as BlockFile,
    Grid,
    GridColumn,
    Iframe,
    Image,
    Isv,
    AddOns,
    Mindnote,
    Sheet,
    Table,
    TableCell,
    View,
    Undefined,
    QuoteContainer,
    # 任务与目标
    Task,
    Okr,
    OkrObjective,
    OkrKeyResult,
    OkrProgress,
    # 外部集成与特殊视图
    JiraIssue,
    WikiCatalog,
    Board,
    Agenda,
    AgendaItem,
    AgendaItemTitle,
    AgendaItemContent,
    LinkPreview,
    SourceSynced,
    ReferenceSynced,
    SubPageList,
    AiTemplate,
    ReferenceBase,
    Project,
    MeetingNotesQa,
    Document,
)
from lark_oapi.api.drive.v1 import (
    FileComment,
    File,
    ShortcutInfo,
    ImportTask,
    ImportTaskMountPoint,
    ReplyList,
)
from lark_oapi.api.im.v1 import Message, ListChat


# === 通用序列化工具 ===
def _serialize_value(v: Any) -> Any:
    """递归序列化值"""
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, list):
        return [_serialize_value(item) for item in v]
    if hasattr(v, "__dict__"):
        result = {}
        for k2, v2 in v.__dict__.items():
            if v2 is not None:
                result[k2] = _serialize_value(v2)
        return result if result else None
    return str(v)


def _serialize_wrapper_items(items: List[Any], inner_attr: str) -> List[dict]:
    """
    序列化 Wrapper 列表

    Args:
        items: Wrapper 对象列表
        inner_attr: 内部 SDK 对象的属性名，如 '_block', '_comment', '_message'
    """
    result_list = []
    for item in items:
        result = {}
        inner_obj = getattr(item, inner_attr, None)
        if inner_obj and hasattr(inner_obj, "__dict__"):
            for k, v in inner_obj.__dict__.items():
                if v is not None:
                    result[k] = _serialize_value(v)
        result_list.append(result)
    return result_list


def _serialize_wrapper_item(item: Any, inner_attr: str) -> dict:
    """
    序列化单个 Wrapper 对象

    Args:
        item: Wrapper 对象
        inner_attr: 内部 SDK 对象的属性名，如 '_member', '_comment'
    """
    result = {}
    inner_obj = getattr(item, inner_attr, None)
    if inner_obj and hasattr(inner_obj, "__dict__"):
        for k, v in inner_obj.__dict__.items():
            if v is not None:
                result[k] = _serialize_value(v)
    return result


# === 云文档相关实体 ===
class RootFolderResult(BaseModel):
    token: str
    id: str
    user_id: str


# === 消息相关实体 ===
class GetMessageResourceResult(BaseModel):
    file_name: str
    file_path: str


# === 机器人信息实体 ===
class GetBotInfoResult(BaseModel):
    open_id: str
    app_name: str
    avatar_url: str
    activate_status: int
    ip_white_list: List[str]


# === 评论相关实体 ===
class FileCommentWrapper:
    """FileComment 包装类 (组合模式)"""

    def __init__(self, comment: FileComment):
        object.__setattr__(self, "_comment", comment)

    # 类型注解（不赋值），仅用于 IDE 智能提示
    comment_id: Optional[str]
    user_id: Optional[str]
    create_time: Optional[int]
    update_time: Optional[int]
    is_solved: Optional[bool]
    solved_time: Optional[int]
    solver_user_id: Optional[str]
    has_more: Optional[bool]
    page_token: Optional[str]
    is_whole: Optional[bool]
    quote: Optional[str]
    reply_list: Optional[ReplyList]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._comment, name)

    def extract_comment_replies(self) -> List[str]:
        """提取评论的所有回复内容"""
        if not self.reply_list:
            return []

        replies = []
        for reply in self.reply_list.replies or []:
            if not reply.content:
                continue

            for elem in reply.content.elements or []:
                if not elem.text_run:
                    continue
                if not elem.text_run.text:
                    continue

                replies.append(elem.text_run.text)
        return replies


class ListCommentsResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    file_token: str
    total_comments: int
    items: List[FileCommentWrapper]

    @field_serializer("items")
    def serialize_items(self, items: List[FileCommentWrapper]) -> List[dict]:
        return _serialize_wrapper_items(items, "_comment")


# === 文档块相关实体 ===

# 文本类 block_type -> 属性
BLOCK_TYPE_TEXT_ATTR_MAP = {
    1: "page",
    2: "text",
    3: "heading1",
    4: "heading2",
    5: "heading3",
    6: "heading4",
    7: "heading5",
    8: "heading6",
    9: "heading7",
    10: "heading8",
    11: "heading9",
    12: "bullet",
    13: "ordered",
    14: "code",
    15: "quote",
    17: "todo",
}
BLOCK_IMAGE_TYPE = 27  # 图片

# Block 类型映射表
BLOCK_TYPE_TO_STR = {
    1: "页面",
    2: "文本",
    3: "标题1",
    4: "标题2",
    5: "标题3",
    6: "标题4",
    7: "标题5",
    8: "标题6",
    9: "标题7",
    10: "标题8",
    11: "标题9",
    12: "无序列表",
    13: "有序列表",
    14: "代码块",
    15: "引用",
    17: "待办事项",
    18: "多维表格",
    19: "高亮块",
    20: "会话卡片",
    21: "流程图/UML",
    22: "分割线",
    23: "文件",
    24: "分栏",
    25: "分栏列",
    26: "内嵌网页",
    27: "图片",
    28: "开放平台小组件",
    29: "思维笔记",
    30: "电子表格",
    31: "表格",
    32: "表格单元格",
    33: "视图",
    34: "引用容器",
    35: "任务",
    36: "OKR",
    37: "OKR Objective",
    38: "OKR Key Result",
    39: "OKR 进展",
    40: "文档小组件",
    41: "Jira 问题",
    42: "Wiki 子目录",
    43: "画板",
    44: "议程",
    45: "议程项",
    46: "议程项标题",
    47: "议程项内容",
    48: "链接预览",
    49: "源同步块",
    50: "引用同步块",
    51: "Wiki 新版子目录",
    52: "AI 模板",
}


class BlockWrapper:
    """
    Block 包装类 (组合模式)。

    设计意图：
    1. 使用组合避免继承 SDK 类带来的 __getattr__ 冲突。
    2. 使用 __getattr__ 动态转发所有属性访问。
    3. 使用类型注解欺骗 IDE，提供智能提示，不影响运行时转发逻辑。
    """

    def __init__(self, block: Block):
        object.__setattr__(self, "_block", block)

    # 类型注解（不赋值），仅用于 IDE 智能提示
    block_id: Optional[str]
    block_type: Optional[int]
    parent_id: Optional[str]
    children: Optional[List[str]]
    page: Optional[Text]
    text: Optional[Text]
    heading1: Optional[Text]
    heading2: Optional[Text]
    heading3: Optional[Text]
    heading4: Optional[Text]
    heading5: Optional[Text]
    heading6: Optional[Text]
    heading7: Optional[Text]
    heading8: Optional[Text]
    heading9: Optional[Text]
    bullet: Optional[Text]
    ordered: Optional[Text]
    code: Optional[Text]
    quote: Optional[Text]
    equation: Optional[Text]
    todo: Optional[Text]
    bitable: Optional[Bitable]
    callout: Optional[Callout]
    chat_card: Optional[ChatCard]
    diagram: Optional[Diagram]
    divider: Optional[Divider]
    file: Optional[BlockFile]
    grid: Optional[Grid]
    grid_column: Optional[GridColumn]
    iframe: Optional[Iframe]
    image: Optional[Image]
    isv: Optional[Isv]
    add_ons: Optional[AddOns]
    mindnote: Optional[Mindnote]
    sheet: Optional[Sheet]
    table: Optional[Table]
    table_cell: Optional[TableCell]
    view: Optional[View]
    undefined: Optional[Undefined]
    quote_container: Optional[QuoteContainer]
    task: Optional[Task]
    okr: Optional[Okr]
    okr_objective: Optional[OkrObjective]
    okr_key_result: Optional[OkrKeyResult]
    okr_progress: Optional[OkrProgress]
    comment_ids: Optional[List[str]]
    jira_issue: Optional[JiraIssue]
    wiki_catalog: Optional[WikiCatalog]
    board: Optional[Board]
    agenda: Optional[Agenda]
    agenda_item: Optional[AgendaItem]
    agenda_item_title: Optional[AgendaItemTitle]
    agenda_item_content: Optional[AgendaItemContent]
    link_preview: Optional[LinkPreview]
    source_synced: Optional[SourceSynced]
    reference_synced: Optional[ReferenceSynced]
    sub_page_list: Optional[SubPageList]
    ai_template: Optional[AiTemplate]
    reference_base: Optional[ReferenceBase]
    project: Optional[Project]
    meeting_notes_qa: Optional[MeetingNotesQa]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._block, name)

    def _is_text_block(self) -> bool:
        return self.block_type in BLOCK_TYPE_TEXT_ATTR_MAP.keys()

    def get_block_type_str(self) -> str:
        """根据 block_type 返回对应的文本描述"""
        if self.block_type is None:
            return "未知类型"
        return BLOCK_TYPE_TO_STR.get(self.block_type, f"未知类型({self.block_type})")

    def get_text_attr(self) -> Optional[Text]:
        """获取块的 Text 属性"""
        if not self._is_text_block():
            return None

        if not self.block_type:
            return None

        attr_name = BLOCK_TYPE_TEXT_ATTR_MAP[self.block_type]
        return getattr(self._block, attr_name, None)

    def extract_block_content(self) -> str:
        """提取文本块的完整文本内容"""
        if not self._is_text_block():
            return ""

        text_attr = self.get_text_attr()
        if not text_attr:
            return ""
        if not text_attr.elements:
            return ""

        parts = [
            elem.text_run.content
            for elem in text_attr.elements
            if elem.text_run and elem.text_run.content
        ]
        return "".join(parts)

    def extract_comment_ids(self) -> Set[str]:
        """
        从块中提取所有 comment_ids

        当前支持文本类型块 与 图片块
        """
        comment_ids = set()
        if self._is_text_block():
            text_attr = self.get_text_attr()
            if not text_attr:
                return comment_ids
            if not text_attr.elements:
                return comment_ids

            for elem in text_attr.elements:
                if not elem.text_run:
                    continue
                if not elem.text_run.text_element_style:
                    continue
                if not elem.text_run.text_element_style.comment_ids:
                    continue

                comment_ids.update(elem.text_run.text_element_style.comment_ids)

            return comment_ids
        elif self.block_type == BLOCK_IMAGE_TYPE:
            if not self.comment_ids:
                return set()
            comment_ids.update(self.comment_ids)

        return comment_ids


class ListBlocksResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    document_id: str
    total_blocks: int
    items: List[BlockWrapper]

    @field_serializer("items")
    def serialize_items(self, items: List[BlockWrapper]) -> List[dict]:
        return _serialize_wrapper_items(items, "_block")


class BatchUpdateBlocksResult(BaseModel):
    """批量更新块结果"""

    model_config = {"arbitrary_types_allowed": True}

    document_id: str
    client_token: Optional[str]
    revision_id: Optional[int]
    block_count: Optional[int]
    items: List[BlockWrapper]

    @field_serializer("items")
    def serialize_items(self, items: List[BlockWrapper]) -> List[dict]:
        return _serialize_wrapper_items(items, "_block")


class UpdateBlockResult(BaseModel):
    """更新块结果"""

    model_config = {"arbitrary_types_allowed": True}

    document_id: str
    block_id: str
    client_token: Optional[str] = None
    revision_id: Optional[int] = None
    block: Optional[BlockWrapper] = None

    @field_serializer("block")
    def serialize_block(self, block: Optional[BlockWrapper]) -> Optional[dict]:
        if block is None:
            return None
        return _serialize_wrapper_item(block, "_block")
