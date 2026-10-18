#!/usr/bin/env python3
# # 文件说明书 (File Manual)
# ## 核心功能 (Core Function)
# 使用 FFmpeg 从视频第一帧生成稳定的 3:4 竖版本地封面文件，并校验 3:4、4:3、16:9 封面比例。
# ## 输入 (Input)
# 接收存在的本地视频路径、目标图片路径和可选 FFmpeg/FFprobe 可执行文件路径。
# ## 输出 (Output)
# 写出居中裁切的 3:4 JPEG/PNG 第一帧图片；失败时抛出包含命令错误的异常，不静默回退平台默认行为。
# ## 定位 (Position)
# 位于 video-publish-workbench 的媒体准备层，由 build_publish_review.py 在无封面候选时调用。
# ## 依赖 (Dependency)
# - FFmpeg：执行单帧解码。
# - build_publish_review.py：决定何时生成第一帧封面。
# ## 维护规则 (Maintenance Rules)
# 1. 每次修改代码逻辑后，必须检查并更新上述的【核心功能】、【输入】、【输出】等信息，确保文档与代码一致。
# 2. 禁止修改或删除本【维护规则】章节的内容。
# 3. 修改完成后，必须扫描当前文件所在的文件夹目录，找到对应的 [当前文件夹名称]_README.md 文档，并同步更新该 README 中关于本文件的描述信息。

"""Extract a deterministic 3:4 first-frame cover image with FFmpeg."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def resolve_ffmpeg(explicit: str | None = None) -> str:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            return str(path)
        raise FileNotFoundError(f"FFmpeg 不存在：{path}")
    discovered = shutil.which("ffmpeg")
    if discovered:
        return discovered
    local = Path.home() / ".local" / "bin" / "ffmpeg"
    if local.is_file():
        return str(local)
    raise FileNotFoundError("未找到 FFmpeg；无法生成第一帧封面")


def resolve_ffprobe(explicit: str | None = None) -> str:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            return str(path)
        raise FileNotFoundError(f"FFprobe 不存在：{path}")
    discovered = shutil.which("ffprobe")
    if discovered:
        return discovered
    ffmpeg = Path(resolve_ffmpeg())
    sibling = ffmpeg.with_name("ffprobe")
    if sibling.is_file():
        return str(sibling)
    raise FileNotFoundError("未找到 FFprobe；无法读取媒体尺寸")


def probe_media_size(path: Path, *, ffprobe: str | None = None) -> tuple[int, int]:
    path = path.expanduser().resolve()
    command = [
        resolve_ffprobe(ffprobe),
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"媒体尺寸读取失败：{completed.stderr.strip() or path}")
    try:
        payload = json.loads(completed.stdout)
        stream = payload["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(f"媒体尺寸读取失败：{path}") from error
    if width <= 0 or height <= 0:
        raise RuntimeError(f"媒体尺寸无效：{width}x{height}")
    return width, height


def is_cover_aspect(path: Path, role: str, *, tolerance: float = 0.02) -> bool:
    width, height = probe_media_size(path)
    targets = {"cover": 3 / 4, "bilibiliCover": 4 / 3, "horizontalCover": 16 / 9}
    if role not in targets:
        return False
    target = targets[role]
    return abs(width / height - target) <= tolerance


def extract_first_frame(
    video_path: Path,
    output_path: Path,
    *,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
) -> Path:
    video_path = video_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"视频文件不存在：{video_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = probe_media_size(video_path, ffprobe=ffprobe)
    if width / height >= 3 / 4:
        crop_height = height - (height % 2)
        crop_width = int(crop_height * 3 / 4)
        crop_width -= crop_width % 2
        crop_x = max(0, (width - crop_width) // 2)
        crop_y = max(0, (height - crop_height) // 2)
    else:
        crop_width = width - (width % 2)
        crop_height = int(crop_width * 4 / 3)
        crop_height -= crop_height % 2
        crop_x = max(0, (width - crop_width) // 2)
        crop_y = max(0, (height - crop_height) // 2)
    command = [
        resolve_ffmpeg(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y}",
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0 or not output_path.is_file() or output_path.stat().st_size == 0:
        message = completed.stderr.strip() or "FFmpeg 没有生成输出文件"
        raise RuntimeError(f"第一帧封面生成失败：{message}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="提取视频第一帧封面")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    args = parser.parse_args()
    try:
        result = extract_first_frame(args.video, args.output, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    except (FileNotFoundError, RuntimeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "output": str(result)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
