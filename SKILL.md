---
name: video-publish-workbench
description: 为视频、字幕、逐字稿或主题材料准备标题、正文和逐平台话题，可选调研与封面生图，生成可编辑的本地视频预发布工作台。用户选择后可复制发布信息；明确要求时再生成可选的一键发交接任务。
---

# 视频预发布工作台

把一条视频的标题、正文、话题和封面放到同一个本地页面，让用户选好再发布。使用步骤、依赖与完整能力见 [README.zh-CN.md](README.zh-CN.md)；English documentation: [README.md](README.md)。

## 三种模式

- `title-only`：基于用户材料生成恰好 10 个不同方向的标题，推荐 Top 3，并说明理由。标题中的数字、亲测、经历和效果必须有材料依据。
- `video-prepublish`：默认模式。生成 5 个公共标题、3–4 个正文版本、逐平台话题和一个本地 HTML。终点是用户评审、编辑与复制。
- `publish-handoff`：用户已选好并明确要求交接时，读取最新 selection，把它转换为逐平台任务 JSON。任务生成成功只代表离线转换通过；脚本不会实际发布。

公开版没有内置账号、发布凭证、私人偏好或执行历史；不要求安装作者的其他 Skill。本仓库打包了调研与封面制作流程；它们使用用户 Agent 已授权、实际可用的浏览器和原生生图工具。视频转写和真实发布仍需单独可用的能力。

## 读取合同

- 生成工作台前读 `references/platform-copy-contract.md`、`references/review-payload.schema.json`。
- 文案检查读 `references/distribution-risk-review.md` 和 `references/distribution-risk-knowledge.md`。
- 标签配置读 `data/platform-tag-library.json`，默认为空，用户可自行添加有依据的条目。
- 交接前读 `references/publish-selection.schema.json` 和 `references/yijianfa-handoff-contract.md`。
- 合成输入参考 `examples/demo-input.json`；旧文件名 `examples/opc-fde-review-input.json` 仅保留测试兼容，其内容也是合成桌面整理示例。

## 一次请求完成前置准备

用户可以从一个主题开始，也可以提供已有图片、视频、逐字稿或文案。支持 `research=auto|skip`、`images=generate|reuse|none`、`reference_mode=none|gallery`；这些是 Agent 的执行选项，不是静态网页调用模型的开关。用户已给出的选项直接执行；请求“全部生成”时采用 research=auto、images=generate，复用现有证据、素材和授权。没有选择时，已有素材优先复用，缺少文案由 Agent 按实际材料补齐；联网和生成工具不可用时说明缺口。

1. 参考 [前置准备示例](examples/preparation-brief.json)，写当前任务的 `brief.md`，包含主题、受众、平台、内容形式、数量、参考图册、来源限制与执行选项。输出目录放在仓库之外，不把任务素材或本机路径提交到 Git。
2. research=auto 时读取并执行本仓库 [调研能力](capabilities/research/SKILL.md)，遵循 [来源契约](references/research-contract.md)。按主题查证事实、同批采集标题正文话题，记录来源和未知项；research=skip 时使用用户材料，并明确未调研。保留来源与采用理由，不用搜索摘要冒充原文。
3. images=generate 时读取并执行本仓库 [生图能力](capabilities/image-production/SKILL.md)和 [提示词模板](references/image-prompts.md)。主题决定图片内容和数量；gallery 模式只使用用户授权的参考图册，提取构图、配色、版式，不写死姿势、人像或作者的私人图库。images=reuse 时核对已有文件，none 时保留上传槽或当前构建器允许的回退。实际生图由用户 Agent 的原生工具执行，不需要安装作者其他 Skill。
4. Agent 基于当前材料、图片和已核验研究写标题、正文及话题候选。事实必须有输入或来源依据，方案不得伪装成经历、实测或热门。用户已有文案默认保留，新增不同侧重点的候选供选择。
5. 将实际素材和候选转换到本仓库原输入 schema，继续下方校验、构建和用户评审流程。研究文件和图片清单独立保存，不把新字段随意塞入旧 schema。只登记真实文件与真实工具回执。
6. 交付 HTML、规范输入、来源清单、资产清单和 `preparation-report.md`。报告逐项标 completed、partial、skipped 或 unavailable，并列出证据、生成数量、复用数量和缺口。禁止把生图提示词当成已生成图片，把离线脚本测试当成联网调研或真实发布。

图文工作台可以从任意主题组织内页；视频工作台生成封面与发布文案，仍需用户提供视频或逐字稿。此包不会自动生成整条视频。

## 生成流程

