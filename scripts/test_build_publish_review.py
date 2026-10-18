#!/usr/bin/env python3
# # 文件说明书 (File Manual)
# ## 核心功能 (Core Function)
# 回归验证六平台视频预发布 JSON 校验、旧四/五平台兼容、3:4/4:3/16:9 三封面槽、第一帧回退、HTML 构建、Logo 内嵌与超限门禁。
# ## 输入 (Input)
# 读取 examples/opc-fde-review-input.json，并在临时目录创建占位视频、封面和构建产物。
# ## 输出 (Output)
# 通过时输出测试摘要；任一合同不满足时抛出断言并返回非零退出码。
# ## 定位 (Position)
# 位于 video-publish-workbench 的代表性自动验证入口，覆盖脚本和模板的关键稳定性。
# ## 依赖 (Dependency)
# - build_publish_review.py：HTML 构建。
# - validate_publish_review.py：输入与超限门禁。
# - examples/opc-fde-review-input.json：标准输入样例。
# ## 维护规则 (Maintenance Rules)
# 1. 每次修改代码逻辑后，必须检查并更新上述的【核心功能】、【输入】、【输出】等信息，确保文档与代码一致。
# 2. 禁止修改或删除本【维护规则】章节的内容。
# 3. 修改完成后，必须扫描当前文件所在的文件夹目录，找到对应的 [当前文件夹名称]_README.md 文档，并同步更新该 README 中关于本文件的描述信息。

"""Representative regression tests for the publish review builder."""

from __future__ import annotations

import base64
import copy
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from build_publish_review import ICON_DIR, SKILL_ROOT, build_html
from extract_first_frame_cover import probe_media_size, resolve_ffmpeg
from validate_publish_review import validate_payload


