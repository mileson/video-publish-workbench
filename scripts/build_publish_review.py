#!/usr/bin/env python3
# # 文件说明书 (File Manual)
# ## 核心功能 (Core Function)
# 支持通用新版工作台：正文版本与选择校验；构建时生成视频真实帧缩略图并注入通用模板。
# 将已校验的视频发布 JSON、视频/封面文件和平台图标注入 HTML 模板，生成单文件预发布工作台。
# ## 输入 (Input)
# 接收 review-input.json、绝对视频路径、可选 3:4/4:3/16:9 封面候选、输出路径和超限演示开关。
# ## 输出 (Output)
# 写出包含交互逻辑、Base64 平台 Logo、本地视频 URI 与稳定封面路径的单文件 HTML，并输出机器可读摘要。
# ## 定位 (Position)
# 位于 video-publish-workbench 的确定性构建层；AI 生成数据，本脚本只校验、转义和渲染。
# ## 依赖 (Dependency)
# - validate_publish_review.py：输入与封面候选门禁。
# - extract_first_frame_cover.py：无自定义竖版封面时生成 3:4 第一帧回退资产。
# - templates/publish-review.html：视觉与交互模板。
# - assets/platform-icons/*.png：平台 Logo。
# ## 维护规则 (Maintenance Rules)
# 1. 每次修改代码逻辑后，必须检查并更新上述的【核心功能】、【输入】、【输出】等信息，确保文档与代码一致。
# 2. 禁止修改或删除本【维护规则】章节的内容。
# 3. 修改完成后，必须扫描当前文件所在的文件夹目录，找到对应的 [当前文件夹名称]_README.md 文档，并同步更新该 README 中关于本文件的描述信息。

