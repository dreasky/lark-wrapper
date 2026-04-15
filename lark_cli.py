import argparse
import json
import sys
import io
from pathlib import Path
from lark_wrapper import *

MAX_FILE_SIZE = 20 * 1024 * 1024

# === 消息 API ===


def cmd_send_text(args):
    """发送文本消息"""
    wrapper = MessageManageWrapper()
    wrapper.send_message(
        receive_id=args.chat_id,
        message=args.message,
        msg_type="text",
        receive_id_type="chat_id",
    )


def cmd_list_messages(args):
    """获取会话历史消息"""
    wrapper = MessageManageWrapper()
    wrapper.list_messages(
        container_id_type=args.container_id_type,
        container_id=args.container_id,
        start_time=args.start_time,
        end_time=args.end_time,
        sort_type=args.sort_type,
        page_size=args.page_size,
        page_token=args.page_token,
    )


def cmd_get_message_resource(args):
    """获取消息中的资源文件"""
    wrapper = MessageManageWrapper()
    wrapper.get_message_resource(
        message_id=args.message_id,
        file_key=args.file_key,
        type=args.type,
        output_dir=args.output_dir,
    )


def cmd_get_message_content(args):
    """获取指定消息的内容"""
    wrapper = MessageManageWrapper()
    wrapper.get_message_content(
        message_id=args.message_id,
        user_id_type=args.user_id_type,
    )


# === 群组 API ===


def cmd_list_chat(args):
    """获取群列表"""
    wrapper = GroupManageWrapper()
    wrapper.list_chat()


# === 机器人 API ===


def cmd_get_bot_info(args):
    """获取机器人信息"""
    wrapper = RobotWrapper()
    wrapper.get_bot_info()


# === 云文档 API ===


def cmd_root_folder(args):
    """获取根文件夹元数据"""
    wrapper = CloudSpaceWrapper()
    wrapper.root_folder()


def cmd_list_file(args):
    """获取文件夹中的文件清单"""
    wrapper = CloudSpaceWrapper()
    wrapper.list_file()


def cmd_upload_file(args):
    """上传文件并创建导入任务"""
    file_path = Path(args.file_path)

    # 获取文件扩展名（不带.）
    file_extension = file_path.suffix[1:]

    # 文件名（包含扩展名）
    file_name = "del_" + file_path.name

    # 文件类型
    obj_type = args.obj_type

    # 文件大小
    file_size = file_path.stat().st_size

    # 上传素材
    cloud_space_wrapper = CloudSpaceWrapper()
    # 获取机器人云空间根目录信息
    root_folder_result = cloud_space_wrapper.root_folder()
    if file_size < MAX_FILE_SIZE:
        # 上传素材方式上传文件
        extra = json.dumps(
            {"obj_type": obj_type, "file_extension": file_extension},
            ensure_ascii=False,
        )

        upload_media_result = cloud_space_wrapper.upload_all_media(
            file_path, file_name, file_size, extra
        )
        file_token = upload_media_result.file_token

    else:
        # 分片上传
        prepare = cloud_space_wrapper.upload_prepare_file(
            file_name=file_name,
            parent_type="explorer",
            parent_node=root_folder_result.token,
            file_size=file_size,
        )

        with open(file_path, "rb") as f:
            for seq in range(prepare.block_num):
                chunk = f.read(prepare.block_size)  # 最后一片可能不足 block_size
                cloud_space_wrapper.upload_part_file(
                    upload_id=prepare.upload_id,
                    seq=seq,
                    size=len(chunk),  # 实际字节数，不能用 block_size
                    file_part=io.BytesIO(chunk),
                )

        upload_finish_file_result = cloud_space_wrapper.upload_finish_file(
            prepare.upload_id, prepare.block_num
        )
        file_token = upload_finish_file_result.file_token

    # 创建导入任务
    cloud_space_wrapper.create_import_task(
        mount_key=root_folder_result.token,
        file_extension=file_extension,
        file_token=file_token,
        type=obj_type,
        file_name=file_name,
    )
    print("✅ 导入文件完成, 查询导入任务结果可获取文件url链接")


def cmd_get_import_task(args):
    """查询导入任务结果"""
    wrapper = CloudSpaceWrapper()
    wrapper.get_import_task(args.ticket)


def cmd_batch_create_permission_member_custom(args):
    """授权文件"""

    # 获取机器人所在全部群组
    group_manage_wrapper = GroupManageWrapper()
    list_chat = group_manage_wrapper.list_chat()

    # 批量授权
    cloud_auth_wrapper = CloudAuthWrapper()
    cloud_auth_wrapper.batch_create_permission_member(
        member_type="openchat",
        member_id_list=list_chat.get_chat_id_list(),
        perm="full_access",
        perm_type="container",
        type="chat",
        file_type="docx",
        file_token=args.file_token,
    )


