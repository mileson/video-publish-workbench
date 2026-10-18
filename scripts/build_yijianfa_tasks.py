#!/usr/bin/env python3
# # 文件说明书 (File Manual)
# ## 核心功能 (Core Function)
# 将视频预发布工作台的最终评审选择转换为逐平台的一键发 shortVideo 任务，映射 B站单一封面及 YouTube 描述话题与 16:9 封面。
# ## 输入 (Input)
# 接收选择结果 JSON、视频绝对路径、浏览器上下文、发布模式与可选封面搜索目录；旧预期账号参数仅兼容接收。
# ## 输出 (Output)
# 写出所选平台各自的 CLI 任务 JSON 和 handoff-manifest.json；B站优先使用已选 4:3 封面，旧四平台选择仍兼容。
# ## 定位 (Position)
# 位于 video-publish-workbench 的评审到一键发交接层；不直接授权或执行真实发布。
# ## 依赖 (Dependency)
# - references/publish-selection.schema.json：评审选择结构合同。
# - references/yijianfa-handoff-contract.md：平台拆分、封面解析与发布门禁。
# - 一键发 CLI：消费生成的 JSON 任务。
# ## 维护规则 (Maintenance Rules)
# 1. 每次修改代码逻辑后，必须检查并更新上述的【核心功能】、【输入】、【输出】等信息，确保文档与代码一致。
# 2. 禁止修改或删除本【维护规则】章节的内容。
# 3. 修改完成后，必须扫描当前文件所在的文件夹目录，找到对应的 [当前文件夹名称]_README.md 文档，并同步更新该 README 中关于本文件的描述信息。

