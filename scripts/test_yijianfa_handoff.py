#!/usr/bin/env python3
# # 文件说明书 (File Manual)
# ## 核心功能 (Core Function)
# 回归验证五个平台的逐平台一键发任务、YouTube 描述话题与单一横版封面、旧四平台兼容、B站 4:3 优先封面、封面角色与发布保护配置。
# ## 输入 (Input)
# 在临时目录构造合成媒体和六平台评审选择；默认离线，RUN_YIJIANFA_INTEGRATION=1 才检查已安装 CLI 的 prepare。
# ## 输出 (Output)
# 通过时输出测试摘要；任一交接合同不满足时抛出断言并返回非零退出码。
# ## 定位 (Position)
# 位于 video-publish-workbench 的一键发交接自动验证层。
# ## 依赖 (Dependency)
# - build_yijianfa_tasks.py：被测任务构建器。
# - references/yijianfa-handoff-contract.md：交接行为合同。
# ## 维护规则 (Maintenance Rules)
# 1. 每次修改代码逻辑后，必须检查并更新上述的【核心功能】、【输入】、【输出】等信息，确保文档与代码一致。
# 2. 禁止修改或删除本【维护规则】章节的内容。
# 3. 修改完成后，必须扫描当前文件所在的文件夹目录，找到对应的 [当前文件夹名称]_README.md 文档，并同步更新该 README 中关于本文件的描述信息。