"""Build a portable video pre-publish review HTML from structured JSON."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import sys
import subprocess
from pathlib import Path
from typing import Any

from extract_first_frame_cover import extract_first_frame, resolve_ffmpeg
from validate_publish_review import PLATFORM_CONTRACTS, add_cover_candidates, validate_payload


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = SKILL_ROOT / "templates" / "publish-review.html"
ICON_DIR = SKILL_ROOT / "assets" / "platform-icons"
PLACEHOLDERS = {
    "__VIDEO_URL__",
    "__VIDEO_TITLE__",
    "__VIDEO_POSTER__",
    "__VIDEO_PATH_JSON__",
    "__STORAGE_KEY__",
    "__PLATFORM_ICONS_JSON__",
    "__REVIEW_DATA_JSON__",
}


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def _icon_data_uri(platform_id: str) -> str:
    path = ICON_DIR / f"{platform_id}.png"
    if path.is_file():
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    label = "B" if platform_id == "bilibili" else platform_id[:1].upper()
    background = "#00AEEC" if platform_id == "bilibili" else "#6B7280"
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="14" fill="{background}"/>'
        f'<text x="32" y="42" text-anchor="middle" font-family="Arial,sans-serif" font-size="34" '
        f'font-weight="700" fill="white">{html.escape(label)}</text></svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _prepare_cover_data(
    payload: dict[str, Any],
    *,
    video_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    video = payload["video"]
    candidates = list(video.get("cover_candidates") or [])
    fallback_path = output_path.with_name(f"{output_path.stem}_vertical-first-frame-cover.jpg")
    extract_first_frame(video_path, fallback_path)
    selected_ids = dict(video.get("selected_cover_ids") or {})
    if "cover" not in selected_ids:
        first_vertical = next((candidate for candidate in candidates if candidate.get("role") == "cover"), None)
        selected_ids["cover"] = first_vertical.get("id") if first_vertical else None
    selected_ids.setdefault("horizontalCover", None)
    selected_ids.setdefault("bilibiliCover", None)
    prepared = []
    for candidate in candidates:
        path = Path(candidate["path"]).expanduser().resolve()
        prepared.append(
            {
                **candidate,
                "path": str(path),
                "fileName": path.name,
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "previewUrl": path.as_uri(),
                "publishable": True,
            }
        )
    fallback_cover = {
        "id": "first-frame",
        "label": "视频第一帧",
        "path": str(fallback_path.resolve()),
        "fileName": fallback_path.name,
        "size": fallback_path.stat().st_size,
        "sha256": hashlib.sha256(fallback_path.read_bytes()).hexdigest(),
        "role": "cover",
        "source": "first_frame",
        "previewUrl": fallback_path.resolve().as_uri(),
        "publishable": True,
    }
    return {
        "candidates": prepared,
        "selectedCoverIds": selected_ids,
        "horizontalCoverEnabled": bool(selected_ids.get("horizontalCover")),
        "fallbackCover": fallback_cover,
    }


def normalized_review_data(payload: dict[str, Any], covers: dict[str, Any]) -> dict[str, Any]:
    """Project the validated payload into the exact data shape consumed by the template."""

    content = payload["content"]
    platforms: dict[str, Any] = {}
    for platform_id in PLATFORM_CONTRACTS:
        if platform_id not in payload["platforms"]:
            continue
        platform = payload["platforms"][platform_id]
        platforms[platform_id] = {
            "name": platform["name"],
            "mode": platform["mode"],
            "tagLimit": platform["tag_limit"],
            "tags": [
                {
                    "name": str(tag["name"]).lstrip("#").strip(),
                    "kind": "preset" if tag["kind"] == "preset" else "content",
                    "selected": tag["selected"],
                    "reason": tag["reason"],
                    **({"source": tag["source_url"]} if tag.get("source_url") else {}),
                }
                for tag in platform["tags"]
            ],
        }
    return {
        "selectedTitle": content.get("selected_title", 0),
        "titles": content["titles"],
        "body": content["body"],
        "bodyVariants": content.get("body_variants") or [{"label": "正文", "text": content["body"]}],
        "selectedBody": content.get("selected_body", 0),
        "platforms": platforms,
        "covers": covers,
    }


def build_html(
    payload: dict[str, Any],
    *,
    video_path: Path,
    output_path: Path,
    allow_overlimit_demo: bool = False,
    cover_candidates: list[Path] | None = None,
    bilibili_cover_candidates: list[Path] | None = None,
    horizontal_cover_candidates: list[Path] | None = None,
) -> dict[str, Any]:
    payload = add_cover_candidates(payload, cover_candidates or [], role="cover")
    payload = add_cover_candidates(payload, bilibili_cover_candidates or [], role="bilibiliCover")
    payload = add_cover_candidates(payload, horizontal_cover_candidates or [], role="horizontalCover")
    errors, warnings = validate_payload(
        payload,
        video_path=video_path,
        allow_overlimit_demo=allow_overlimit_demo,
    )
    if errors:
        raise ValueError("\n".join(errors))

    covers = _prepare_cover_data(payload, video_path=video_path, output_path=output_path)
    review_data = normalized_review_data(payload, covers)
    icons = {platform_id: _icon_data_uri(platform_id) for platform_id in review_data["platforms"]}
    digest_source = _json_for_script(review_data) + str(video_path.resolve())
    storage_key = f"social-publish-package-{hashlib.sha256(digest_source.encode('utf-8')).hexdigest()[:16]}"

    poster_path = output_path.with_name(f"{output_path.stem}_video-preview.jpg")
    subprocess.run([resolve_ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", str(video_path.resolve()),
                    "-frames:v", "1", "-vf", "scale=640:-2", "-threads", "1", "-y", str(poster_path)],
                   check=True, capture_output=True)
    poster_uri = "data:image/jpeg;base64," + base64.b64encode(poster_path.read_bytes()).decode("ascii")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "__VIDEO_URL__": html.escape(video_path.resolve().as_uri(), quote=True),
        "__VIDEO_TITLE__": html.escape(payload["video"]["display_title"], quote=True),
        "__VIDEO_POSTER__": poster_uri,
        "__VIDEO_PATH_JSON__": _json_for_script(str(video_path.resolve())),
        "__STORAGE_KEY__": storage_key,
        "__PLATFORM_ICONS_JSON__": _json_for_script(icons),
        "__REVIEW_DATA_JSON__": _json_for_script(review_data),
    }
    rendered = template
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    unresolved = sorted(marker for marker in PLACEHOLDERS if marker in rendered)
    if unresolved:
        raise ValueError(f"模板仍含未替换占位符：{', '.join(unresolved)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return {
        "ok": True,
        "output": str(output_path.resolve()),
        "storage_key": storage_key,
        "title_count": len(review_data["titles"]),
        "platforms": list(review_data["platforms"]),
        "cover_count": len(covers["candidates"]),
        "selected_cover_ids": covers["selectedCoverIds"],
        "resolved_vertical_cover_path": next(
            (
                candidate["path"]
                for candidate in covers["candidates"]
                if candidate["id"] == covers["selectedCoverIds"].get("cover")
            ),
            covers["fallbackCover"]["path"],
        ),
        "bilibili_cover_path": next(
            (
                candidate["path"]
                for candidate in covers["candidates"]
                if candidate["id"] == covers["selectedCoverIds"].get("bilibiliCover")
            ),
            None,
        ),
        "horizontal_cover_path": next(
            (
                candidate["path"]
                for candidate in covers["candidates"]
                if candidate["id"] == covers["selectedCoverIds"].get("horizontalCover")
            ),
            None,
        ),
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成视频预发布工作台 HTML")
    parser.add_argument("--input", required=True, type=Path, help="review-input.json 路径")
    parser.add_argument("--video", required=True, type=Path, help="待预览视频绝对路径")
    parser.add_argument("--cover-candidate", action="append", default=[], type=Path, help="可重复传入竖版封面候选")
    parser.add_argument("--bilibili-cover-candidate", action="append", default=[], type=Path, help="可重复传入 B站 4:3 封面候选")
    parser.add_argument("--horizontal-cover-candidate", action="append", default=[], type=Path, help="可重复传入横版封面候选")
    parser.add_argument("--output", required=True, type=Path, help="输出 HTML 路径")
    parser.add_argument("--allow-overlimit-demo", action="store_true")
    args = parser.parse_args()

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = build_html(
            payload,
            video_path=args.video,
            output_path=args.output,
            allow_overlimit_demo=args.allow_overlimit_demo,
            cover_candidates=args.cover_candidate,
            bilibili_cover_candidates=args.bilibili_cover_candidate,
            horizontal_cover_candidates=args.horizontal_cover_candidate,
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