"""Build validated, per-platform yijianfa tasks from a review selection."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import sys
import uuid
from pathlib import Path
from typing import Any

from extract_first_frame_cover import is_cover_aspect, probe_media_size


SELECTION_VERSION = "social-publish-package.selection.v3"
PLATFORM_CONTRACTS: dict[str, dict[str, Any]] = {
    "xiaohongshu": {"tag_limit": 10, "cover_roles": ("cover",)},
    "douyin": {"tag_limit": 5, "cover_roles": ("cover", "horizontalCover")},
    "kuaishou": {"tag_limit": 4, "cover_roles": ("cover",)},
    "shipinhao": {"tag_limit": 7, "cover_roles": ("cover", "horizontalCover")},
    "bilibili": {"tag_limit": 10, "cover_roles": ("cover", "horizontalCover")},
    "youtube": {"tag_limit": 60, "cover_roles": ("horizontalCover",)},
}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def is_shipinhao_short_title(value: str) -> bool:
    return bool(value) and len(value) <= 16 and all(character.isalnum() or character.isspace() for character in value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _image_mime(path: Path) -> str | None:
    header = path.read_bytes()[:16]
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def _video_mime(path: Path) -> str:
    guessed = mimetypes.guess_type(path.name)[0]
    return guessed if guessed and guessed.startswith("video/") else "video/mp4"


def _validate_local_image(path: Path, cover: dict[str, Any], label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"{label}原始文件不存在：{resolved}")
    if _image_mime(resolved) is None:
        raise ValueError(f"{label}必须是 PNG、JPEG 或 WEBP 图片：{resolved}")
    role = cover.get("role")
    try:
        width, height = probe_media_size(resolved)
        if not is_cover_aspect(resolved, role):
            expected = {"cover": "3:4 竖版", "bilibiliCover": "4:3 B站", "horizontalCover": "16:9 横版"}[role]
            raise ValueError(f"{label}必须接近 {expected}，当前为 {width}x{height}：{resolved}")
    except (FileNotFoundError, RuntimeError) as error:
        raise ValueError(f"{label}无法读取图片尺寸：{error}") from error
    expected_size = cover.get("size")
    if isinstance(expected_size, int) and resolved.stat().st_size != expected_size:
        raise ValueError(f"{label}文件大小与页面选择不一致；标准值为 {expected_size} 字节：{resolved}")
    expected_sha256 = cover.get("sha256")
    if isinstance(expected_sha256, str) and SHA256_RE.fullmatch(expected_sha256):
        actual = _sha256(resolved)
        if actual != expected_sha256:
            raise ValueError(f"{label}SHA-256 与页面选择不一致：{resolved}")
    return resolved


def _search_original_cover(
    cover: dict[str, Any],
    *,
    role: str,
    search_roots: list[Path],
) -> Path:
    label = {"cover": "竖版封面", "bilibiliCover": "B站 4:3 封面", "horizontalCover": "横版封面"}[role]
    if cover.get("role") != role:
        raise ValueError(f"{label}角色错误；标准角色必须是 {role}")

    raw_path = cover.get("path")
    if cover.get("publishable") is True and isinstance(raw_path, str) and raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            raise ValueError(f"{label}已登记路径必须是绝对路径：{raw_path}")
        return _validate_local_image(path, cover, label)

    file_name = cover.get("fileName")
    expected_size = cover.get("size")
    expected_sha256 = cover.get("sha256")
    if not isinstance(file_name, str) or not file_name or Path(file_name).name != file_name:
        raise ValueError(f"{label}缺少有效文件名，无法定位原始文件")
    if not isinstance(expected_size, int) or expected_size < 0:
        raise ValueError(f"{label}缺少文件大小；请刷新新版 HTML 后重新选择封面")
    if expected_sha256 is not None and (
        not isinstance(expected_sha256, str) or not SHA256_RE.fullmatch(expected_sha256)
    ):
        raise ValueError(f"{label}SHA-256 格式无效；标准格式为 64 位小写十六进制")

    candidates: dict[str, Path] = {}
    for raw_root in search_roots:
        root = raw_root.expanduser().resolve()
        if root.is_file():
            paths = [root] if root.name == file_name else []
        elif root.is_dir():
            direct = root / file_name
            paths = [direct] if direct.is_file() else []
            paths.extend(path for path in root.rglob(file_name) if path.is_file() and path != direct)
        else:
            continue
        for path in paths:
            resolved = path.resolve()
            if resolved.stat().st_size != expected_size or _image_mime(resolved) is None:
                continue
            if expected_sha256 and _sha256(resolved) != expected_sha256:
                continue
            candidates[str(resolved)] = resolved

    matches = list(candidates.values())
    if not matches:
        roots = "、".join(str(path.expanduser().resolve()) for path in search_roots)
        raise ValueError(
            f"找不到{label}原始文件 {file_name}；标准要求是在视频目录或 --cover-search-root 指定目录内，"
            f"文件名、大小{('、SHA-256' if expected_sha256 else '')}均与页面选择一致。已搜索：{roots}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"{label}匹配到多个原始文件，请用 --cover-search-root 缩小范围或先登记绝对路径："
            + "、".join(str(path) for path in matches[:8])
        )
    return _validate_local_image(matches[0], cover, label)


def _parse_expected_accounts(values: list[str]) -> dict[str, str]:
    accounts: dict[str, str] = {}
    for value in values:
        platform, separator, account = value.partition("=")
        platform = platform.strip()
        account = account.strip()
        if not separator or platform not in PLATFORM_CONTRACTS or not account:
            raise ValueError("--expected-account 格式必须是 platform=账号，平台限 " + "/".join(PLATFORM_CONTRACTS))
        accounts[platform] = account
    return accounts


def validate_selection(selection: Any, platforms: list[str]) -> None:
    if not isinstance(selection, dict):
        raise ValueError("selection 必须是 JSON 对象")
    if selection.get("schema_version") != SELECTION_VERSION:
        raise ValueError(f"selection.schema_version 必须是 {SELECTION_VERSION}")
    title = selection.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("selection.title 不能为空")
    if len(title) > 16:
        raise ValueError(f"selection.title 为 {len(title)}/16 字；标准上限是 16 字")
    body = selection.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("selection.body 不能为空")
    selected_platforms = selection.get("platforms")
    if not isinstance(selected_platforms, dict):
        raise ValueError("selection.platforms 必须是对象")
    for platform in platforms:
        data = selected_platforms.get(platform)
        if not isinstance(data, dict) or not isinstance(data.get("tags"), list):
            raise ValueError(f"selection.platforms.{platform}.tags 必须是数组")
        platform_title = data.get("title")
        if not isinstance(platform_title, str) or not platform_title.strip():
            raise ValueError(f"selection.platforms.{platform}.title 不能为空")
        if platform == "shipinhao" and not is_shipinhao_short_title(platform_title.strip()):
            raise ValueError("selection.platforms.shipinhao.title 必须不超过 16 字，且只能包含文字、字母、数字和空格")
        tags = data["tags"]
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise ValueError(f"selection.platforms.{platform}.tags 只能包含非空字符串")
        limit = PLATFORM_CONTRACTS[platform]["tag_limit"]
        if len(tags) > limit:
            raise ValueError(f"selection.platforms.{platform}.tags 为 {len(tags)}/{limit} 个；标准上限是 {limit} 个")
    covers = selection.get("covers")
    if not isinstance(covers, dict):
        raise ValueError("selection.covers 必须是对象")
    if not isinstance(covers.get("horizontalCoverEnabled"), bool):
        raise ValueError("selection.covers.horizontalCoverEnabled 必须是布尔值")


def build_tasks(
    selection: dict[str, Any],
    *,
    video_path: Path,
    output_dir: Path,
    browser_context: str,
    mode: str,
    platforms: list[str],
    search_roots: list[Path],
    expected_accounts: dict[str, str],
) -> dict[str, Any]:
    if browser_context not in {"regular", "incognito"}:
        raise ValueError("browser_context 必须显式指定为 regular 或 incognito")
    if mode not in {"fill", "publish"}:
        raise ValueError("mode 必须是 fill 或 publish")
    invalid_platforms = [platform for platform in platforms if platform not in PLATFORM_CONTRACTS]
    if invalid_platforms:
        raise ValueError(f"不支持的平台：{', '.join(invalid_platforms)}")
    validate_selection(selection, platforms)

    video = video_path.expanduser().resolve()
    if not video.is_file():
        raise ValueError(f"视频文件不存在：{video}")
    roots = [video.parent, *search_roots]
    unique_roots = list(dict.fromkeys(path.expanduser().resolve() for path in roots))
    covers = selection["covers"]
    bilibili_data = covers.get("bilibiliCover")
    bilibili_cover = _search_original_cover(
        bilibili_data, role="bilibiliCover", search_roots=unique_roots,
    ) if any(platform in platforms for platform in ("bilibili", "douyin")) and isinstance(bilibili_data, dict) else None
    if "douyin" in platforms and bilibili_cover is None:
        raise ValueError("抖音必须同时提供 3:4 竖版与 4:3 横版封面；请在抖音/B站 4:3 槽选择图片")
    vertical_data = covers.get("verticalCover")
    needs_vertical = any(platform != "youtube" for platform in platforms)
    if needs_vertical and not isinstance(vertical_data, dict):
        raise ValueError("selection.covers.verticalCover 不能为空；清空竖版时应由 HTML 返回第一帧回退文件")
    vertical = _search_original_cover(vertical_data, role="cover", search_roots=unique_roots) if needs_vertical else None
    horizontal_data = covers.get("horizontalCover")
    horizontal_enabled = covers["horizontalCoverEnabled"]
    if horizontal_enabled and not isinstance(horizontal_data, dict):
        raise ValueError("已启用横版封面，但 selection.covers.horizontalCover 为空")
    if not horizontal_enabled and isinstance(horizontal_data, dict):
        raise ValueError("横版封面未显式启用，不得下发 horizontalCover")
    horizontal = _search_original_cover(
        horizontal_data,
        role="horizontalCover",
        search_roots=unique_roots,
    ) if horizontal_enabled else None

    if "youtube" in platforms and horizontal is None:
        raise ValueError("YouTube requires an enabled 16:9 horizontalCover")

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    task_entries = []
    for platform in platforms:
        platform_data = selection["platforms"][platform]
        data: dict[str, Any] = {
            "title": platform_data["title"].strip(),
            "description": selection["body"].strip(),
            "content": selection["body"].strip(),
            "tags": [tag.strip().lstrip("#") for tag in platform_data["tags"]],
        }
        if platform == "youtube":
            hashtags = " ".join(f"#{tag}" for tag in dict.fromkeys(data["tags"]))
            description = data["description"] + ("\n\n" + hashtags if hashtags else "")
            data.update(description=description, content=description, tags=[])
        if mode == "publish":
            data["publishGuard"] = {
                "version": 1,
                "expectedTargets": {},
                "requirePublicUrl": True,
            }
        assets = [{"path": str(video), "role": "media", "type": _video_mime(video)}]
        if platform == "youtube":
            assets.append({"path": str(horizontal), "role": "horizontalCover", "type": _image_mime(horizontal)})
        elif platform == "douyin":
            assets.append({"path": str(vertical), "role": "cover", "type": _image_mime(vertical)})
            assets.append({"path": str(bilibili_cover), "role": "horizontalCover", "type": _image_mime(bilibili_cover)})
        elif platform == "bilibili" and (bilibili_cover is not None or horizontal is not None):
            chosen = bilibili_cover or horizontal
            assets.append({"path": str(chosen), "role": "horizontalCover", "type": _image_mime(chosen)})
        else:
            assets.append({"path": str(vertical), "role": "cover", "type": _image_mime(vertical)})
            if horizontal is not None and "horizontalCover" in PLATFORM_CONTRACTS[platform]["cover_roles"]:
                assets.append({"path": str(horizontal), "role": "horizontalCover", "type": _image_mime(horizontal)})
        task = {
            "requestId": str(uuid.uuid4()),
            "browserContext": browser_context,
            "type": "shortVideo",
            "platforms": [platform],
            "data": data,
            "assets": assets,
        }
        task_path = output_dir / f"yijianfa-{platform}.json"
        task_path.write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        execute_command = "publish" if mode == "publish" else "fill"
        execute_argv = ["yijianfa", execute_command]
        if mode == "publish":
            execute_argv.append("--yes")
        execute_argv.extend(["--browser-context", browser_context, "--input", str(task_path)])
        task_entries.append(
            {
                "platform": platform,
                "task": str(task_path),
                "cover_roles": [asset["role"] for asset in assets if asset["role"] != "media"],
                "prepare_argv": [
                    "yijianfa", "prepare", "--browser-context", browser_context, "--input", str(task_path),
                ],
                "execute_argv": execute_argv,
            }
        )

    manifest = {
        "schema_version": "social-publish-package.yijianfa-handoff.v1",
        "mode": mode,
        "browser_context": browser_context,
        "video": str(video),
        "resolved_covers": {
            "cover": str(vertical) if vertical else None,
            "bilibiliCover": str(bilibili_cover) if bilibili_cover else None,
            "horizontalCover": str(horizontal) if horizontal else None,
            "horizontalCoverEnabled": horizontal_enabled,
        },
        "tasks": task_entries,
    }
    manifest_path = output_dir / "handoff-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "manifest": str(manifest_path), **manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description="把视频预发布评审结果转换为逐平台一键发任务")
    parser.add_argument("--selection", required=True, type=Path, help="window.getPublishReviewSelection() 导出的 JSON")
    parser.add_argument("--video", required=True, type=Path, help="视频绝对路径")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--browser-context", required=True, choices=["regular", "incognito"])
    parser.add_argument("--mode", choices=["fill", "publish"], default="fill")
    parser.add_argument("--platform", action="append", choices=list(PLATFORM_CONTRACTS), default=[])
    parser.add_argument("--cover-search-root", action="append", type=Path, default=[])
    parser.add_argument("--expected-account", action="append", default=[], help="兼容旧调用；当前 CLI 忽略账号名称，不用于验真")
    args = parser.parse_args()

    try:
        selection = json.loads(args.selection.read_text(encoding="utf-8"))
        available = selection.get("platforms") if isinstance(selection, dict) else {}
        platforms = args.platform or [platform for platform in PLATFORM_CONTRACTS if platform in available]
        result = build_tasks(
            selection,
            video_path=args.video,
            output_dir=args.output_dir,
            browser_context=args.browser_context,
            mode=args.mode,
            platforms=platforms,
            search_roots=args.cover_search_root,
            expected_accounts=_parse_expected_accounts(args.expected_account),
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
