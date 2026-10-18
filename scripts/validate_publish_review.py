#!/usr/bin/env python3
# # 文件说明书 (File Manual)
# ## 核心功能 (Core Function)
# 支持通用新版工作台：正文版本与选择校验；构建时生成视频真实帧缩略图并注入通用模板。
# 校验视频预发布 JSON 的字段、平台合同、标题数量、标签容量、视频与三种比例封面文件状态。
# ## 输入 (Input)
# 接收 review-payload.schema.json 约定的 JSON 对象、可选视频/封面路径与超限演示开关。
# ## 输出 (Output)
# 返回 errors/warnings；命令行模式输出 JSON 校验报告并以退出码区分通过或失败。
# ## 定位 (Position)
# 位于 video-publish-workbench 的确定性门禁层，供 AI 写完数据后和 HTML 构建前调用。
# ## 依赖 (Dependency)
# - references/review-payload.schema.json：结构合同。
# - references/platform-copy-contract.md：固定平台模式与容量。
# ## 维护规则 (Maintenance Rules)
# 1. 每次修改代码逻辑后，必须检查并更新上述的【核心功能】、【输入】、【输出】等信息，确保文档与代码一致。
# 2. 禁止修改或删除本【维护规则】章节的内容。
# 3. 修改完成后，必须扫描当前文件所在的文件夹目录，找到对应的 [当前文件夹名称]_README.md 文档，并同步更新该 README 中关于本文件的描述信息。