def cmd_list_comments(args):
    """获取云文档所有评论"""
    wrapper = CloudSpaceWrapper()
    wrapper.list_comments(
        file_token=args.file_token,
        file_type=args.file_type,
        output_dir=args.output_dir,
        is_whole=args.is_whole,
        is_solved=args.is_solved,
        user_id_type=args.user_id_type,
    )


# === 文档块 API ===


def cmd_list_blocks(args):
    """获取文档所有块（自动分页）"""
    wrapper = CloudDocBlockWrapper()
    wrapper.list_blocks(
        document_id=args.document_id,
        output_dir=args.output_dir,
        document_revision_id=args.document_revision_id,
        user_id_type=args.user_id_type,
    )


def main():
    parser = argparse.ArgumentParser(description="feishu CLI - 飞书命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # === 消息 API ===
    p = subparsers.add_parser("send-text", help="发送文本消息")
    p.add_argument("--chat-id", required=True, help="对话ID")
    p.add_argument("--message", required=True, help="消息文本")

    p = subparsers.add_parser("list-messages", help="获取会话历史消息")
    p.add_argument(
        "--container-id-type", required=True, help="容器类型: chat 或 thread"
    )
    p.add_argument("--container-id", required=True, help="容器ID")
    p.add_argument("--start-time", default=None, help="起始时间（秒级时间戳）")
    p.add_argument("--end-time", default=None, help="结束时间（秒级时间戳）")
    p.add_argument(
        "--sort-type", default="ByCreateTimeAsc", help="排序方式，默认 ByCreateTimeAsc"
    )
    p.add_argument("--page-size", type=int, default=20, help="分页大小，默认20，最大50")
    p.add_argument("--page-token", default=None, help="分页标记")

    p = subparsers.add_parser("get-message-resource", help="获取消息中的资源文件")
    p.add_argument("--message-id", required=True, help="消息ID")
    p.add_argument("--file-key", required=True, help="资源Key")
    p.add_argument("--type", required=True, help="资源类型: image 或 file")
    p.add_argument("--output-dir", required=True, help="文件保存目录")

    p = subparsers.add_parser("get-message-content", help="获取指定消息的内容")
    p.add_argument("--message-id", required=True, help="消息ID")
    p.add_argument(
        "--user-id-type",
        default="open_id",
        help="用户ID类型: open_id / union_id / user_id，默认 open_id",
    )

    # === 群组 API ===
    subparsers.add_parser("list-chat", help="获取用户或机器人所在的群列表")

    # === 机器人 API ===
    subparsers.add_parser("get-bot-info", help="获取机器人信息")

    # === 云文档 API ===
    subparsers.add_parser("root-folder", help="获取我的空间（根文件夹）元数据")

    subparsers.add_parser("list-file", help="获取文件夹中的文件清单")

    p = subparsers.add_parser("upload-file", help="上传文件")
    p.add_argument("--file-path", required=True, help="文件路径")
    p.add_argument("--obj-type", default="docx", help="上传目标类型, 默认docx")

    p = subparsers.add_parser("get-import-task", help="查询导入任务结果")
    p.add_argument("--ticket", required=True, help="任务ticket")

    p = subparsers.add_parser("authorize-file", help="授权文件权限(全量,群组)")
    p.add_argument("--file-token", required=True, help="文件token")

    p = subparsers.add_parser("list-comments", help="获取云文档所有评论")
    p.add_argument("--file-token", required=True, help="云文档token")
    p.add_argument(
        "--file-type",
        required=True,
        help="文档类型: doc / docx / sheet / file / slides",
    )
    p.add_argument("--output-dir", help="保存文件路径")
    p.add_argument("--is-whole", action="store_true", default=None, help="是否全文评论")
    p.add_argument("--is-solved", action="store_true", default=None, help="是否已解决")
    p.add_argument(
        "--user-id-type", default=None, help="用户ID类型: open_id / union_id / user_id"
    )

    # === 文档块 API ===
    p = subparsers.add_parser("list-blocks", help="获取文档所有块（自动分页）")
    p.add_argument("--document-id", required=True, help="文档ID")
    p.add_argument("--output-dir", help="保存文件路径")
    p.add_argument(
        "--document-revision-id", type=int, default=None, help="文档版本，-1表示最新"
    )
    p.add_argument(
        "--user-id-type", default=None, help="用户ID类型: open_id / union_id / user_id"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "send-text": cmd_send_text,
        "list-messages": cmd_list_messages,
        "get-message-resource": cmd_get_message_resource,
        "get-message-content": cmd_get_message_content,
        "list-chat": cmd_list_chat,
        "get-bot-info": cmd_get_bot_info,
        "root-folder": cmd_root_folder,
        "list-file": cmd_list_file,
        "upload-file": cmd_upload_file,
        "get-import-task": cmd_get_import_task,
        "authorize-file": cmd_batch_create_permission_member_custom,
        "list-comments": cmd_list_comments,
        "list-blocks": cmd_list_blocks,
    }

    try:
        cmd_map[args.command](args)
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