1. 确认视频、已有字幕或逐字稿、受众、核心观点和禁止夸大的事实。复用已有材料；没有转写工具时说明缺口，不假装读过音频。
2. 有授权的平台样本时，同批记录标题、可获取正文、真实标签、来源和时间。缺失值记 null，不从标题推测正文，不伪造热度或平台认可。
3. 写恰好 5 个不同方向的公共标题，每个最多 16 个 Unicode 字符、附一句说明；写 3–4 个不同侧重的正文版本。上述长度是当前工作台默认配置，不代表全部平台实时规则。
4. 根据本条内容生成逐平台话题，保留准确产品名和依据，不硬塞活动或凑满额度。用户配置了活动目录时可在授权范围读取，并核对平台、有效期及参与条件；没有目录时用内容相关标签，明确未验证热度。无默认外部目录、无强制私人偏好。
5. 写符合 schema 的 JSON。新任务使用六个平台；兼容旧四／五平台输入。每个平台话题数量不超过工作台配置：小红书 10、抖音 5、快手 4、视频号 7、B 站 10、YouTube 60。实际发布前核对当前平台规则；修改默认值时同步 schema、两个验证器与测试。
6. 可登记 3:4 `cover`、4:3 `bilibiliCover`、16:9 `horizontalCover`；候选和默认选择都按角色匹配。没有竖版候选时，构建器用 FFmpeg 将第一帧居中裁为 3:4。第一帧仅是稳定回退，不保证构图合适。其他比例可留空。
7. 使用绝对路径校验再构建。输出 HTML 引用本机视频和封面，不上传；平台图标与视频缩略图内嵌。保持媒体文件原位置。分享前删除个人路径和私密素材。

```bash
python3 scripts/validate_publish_review.py --input /absolute/path/review-input.json --video /absolute/path/video.mp4
python3 scripts/build_publish_review.py --input /absolute/path/review-input.json --video /absolute/path/video.mp4 --output /absolute/path/project/review.html
```

输入必须包含非空主题、核心观点、5 个标题、默认选择、正文和平台列表。`title_limit` 使用 16；`selected_title` 和 `selected_body` 指向现有候选。封面文件存在且符合比例，不能用不同角色的图片替代。

## 页面与用户选择

统一预览和四个缩略项：3:4、4:3、16:9、视频。用户可切换预览、选择或拖入封面、编辑标题、切换并编辑正文、逐平台勾选话题。计数超限显示提示，正式构建遇到超限须失败，不静默截断。

标题和正文编辑保存在当前浏览器草稿中，不写回原 HTML。复制使用当前最新选择；AI 交接可读取页面 `window.getPublishReviewSelection()`，由用户或有权限的 Agent 保存 JSON。临时上传图片需在本机允许目录通过文件名、大小与 SHA-256 找到唯一原文件，页面预览可用不代表交接资产已就绪。

用户页面编辑后重新交接，必须读取最新 selection；不得用初稿覆盖用户选择。有需要时按当前选择额外生成发布文案 Markdown，但不能声称生成器已自动完成该文件。

## 可选发布交接

`build_yijianfa_tasks.py` 只生成 JSON。一键发不是本地工作台的默认依赖，也未在本仓库发布流程中验证全部平台的真实提交。

```bash
python3 scripts/build_yijianfa_tasks.py --selection /absolute/path/publish-selection.json --video /absolute/path/video.mp4 --browser-context regular --output-dir /absolute/path/tasks
```

- 明确选择 `regular` 或 `incognito`，核对实际安装 CLI 的 doctor/capabilities、目标登录态和字段语义；版本不兼容时停止。
- 逐平台拆分标题、标签和封面；视频号短标题最多 16 字，仅文字、数字、字母和空格。
- 当前离线合同中抖音需要 3:4 加 4:3，YouTube 需要启用的 16:9。B 站优先 4:3，其次启用的 16:9，再回退竖版。
- YouTube 话题写入描述，task tags 留空；必须在真实页面读回确认，不能据离线测试宣称适配器已兼容。
- 默认 `--mode fill` 仅写出填入命令。`--mode publish` 会在生成的任务中带公开链接保护，但仍不执行命令。只有明确授权、核对账号和能力后才运行真实发布；不得绕过登录或站点限制。
- 状态 unknown 或超时时保留 requestId，先核对已有提交，不能重复发送。用户接管页面后停止自动操作。

## 隐私和验证

不把真实字幕、账号、私人目录或回执提交到公开仓库。默认标签库和记忆文件为空；私有配置放仓库之外。页面无网络请求和凭证配置，剪贴板与本地存储可能受浏览器权限限制。

```bash
python3 scripts/test_build_publish_review.py
python3 scripts/test_yijianfa_handoff.py
```

测试默认离线；仅明确设置 `RUN_YIJIANFA_INTEGRATION=1` 才允许调用已安装 CLI 的 prepare。脚本测试不能代替实际浏览器操作和真实发布验收。交付时区分：本地生成、已人工评审、任务生成、已填入、已提交、公开链接已核验。