"""Validate structured input for the video pre-publish review builder."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from extract_first_frame_cover import is_cover_aspect, probe_media_size


SCHEMA_VERSION = "social-publish-package.v1"
PLATFORM_CONTRACTS: dict[str, dict[str, Any]] = {
    "xiaohongshu": {"name": "小红书", "mode": "separate", "tag_limit": 10},
    "douyin": {"name": "抖音", "mode": "separate", "tag_limit": 5},
    "kuaishou": {"name": "快手", "mode": "combined", "tag_limit": 4},
    "shipinhao": {"name": "视频号", "mode": "combined", "tag_limit": 7},
    "bilibili": {"name": "B 站", "mode": "separate", "tag_limit": 10},
    "youtube": {"name": "YouTube", "mode": "separate", "tag_limit": 60},
}
CORE_REQUIRED_PLATFORMS = {"xiaohongshu", "douyin", "kuaishou", "shipinhao"}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _looks_like_image(path: Path) -> bool:
    try:
        header = path.read_bytes()[:16]
    except OSError:
        return False
    return (
        header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith(b"\xff\xd8\xff")
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
    )


def add_cover_candidates(
    payload: dict[str, Any],
    paths: list[Path],
    *,
    role: str = "cover",
) -> dict[str, Any]:
    """Return a copied payload with stable CLI-provided cover candidates appended."""

    result = copy.deepcopy(payload)
    video = result.setdefault("video", {})
    candidates = video.setdefault("cover_candidates", [])
    existing_paths = {str(Path(item.get("path", "")).expanduser()) for item in candidates if isinstance(item, dict)}
    for raw_path in paths:
        path = raw_path.expanduser().resolve()
        if str(path) in existing_paths:
            continue
        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
        candidates.append(
            {
                "id": f"cover-{digest}",
                "label": path.stem,
                "path": str(path),
                "role": role,
                "source": "provided",
            }
        )
        existing_paths.add(str(path))
    video.setdefault("fallback_cover", "first_frame")
    selected_ids = video.setdefault("selected_cover_ids", {})
    if role == "cover" and role not in selected_ids:
        first_for_role = next((candidate for candidate in candidates if candidate.get("role") == role), None)
        selected_ids[role] = first_for_role.get("id") if first_for_role else None
    elif role in {"bilibiliCover", "horizontalCover"}:
        selected_ids.setdefault(role, None)
    return result


def validate_payload(
    payload: Any,
    *,
    video_path: Path | None = None,
    allow_overlimit_demo: bool = False,
) -> tuple[list[str], list[str]]:
    """Return deterministic validation errors and warnings."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return ["payload 必须是 JSON 对象"], warnings

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version 必须是 {SCHEMA_VERSION}")

    if video_path is not None:
        if not video_path.is_absolute():
            errors.append("video 路径必须是绝对路径")
        elif not video_path.is_file():
            errors.append(f"video 文件不存在：{video_path}")

    video = payload.get("video")
    if not isinstance(video, dict):
        errors.append("video 必须是对象")
    else:
        if not _text(video.get("display_title")):
            errors.append("video.display_title 不能为空")
        if not _text(video.get("core_viewpoint")):
            errors.append("video.core_viewpoint 不能为空")
        if video.get("fallback_cover", "first_frame") != "first_frame":
            errors.append("video.fallback_cover 必须是 first_frame")
        cover_candidates = video.get("cover_candidates", [])
        if not isinstance(cover_candidates, list):
            errors.append("video.cover_candidates 必须是数组")
            cover_candidates = []
        cover_ids: set[str] = set()
        cover_names: set[str] = set()
        for index, candidate in enumerate(cover_candidates):
            prefix = f"video.cover_candidates[{index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            cover_id = _text(candidate.get("id"))
            label = _text(candidate.get("label"))
            raw_path = _text(candidate.get("path"))
            if not cover_id:
                errors.append(f"{prefix}.id 不能为空")
            elif cover_id in cover_ids:
                errors.append(f"{prefix}.id 重复：{cover_id}")
            cover_ids.add(cover_id)
            if not label:
                errors.append(f"{prefix}.label 不能为空")
            if candidate.get("role") not in {"cover", "bilibiliCover", "horizontalCover"}:
                errors.append(f"{prefix}.role 必须是 cover、bilibiliCover 或 horizontalCover")
            if candidate.get("source") not in {"provided", "discovered", "first_frame"}:
                errors.append(f"{prefix}.source 必须是 provided、discovered 或 first_frame")
            if not raw_path:
                errors.append(f"{prefix}.path 不能为空")
                continue
            cover_path = Path(raw_path).expanduser()
            if not cover_path.is_absolute():
                errors.append(f"{prefix}.path 必须是绝对路径")
            elif not cover_path.is_file():
                errors.append(f"{prefix}.path 文件不存在：{cover_path}")
            elif not _looks_like_image(cover_path):
                errors.append(f"{prefix}.path 必须是 PNG、JPEG 或 WEBP 图片")
            else:
                try:
                    width, height = probe_media_size(cover_path)
                    if not is_cover_aspect(cover_path, candidate.get("role")):
                        expected = {"cover": "3:4 竖版", "bilibiliCover": "4:3 B站", "horizontalCover": "16:9 横版"}.get(candidate.get("role"), "有效封面比例")
                        errors.append(f"{prefix}.path 必须接近 {expected}，当前为 {width}x{height}")
                except (FileNotFoundError, RuntimeError) as error:
                    errors.append(f"{prefix}.path 无法读取图片尺寸：{error}")
            file_name = cover_path.name.casefold()
            if file_name in cover_names:
                errors.append(f"{prefix}.path 文件名重复，无法稳定匹配拖入文件：{cover_path.name}")
            cover_names.add(file_name)
        selected_cover_ids = video.get("selected_cover_ids", {})
        if not isinstance(selected_cover_ids, dict):
            errors.append("video.selected_cover_ids 必须是对象")
        else:
            allowed_selected_keys = {"cover", "bilibiliCover", "horizontalCover"}
            extra_selected_keys = sorted(set(selected_cover_ids) - allowed_selected_keys)
            if extra_selected_keys:
                errors.append(f"video.selected_cover_ids 只允许 cover、bilibiliCover 和 horizontalCover，收到：{', '.join(extra_selected_keys)}")
            candidates_by_id = {
                candidate.get("id"): candidate
                for candidate in cover_candidates
                if isinstance(candidate, dict) and _text(candidate.get("id"))
            }
            for role in sorted(allowed_selected_keys):
                selected_id = selected_cover_ids.get(role)
                if selected_id is None:
                    continue
                candidate = candidates_by_id.get(selected_id)
                if candidate is None:
                    errors.append(f"video.selected_cover_ids.{role} 必须指向现有封面候选")
                elif candidate.get("role") != role:
                    errors.append(
                        f"video.selected_cover_ids.{role} 指向了 {candidate.get('role')} 候选；标准角色必须是 {role}"
                    )

    content = payload.get("content")
    if not isinstance(content, dict):
        errors.append("content 必须是对象")
        content = {}

    titles = content.get("titles")
    if not isinstance(titles, list) or len(titles) != 5:
        errors.append("content.titles 必须恰好包含 5 个候选")
        titles = titles if isinstance(titles, list) else []

    title_limit = content.get("title_limit", 16)
    if not isinstance(title_limit, int) or title_limit <= 0:
        errors.append("content.title_limit 必须是正整数")
        title_limit = 16

    seen_titles: set[str] = set()
    for index, item in enumerate(titles):
        prefix = f"content.titles[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} 必须是对象")
            continue
        title = _text(item.get("text"))
        if not title:
            errors.append(f"{prefix}.text 不能为空")
            continue
        if title in seen_titles:
            errors.append(f"{prefix}.text 与其他候选重复")
        seen_titles.add(title)
        if not _text(item.get("note")):
            errors.append(f"{prefix}.note 不能为空")
        if len(title) > title_limit:
            message = f"{prefix}.text 为 {len(title)}/{title_limit} 字"
            if allow_overlimit_demo:
                warnings.append(f"超限演示：{message}")
            else:
                errors.append(f"标题超限：{message}")

    selected_title = content.get("selected_title", 0)
    if not isinstance(selected_title, int) or not 0 <= selected_title < len(titles):
        errors.append("content.selected_title 必须指向现有标题候选")
    variants = content.get("body_variants")
    if variants is not None:
        if not isinstance(variants, list) or not variants:
            errors.append("content.body_variants 必须为非空数组")
        else:
            for variant in variants:
                if not isinstance(variant, dict) or not _text(variant.get("label")) or not _text(variant.get("text")):
                    errors.append("正文版本必须包含非空 label 和 text")
            selected_body = content.get("selected_body", 0)
            if type(selected_body) is not int or not 0 <= selected_body < len(variants):
                errors.append("content.selected_body 必须指向现有正文版本")
    elif content.get("selected_body", 0) != 0:
        errors.append("无正文版本时 selected_body 必须为 0")
    if not _text(content.get("body")):
        errors.append("content.body 不能为空")

    platforms = payload.get("platforms")
    if not isinstance(platforms, dict):
        errors.append("platforms 必须是对象")
        platforms = {}

    missing = sorted(CORE_REQUIRED_PLATFORMS - set(platforms))
    extra = sorted(set(platforms) - set(PLATFORM_CONTRACTS))
    if missing:
        errors.append(f"platforms 缺少：{', '.join(missing)}")
    if extra:
        errors.append(f"platforms 包含未支持项：{', '.join(extra)}")

    for platform_id, contract in PLATFORM_CONTRACTS.items():
        platform = platforms.get(platform_id)
        if not isinstance(platform, dict):
            continue
        prefix = f"platforms.{platform_id}"
        if platform.get("mode") != contract["mode"]:
            errors.append(f"{prefix}.mode 必须是 {contract['mode']}")
        if platform.get("tag_limit") != contract["tag_limit"]:
            errors.append(f"{prefix}.tag_limit 必须是 {contract['tag_limit']}")
        if _text(platform.get("name")) != contract["name"]:
            errors.append(f"{prefix}.name 必须是 {contract['name']}")

        tags = platform.get("tags")
        if not isinstance(tags, list):
            errors.append(f"{prefix}.tags 必须是数组")
            continue
        seen_tags: set[str] = set()
        selected_count = 0
        for index, tag in enumerate(tags):
            tag_prefix = f"{prefix}.tags[{index}]"
            if not isinstance(tag, dict):
                errors.append(f"{tag_prefix} 必须是对象")
                continue
            name = _text(tag.get("name")).lstrip("#").strip()
            if not name:
                errors.append(f"{tag_prefix}.name 不能为空")
            key = name.casefold()
            if key in seen_tags:
                errors.append(f"{tag_prefix}.name 重复：{name}")
            seen_tags.add(key)
            if tag.get("kind") not in {"preset", "ai"}:
                errors.append(f"{tag_prefix}.kind 必须是 preset 或 ai")
            if not isinstance(tag.get("selected"), bool):
                errors.append(f"{tag_prefix}.selected 必须是布尔值")
            elif tag["selected"]:
                selected_count += 1
            if not _text(tag.get("reason")):
                errors.append(f"{tag_prefix}.reason 不能为空")
            if tag.get("eligible") is False:
                errors.append(f"{tag_prefix} 未通过场景门禁，不得进入 HTML")

        if selected_count > contract["tag_limit"]:
            message = f"{prefix} 已选 {selected_count}/{contract['tag_limit']} 个标签"
            if allow_overlimit_demo:
                warnings.append(f"超限演示：{message}")
            else:
                errors.append(f"标签超限：{message}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="校验视频预发布 JSON")
    parser.add_argument("--input", required=True, type=Path, help="review-input.json 路径")
    parser.add_argument("--video", type=Path, help="待预览视频的绝对路径")
    parser.add_argument("--cover-candidate", action="append", default=[], type=Path)
    parser.add_argument("--bilibili-cover-candidate", action="append", default=[], type=Path)
    parser.add_argument("--horizontal-cover-candidate", action="append", default=[], type=Path)
    parser.add_argument("--allow-overlimit-demo", action="store_true")
    args = parser.parse_args()

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "errors": [str(error)], "warnings": []}, ensure_ascii=False))
        return 1

    payload = add_cover_candidates(payload, args.cover_candidate, role="cover")
    payload = add_cover_candidates(payload, args.bilibili_cover_candidate, role="bilibiliCover")
    payload = add_cover_candidates(payload, args.horizontal_cover_candidate, role="horizontalCover")
    errors, warnings = validate_payload(
        payload,
        video_path=args.video,
        allow_overlimit_demo=args.allow_overlimit_demo,
    )
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