"""Regression tests for the review-to-yijianfa handoff builder."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from build_yijianfa_tasks import build_tasks
from extract_first_frame_cover import resolve_ffmpeg


def cover_record(path: Path, role: str, *, publishable: bool) -> dict[str, object]:
    return {
        "id": f"test-{role}",
        "fileName": path.name,
        "size": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "path": str(path.resolve()) if publishable else None,
        "role": role,
        "source": "provided" if publishable else "temporary",
        "publishable": publishable,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="social-publish-handoff-test-") as temp_value:
        temp_dir = Path(temp_value)
        video = temp_dir / "sample.mp4"
        video.write_bytes(b"local-video-test")
        vertical = temp_dir / "vertical.png"
        horizontal = temp_dir / "horizontal.png"
        bilibili_cover = temp_dir / "bilibili-4x3.png"
        for path, size in ((vertical, "300x400"), (horizontal, "320x180"), (bilibili_cover, "320x240")):
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
        output_dir = temp_dir / "tasks"

        platform_tags = {
            "xiaohongshu": ["小红书专属"],
            "douyin": ["抖音专属"],
            "kuaishou": ["快手专属"],
            "shipinhao": ["视频号专属"],
            "bilibili": ["B站专属"],
        }
        selection = {
            "schema_version": "social-publish-package.selection.v3",
            "title": "测试标题",
            "body": "测试正文",
            "platforms": {
                platform: {
                    "mode": "separate" if platform in {"xiaohongshu", "douyin", "bilibili"} else "combined",
                    "title": "测试标题" if platform != "shipinhao" else "测试标题无符号",
                    "tags": tags,
                }
                for platform, tags in platform_tags.items()
            },
            "covers": {
                "verticalCover": cover_record(vertical, "cover", publishable=False),
                "bilibiliCover": cover_record(bilibili_cover, "bilibiliCover", publishable=True),
                "horizontalCover": cover_record(horizontal, "horizontalCover", publishable=True),
                "horizontalCoverEnabled": True,
                "selectedCoverIds": {"cover": None, "horizontalCover": "test-horizontalCover"},
            },
        }
        selection["platforms"]["youtube"] = {
            "mode": "separate",
            "title": "测试标题",
            "tags": ["AI写作"],
        }
        youtube_selection = copy.deepcopy(selection)
        youtube_selection["covers"]["verticalCover"] = None
        youtube_selection["platforms"]["youtube"]["tags"] = ["AI", "agent", "Muse", "tutorial", "tools", "workflow"]
        yt_result = build_tasks(
            youtube_selection, video_path=video, output_dir=temp_dir / "youtube",
            browser_context="regular", mode="publish", platforms=["youtube"],
            search_roots=[], expected_accounts={},
        )
        yt_task = json.loads(Path(yt_result["tasks"][0]["task"]).read_text())
        assert yt_task["data"]["title"] == selection["platforms"]["youtube"]["title"]
        assert yt_task["data"]["tags"] == []
        assert yt_task["data"]["description"] == selection["body"] + "\n\n#AI #agent #Muse #tutorial #tools #workflow"
        assert yt_task["data"]["content"] == yt_task["data"]["description"]
        assert yt_task["data"]["publishGuard"]["requirePublicUrl"] is True
        assert [a["role"] for a in yt_task["assets"]] == ["media", "horizontalCover"]
        assert yt_task["assets"][1]["path"] == str(horizontal.resolve())
        youtube_selection["covers"].update(horizontalCover=None, horizontalCoverEnabled=False)
        try:
            build_tasks(youtube_selection, video_path=video, output_dir=temp_dir / "yt-invalid",
                        browser_context="regular", mode="fill", platforms=["youtube"],
                        search_roots=[], expected_accounts={})
        except ValueError as error:
            assert "16:9" in str(error)
        else:
            raise AssertionError("YouTube without 16:9 must fail")
        result = build_tasks(
            selection,
            video_path=video,
            output_dir=output_dir,
            browser_context="incognito",
            mode="fill",
            platforms=list(platform_tags),
            search_roots=[],
            expected_accounts={},
        )
        assert result["ok"] is True
        assert result["resolved_covers"]["cover"] == str(vertical.resolve())
        assert len(result["tasks"]) == 5
        for entry in result["tasks"]:
            task = json.loads(Path(entry["task"]).read_text(encoding="utf-8"))
            platform = entry["platform"]
            assert task["browserContext"] == "incognito"
            assert task["platforms"] == [platform]
            assert task["data"]["tags"] == platform_tags[platform]
            assert task["data"]["title"] == selection["platforms"][platform]["title"]
            roles = [asset["role"] for asset in task["assets"]]
            if platform == "bilibili":
                assert roles == ["media", "horizontalCover"]
            else:
                assert roles[:2] == ["media", "cover"]
            if platform == "douyin":
                assert task["assets"][2]["path"] == str(bilibili_cover.resolve())
            if platform in {"douyin", "shipinhao"}:
                assert "horizontalCover" in roles
            elif platform != "bilibili":
                assert "horizontalCover" not in roles
            yijianfa = shutil.which("yijianfa") if os.environ.get("RUN_YIJIANFA_INTEGRATION") == "1" else None
            if yijianfa:
                prepared = subprocess.run(
                    [yijianfa, "prepare", "--browser-context", "incognito", "--input", entry["task"]],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                assert prepared.returncode == 0, prepared.stderr
                response = json.loads(prepared.stdout)
                assert response["ok"] is True
                assert response["result"]["status"] == "prepared_local"

        no_horizontal = copy.deepcopy(selection)
        no_horizontal["covers"]["horizontalCover"] = None
        no_horizontal["covers"]["horizontalCoverEnabled"] = False
        no_horizontal["covers"]["selectedCoverIds"]["horizontalCover"] = None
        no_horizontal_result = build_tasks(
            no_horizontal,
            video_path=video,
            output_dir=temp_dir / "tasks-no-horizontal",
            browser_context="regular",
            mode="fill",
            platforms=list(platform_tags),
            search_roots=[],
            expected_accounts={},
        )
        for entry in no_horizontal_result["tasks"]:
            task = json.loads(Path(entry["task"]).read_text(encoding="utf-8"))
            if entry["platform"] in {"douyin", "bilibili"}:
                assert task["assets"][-1]["path"] == str(bilibili_cover.resolve())
            else:
                assert "horizontalCover" not in [asset["role"] for asset in task["assets"]]

        missing_four_three = copy.deepcopy(selection)
        missing_four_three["covers"]["bilibiliCover"] = None
        try:
            build_tasks(missing_four_three, video_path=video, output_dir=temp_dir / "missing",
                        browser_context="regular", mode="fill", platforms=["douyin"],
                        search_roots=[], expected_accounts={})
        except ValueError as error:
            assert "抖音必须" in str(error)
        else:
            raise AssertionError("Douyin must reject missing 4:3 even with 16:9 selected")

        bilibili_four_three = copy.deepcopy(selection)
        bilibili_four_three["covers"]["bilibiliCover"] = cover_record(bilibili_cover, "bilibiliCover", publishable=True)
        bilibili_four_three["covers"]["selectedCoverIds"]["bilibiliCover"] = "test-bilibiliCover"
        bilibili_result = build_tasks(
            bilibili_four_three,
            video_path=video,
            output_dir=temp_dir / "tasks-bilibili-four-three",
            browser_context="regular",
            mode="fill",
            platforms=["bilibili"],
            search_roots=[],
            expected_accounts={},
        )
        bilibili_task = json.loads(Path(bilibili_result["tasks"][0]["task"]).read_text(encoding="utf-8"))
        assert [asset["role"] for asset in bilibili_task["assets"]] == ["media", "horizontalCover"]
        assert bilibili_task["assets"][1]["path"] == str(bilibili_cover.resolve())
        assert bilibili_result["resolved_covers"]["bilibiliCover"] == str(bilibili_cover.resolve())

        wrong_ratio_bilibili = copy.deepcopy(bilibili_four_three)
        wrong_ratio_bilibili["covers"]["bilibiliCover"] = cover_record(horizontal, "bilibiliCover", publishable=False)
        try:
            build_tasks(
                wrong_ratio_bilibili,
                video_path=video,
                output_dir=temp_dir / "tasks-bilibili-wrong-ratio",
                browser_context="regular",
                mode="fill",
                platforms=["bilibili"],
                search_roots=[],
                expected_accounts={},
            )
        except ValueError as error:
            assert "4:3 B站" in str(error)
        else:
            raise AssertionError("16:9 image must not be accepted as B站 4:3 cover")

        legacy_selection = copy.deepcopy(selection)
        legacy_selection["platforms"].pop("bilibili")
        legacy_selection["platforms"].pop("youtube")
        legacy_result = build_tasks(
            legacy_selection,
            video_path=video,
            output_dir=temp_dir / "tasks-legacy-four-platform",
            browser_context="regular",
            mode="fill",
            platforms=list(legacy_selection["platforms"]),
            search_roots=[],
            expected_accounts={},
        )
        assert len(legacy_result["tasks"]) == 4
        assert "bilibili" not in [entry["platform"] for entry in legacy_result["tasks"]]

        invalid_vertical = copy.deepcopy(no_horizontal)
        invalid_vertical["covers"]["verticalCover"] = cover_record(horizontal, "cover", publishable=True)
        try:
            build_tasks(
                invalid_vertical,
                video_path=video,
                output_dir=temp_dir / "tasks-invalid-vertical",
                browser_context="regular",
                mode="fill",
                platforms=["xiaohongshu"],
                search_roots=[],
                expected_accounts={},
            )
        except ValueError as error:
            assert "3:4 竖版" in str(error)
        else:
            raise AssertionError("horizontal image must not be accepted as vertical cover")

        invalid_shipinhao_title = copy.deepcopy(no_horizontal)
        invalid_shipinhao_title["platforms"]["shipinhao"]["title"] = "标题，包含逗号"
        try:
            build_tasks(
                invalid_shipinhao_title,
                video_path=video,
                output_dir=temp_dir / "tasks-invalid-shipinhao-title",
                browser_context="regular",
                mode="fill",
                platforms=["shipinhao"],
                search_roots=[],
                expected_accounts={},
            )
        except ValueError as error:
            assert "只能包含文字、字母、数字和空格" in str(error)
        else:
            raise AssertionError("shipinhao title punctuation must be rejected")

        publish_result = build_tasks(
            selection,
            video_path=video,
            output_dir=temp_dir / "publish-tasks",
            browser_context="regular",
            mode="publish",
            platforms=["xiaohongshu"],
            search_roots=[],
            expected_accounts={},
        )
        publish_task = json.loads(Path(publish_result["tasks"][0]["task"]).read_text(encoding="utf-8"))
        assert publish_task["data"]["publishGuard"] == {
            "version": 1, "expectedTargets": {}, "requirePublicUrl": True,
        }
        assert publish_result["tasks"][0]["execute_argv"][1:3] == ["publish", "--yes"]

    print("social publish yijianfa handoff tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