def main() -> int:
    payload_path = SKILL_ROOT / "examples" / "opc-fde-review-input.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    errors, warnings = validate_payload(payload)
    assert not errors, errors
    assert not warnings, warnings

    with tempfile.TemporaryDirectory(prefix="video-publish-workbench-test-") as temp_value:
        temp_dir = Path(temp_value)
        video_path = temp_dir / "sample.mp4"
        subprocess.run(
            [
                resolve_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=320x180:d=0.2",
                "-pix_fmt", "yuv420p", str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        cover_path = temp_dir / "sample-cover.png"
        second_cover_path = temp_dir / "sample-cover-2.png"
        bilibili_cover_path = temp_dir / "sample-bilibili-cover.png"
        horizontal_cover_path = temp_dir / "review_first-frame-cover.jpg"
        for path, size in (
            (cover_path, "300x400"),
            (second_cover_path, "300x400"),
            (bilibili_cover_path, "400x300"),
            (horizontal_cover_path, "320x180"),
        ):
            subprocess.run(
                [
                    resolve_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"color=c=black:s={size}:d=0.1",
                    "-frames:v", "1", str(path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        output_path = temp_dir / "review.html"
        payload["video"].setdefault("cover_candidates", []).append({
            "id": "sample-bilibili", "label": "B站4:3", "path": str(bilibili_cover_path),
            "role": "bilibiliCover", "source": "provided",
        })
        payload["video"].setdefault("selected_cover_ids", {})["bilibiliCover"] = "sample-bilibili"
        result = build_html(
            payload,
            video_path=video_path,
            output_path=output_path,
            cover_candidates=[cover_path, second_cover_path],
            horizontal_cover_candidates=[horizontal_cover_path],
        )
        assert result["ok"] is True
        assert result["cover_count"] == 4
        assert result["resolved_vertical_cover_path"] == str(cover_path.resolve())
        assert result["bilibili_cover_path"] == str(bilibili_cover_path.resolve())
        assert result["horizontal_cover_path"] is None
        assert result["selected_cover_ids"]["horizontalCover"] is None
        assert probe_media_size(horizontal_cover_path) == (320, 180)
        html = output_path.read_text(encoding="utf-8")
        assert "__REVIEW_DATA_JSON__" not in html
        assert "__PLATFORM_ICONS_JSON__" not in html
        assert "data:image/png;base64," in html
        assert html.count("data:image/png;base64,") >= 5
        bilibili_icon_uri = "data:image/png;base64," + base64.b64encode(
            (ICON_DIR / "bilibili.png").read_bytes()
        ).decode("ascii")
        assert bilibili_icon_uri in html
        assert "data:image/svg+xml;base64," not in html
        assert '"bilibili"' in html
        assert video_path.resolve().as_uri() in html
        assert payload["video"]["display_title"] in html
        assert "join(\"\\n\\n\")" in html
        assert cover_path.resolve().as_uri() in html
        assert bilibili_cover_path.resolve().as_uri() in html
        assert "window.getPublishReviewSelection" in html
        assert 'schema_version: "social-publish-package.selection.v3"' in html
        assert "shipinhaoShortTitle" in html
        assert "title: platformTitle(id)" in html
        assert "horizontalCoverEnabled" in html
        assert "添加横版封面（可选）" not in html
        assert "sha256File(file)" in html
        assert 'fileName: cover.fileName || null' in html
        assert 'sha256: cover.sha256 || null' in html
        assert "selectedCoverIds" in html
        assert "fallbackCover" in html
        assert 'id="coverOptions"' not in html
        assert 'id="coverDropzone"' not in html
        assert 'id="previewVideo"' in html
        assert 'id="previewCover"' in html
        assert 'id="videoThumb"' in html
        assert 'data:image/jpeg;base64,' in html
        assert 'id="bodyOptions"' in html
        assert '"bodyVariants":' in html
        assert '"selectedBody":0' in html
        assert 'data-title-edit=' in html
        assert '【${platform.name}】' in html
        assert 'Meta Muse' not in html
        assert html.index('id="previewVideo"') < html.index('id="coverSlots"')

        empty_cover_payload = json.loads(payload_path.read_text(encoding="utf-8"))
        empty_cover_payload["video"].pop("cover_candidates", None)
        empty_cover_payload["video"].pop("selected_cover_ids", None)
        empty_cover_output = temp_dir / "empty-cover-review.html"
        empty_cover_result = build_html(empty_cover_payload, video_path=video_path, output_path=empty_cover_output)
        empty_cover_html = empty_cover_output.read_text(encoding="utf-8")
        assert empty_cover_result["cover_count"] == 0
        assert empty_cover_result["selected_cover_ids"] == {
            "cover": None, "horizontalCover": None, "bilibiliCover": None,
        }
        assert '"candidates":[]' in empty_cover_html
        assert 'id="verticalCoverInput"' in empty_cover_html
        assert 'id="bilibiliCoverInput"' in empty_cover_html
        assert 'id="horizontalCoverInput"' in empty_cover_html
        assert 'const roles = ["cover", "bilibiliCover", "horizontalCover"]' in empty_cover_html
        assert '选择${coverRoleLabel(role)}封面' in empty_cover_html

        scripts = re.findall(r"<script>([\s\S]*?)</script>", html)
        assert scripts, "generated HTML script missing"
        if shutil.which("node"):
            js_path = temp_dir / "generated.js"
            js_path.write_text(scripts[-1], encoding="utf-8")
            subprocess.run(["node", "--check", str(js_path)], check=True, capture_output=True, text=True)

        legacy_payload = copy.deepcopy(payload)
        legacy_payload["platforms"].pop("bilibili")
        legacy_errors, legacy_warnings = validate_payload(legacy_payload)
        assert not legacy_errors, legacy_errors
        assert not legacy_warnings, legacy_warnings
        legacy_output = temp_dir / "legacy-four-platform-review.html"
        build_html(legacy_payload, video_path=video_path, output_path=legacy_output)
        legacy_html = legacy_output.read_text(encoding="utf-8")
        assert '"bilibili"' not in legacy_html

        youtube_payload = copy.deepcopy(payload)
        youtube_payload["platforms"]["youtube"] = {
            "name": "YouTube",
            "mode": "separate",
            "tag_limit": 60,
            "tags": [
                {"name": "AI写作", "kind": "ai", "selected": True, "reason": "视频演示 AI 写作"},
                {"name": "内容创作", "kind": "ai", "selected": True, "reason": "视频讲述内容创作"},
                {"name": "X文章", "kind": "ai", "selected": True, "reason": "视频展示 X 文章"},
            ],
        }
        youtube_errors, youtube_warnings = validate_payload(youtube_payload)
        assert not youtube_errors, youtube_errors
        assert not youtube_warnings, youtube_warnings
        youtube_output = temp_dir / "youtube-review.html"
        build_html(youtube_payload, video_path=video_path, output_path=youtube_output)
        youtube_html = youtube_output.read_text(encoding="utf-8")
        youtube_icon_uri = "data:image/png;base64," + base64.b64encode(
            (ICON_DIR / "youtube.png").read_bytes()
        ).decode("ascii")
        assert youtube_icon_uri in youtube_html
        assert '"youtube"' in youtube_html
        assert "复制正文与话题" in youtube_html
        assert "文案复制 · 建议3个话题" not in youtube_html
        youtube_payload["platforms"]["youtube"]["tags"].extend(
            {"name": f"相关话题{index}", "kind": "ai", "selected": True, "reason": "测试上限"}
            for index in range(57)
        )
        youtube_errors, _ = validate_payload(youtube_payload)
        assert not youtube_errors, youtube_errors
        youtube_payload["platforms"]["youtube"]["tags"].append(
            {"name": "相关话题57", "kind": "ai", "selected": True, "reason": "测试超限"}
        )
        youtube_errors, _ = validate_payload(youtube_payload)
        assert any("platforms.youtube" in error and "标签超限" in error for error in youtube_errors)

        demo = copy.deepcopy(payload)
        demo["content"]["titles"][0]["text"] = "这是一个明确超过十六个字限制的标题超限演示候选"
        demo["platforms"]["douyin"]["tags"].append(
            {"name": "超限演示", "kind": "ai", "selected": True, "reason": "测试第六个已选标签"}
        )
        for tag in demo["platforms"]["douyin"]["tags"]:
            tag["selected"] = True
        errors, _ = validate_payload(demo)
        assert any("标题超限" in item for item in errors)
        assert any("标签超限" in item for item in errors)
        demo_errors, demo_warnings = validate_payload(demo, allow_overlimit_demo=True)
        assert not demo_errors, demo_errors
        assert any("超限演示" in item for item in demo_warnings)
        demo_output = temp_dir / "review-overlimit.html"
        build_html(
            demo,
            video_path=video_path,
            output_path=demo_output,
            allow_overlimit_demo=True,
            cover_candidates=[cover_path],
        )
        assert " over" in demo_output.read_text(encoding="utf-8")

        fallback_output = temp_dir / "fallback-review.html"
        fallback_result = build_html(payload, video_path=video_path, output_path=fallback_output)
        fallback_cover = Path(fallback_result["resolved_vertical_cover_path"])
        assert fallback_result["selected_cover_ids"]["cover"] is None
        assert fallback_cover.is_file() and fallback_cover.stat().st_size > 0
        fallback_width, fallback_height = probe_media_size(fallback_cover)
        assert abs(fallback_width / fallback_height - 3 / 4) <= 0.02

    print("video publish workbench tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
