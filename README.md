<a id="视频发布工作台video-publish-workbench"></a>

<div align="center">

# 视频发布工作台 · 发布前预览与选择

**把视频、标题、正文和封面放在同一个页面里选好再发布。**

标题候选 · 正文编辑 · 逐平台话题 · 封面选择

[![中文说明](https://img.shields.io/badge/%E8%AF%B4%E6%98%8E-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-059669)](#readme-detail-15)
[![项目类型](https://img.shields.io/badge/%E9%A1%B9%E7%9B%AE-Skill-6366f1)](#readme-detail-15)

[✨ 核心特性](#readme-detail-15) · [👀 效果预览](#readme-detail-17) · [✅ 适用场景](#readme-detail-27) · [🚀 安装](#readme-detail-19) · [🧩 模块速查](#readme-detail-33) · [🔒 隐私、验证与维护](#readme-detail-37)

</div>

---

[给 AI 的使用规则](SKILL.md) · [合成输入样例](examples/demo-input.json)

视频做完之后，发布准备往往还散在几个地方：标题在聊天里，正文在文档里，封面在文件夹里，各个平台的话题又不完全一样。这个 Skill 让 AI 先准备候选，你在一个页面里检查、修改和选择。生成本地工作台不需要登录平台、配置密钥或安装发布工具。页面与默认说明均使用中文。

<a id="readme-section-1"></a>

<a id="详细能力清单"></a>

<a id="readme-detail-15"></a>

## ✨ 核心特性

### 前置准备能力

- 按用户主题调研同类内容与事实，记录来源、可见互动数据和缺口。
- 复用用户图片，或调用可用生图工具制作当前主题的图片与封面。
- 可选参考用户图册的构图、配色和版式，保留原图，生成新副本。
- 根据实际材料生成标题、正文和话题候选，再输出可编辑工作台。

**可以完全自动准备吗？** 在你的 AI 助手具备相应工具、素材授权和必要预算时，可以用一次请求串起准备流程。登录、工具不可用或事实缺失时会报告缺口；静态页面不会自己调用模型。


| 能力 | 你能做什么 | 条件与边界 |
| --- | --- | --- |
| 只生成标题 | 让 AI 给出 10 个方向和 Top 3 | 依据你提供的事实，由 AI 助手生成 |
| 视频标题评审 | 比较、选择、编辑五个标题 | 公共标题默认最多 16 个 Unicode 字符 |
| 多版正文 | 切换不同版本，分别修改，查看字数 | 页面草稿存在当前浏览器，不自动改原 JSON |
| 媒体预览 | 播放本地视频，比较三种比例的封面 | 视频与封面引用本地文件，移动后可能失效 |
| 封面选择 | 点击、拖入、更换或清空封面 | 临时图片交接时需要找到唯一原始文件 |
| 六个平台 | 小红书、抖音、快手、视频号、B 站、YouTube 分别选话题 | 默认数量是仓库配置，不能当作实时平台规则 |
| 复制发布内容 | 复制标题、分平台正文话题或完整 AI 发布信息 | 剪贴板需要浏览器允许 |
| 当前选择数据 | 用 `window.getPublishReviewSelection()` 取得当前选择和封面元信息 | 由用户或授权 Agent 保存 JSON，不自动写回 HTML |
| 结构校验 | 拦截缺字段、封面比例错误、标题或话题超限 | 不自动核实事实，也不能预测平台审核 |
| 可选发布交接 | 把确认后的选择转换为逐平台一键发任务 | 离线 JSON 成功不代表登录、上传或真实发布成功 |

六个平台的默认话题数量上限依次为 10、5、4、7、10、60。新任务准备六个平台，旧四／五平台输入仍兼容。真实发布前需核对当前规则；要改数量时同步 schema、两个验证器和测试。公开版标签库为空，用户可以加入有依据的相关条目；没有默认流量目录，也不会自动请求历史活动页面。

<a id="readme-section-2"></a>

<a id="工作台效果"></a>

<a id="readme-detail-17"></a>

## 👀 效果预览

<table>
<tr>
<td width="33%" align="center"><a href="docs/screenshots/workbench-preview.png"><img src="docs/screenshots/workbench-preview.png" alt="淡白色遮盖对话与路径后的视频预发布工作台效果示意" width="250"></a><br><sub>淡白色遮盖对话与路径后的视频预发布工作台效果示意</sub></td>
<td width="33%" align="center"><a href="docs/screenshots/choose-title.png"><img src="docs/screenshots/choose-title.png" alt="视频标题候选与选中状态" width="250"></a><br><sub>视频标题候选与选中状态</sub></td>
<td width="33%" align="center"><a href="docs/screenshots/platform-tags.png"><img src="docs/screenshots/platform-tags.png" alt="小红书、抖音等平台分别选择话题" width="250"></a><br><sub>小红书、抖音等平台分别选择话题</sub></td>
</tr>
</table>

视频、不同尺寸的封面、标题候选和正文放在一起检查。各个平台的话题分开选择，选好后再复制当前发布包。

效果示意来自课件中的视频案例，左侧对话与本机路径已用淡白色遮盖，指令卡展示调用示例，不是实际执行回执。下面的局部截图保留实际演示界面。视频内容与话题只用于展示操作，不是当前平台的推荐话题，也不代表发布成功。

### 比较标题


### 按平台选话题


小红书、抖音、快手、视频号、B 站和 YouTube 各有自己的选择状态。整理某个平台的文案，不会直接连接账号或发布内容。

![示意：从材料准备到人工选择，再到复制或可选交接](docs/workflow.svg)

<a id="readme-section-7"></a>

<a id="什么时候用"></a>

<a id="readme-detail-27"></a>

## ✅ 适用场景

- 视频和逐字稿已经有了，希望比较几个标题方向，再决定用哪一个。
- 同一条视频准备发到多个平台，希望正文共用，话题分别选择。
- 竖版、横版封面需要一起检查，避免拿错图片。
- 同事或 AI 负责准备候选，你负责最终修改和发布决定。

<a id="readme-section-3"></a>

<a id="安装"></a>

<a id="readme-detail-19"></a>

## 🚀 安装

从下面的现有入口开始，按顺序准备环境、配置并完成首次运行。

```bash
npx skills add mileson/video-publish-workbench
```

<a id="readme-section-4"></a>

<a id="自己填写输入并生成"></a>

<a id="readme-detail-21"></a>

## 🔧 自备材料与生成工作台

1. 把 `examples/demo-input.json` 复制到私有项目目录。
2. 替换合成内容，保留五个标题、正文版本和符合默认数量限制的话题。
3. 提供视频绝对路径。已有封面可以写进 `video.cover_candidates`，也可以用下面的命令参数登记。
4. 先校验，再构建并打开页面。视频和封面保留在原位置。

```bash
python3 scripts/validate_publish_review.py --input /absolute/path/review-input.json --video /absolute/path/video.mp4
python3 scripts/build_publish_review.py --input /absolute/path/review-input.json --video /absolute/path/video.mp4 --cover-candidate /absolute/path/vertical-3x4.png --bilibili-cover-candidate /absolute/path/landscape-4x3.png --horizontal-cover-candidate /absolute/path/wide-16x9.png --output /absolute/path/project/review.html
```

没有对应封面时可以省略参数。没有竖版候选，构建器会把第一帧居中裁成 3:4，作为稳定回退；仍需检查画面是否合适。横版槽位可以为空。登记横版图片不一定自动选中，默认选择由输入 JSON 控制。

<a id="readme-section-5"></a>

<a id="可选交接给发布工具"></a>

<a id="readme-detail-23"></a>

## 📤 可选的发布交接

多数情况下，复制检查好的内容、手动发布就够用了。已有兼容一键发环境时，可以把最新选择转换为任务；一键发不属于本地工作台的默认依赖。

```bash
python3 scripts/build_yijianfa_tasks.py --selection /absolute/path/publish-selection.json --video /absolute/path/video.mp4 --browser-context regular --output-dir /absolute/path/tasks
```

命令只写出任务 JSON 和 manifest，不执行其中的发布命令。运行真实操作前核对 CLI 能力、当前登录账号和目标平台要求，真实发布需要明确授权及结果链接核验。`--mode publish` 只改变生成任务，仍不执行命令。

当前离线合同里，抖音需要 3:4 加 4:3 封面，YouTube 需要启用的 16:9 封面；YouTube 话题放进描述、task tags 留空。这些映射仍需用实际安装的适配器在真实页面读回，不能据测试宣布所有平台发布已验证。

<a id="readme-section-6"></a>

<a id="告诉-ai-你想做什么"></a>

<a id="readme-detail-25"></a>

## 🤖 给 Agent 的任务示例

把完整仓库放进你的 AI 助手支持的 Skill 目录。支持斜杠调用的助手可以使用下面的指令；其他助手可以直接让它读取仓库里的 `SKILL.md`。斜杠形式取决于所用助手，不是网页里的按钮。

```text
/video-publish-workbench
准备这条桌面整理视频的发布材料，面向第一次接触这个主题的人。
先调研，准备标题、正文和话题；需要图片时生成图片封面。
有参考图册就参考构图与配色，不沿用旧主题和旧文案。
最后生成工作台，让我选择和修改。不要发布。
```

附上自己的视频和已有逐字稿；没有转写能力时，AI 会说明缺口。这里生成封面和发布材料，不生成整条视频。

| 选项 | 你可以怎么说 |
|---|---|
| 调研 | “先调研”或“只用我的材料，不调研” |
| 图片准备 | “帮我生图”或“复用这些图片” |
| 图册参考 | “参考这份图册的构图与配色”或“不用参考图册” |
| 全流程 | “从主题开始，调研、准备图片和文案，再生成工作台” |

调研、生图的执行流程和提示词已经打包在本仓库的 [capabilities](capabilities/research/SKILL.md) 中，图片整理工具也随仓库分发。使用时需要你的 AI 助手有可用的浏览器或搜索、生图工具；没有这些工具仍可使用已有材料生成工作台。不会内置账号或密钥，也不会仅凭一句指令绕过付费、登录和授权。

能力来源与集成范围见 [说明](docs/capability-origins.md)。

[前置准备示例](examples/preparation-brief.json)给 Agent 读取；最终工作台仍使用原来的输入格式。

<a id="readme-section-8"></a>

<a id="让-ai-帮你准备自己的视频"></a>

<a id="readme-detail-29"></a>

## 🤖 让 Agent 准备视频材料

这是给 Agent 使用的 Skill，加上一组负责校验和生成页面的 Python 脚本。能读取本地文件、运行 Python 的 AI 助手可以按照 `SKILL.md` 操作。把完整目录放到助手支持的 Skill 目录，或者直接把仓库的绝对路径交给它。不同助手的安装位置不同；生成器本身不会自动写 AI 文案。

你可以这样发送：

> 读取这个仓库的 SKILL.md。根据我提供的视频和逐字稿，准备五个标题、三个正文版本，以及各个平台相关的话题，生成本地视频预发布工作台。视频保持私密，不上传、不发布。缺少逐字稿或平台样本时请说明，不要编造视频内容或热度。

同时提供真实文件路径、目标受众和事实约束。转写、封面制作、实时平台调研需要助手有对应能力和授权；缺少能力时应使用你给出的材料并说明缺口。生成工作台不强制安装作者的其他 Skill。

<a id="readme-section-9"></a>

<a id="进一步阅读"></a>

<a id="readme-detail-31"></a>

## 📚 进一步阅读

- [贡献指南](CONTRIBUTING.md)
- [安全反馈](SECURITY.md)

<a id="readme-section-10"></a>

<a id="仓库导航"></a>

<a id="readme-detail-33"></a>

## 🧩 模块速查

按要处理的工作选择入口，先看模块职责，再进入对应文件或目录。

| 模块入口 | 负责什么 | 什么时候看 |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | Agent 使用规则与执行入口 | 让 Agent 读取任务规则、所需材料与交付要求 |
| [`assets/`](assets/) | 项目图片与静态素材 | 维护图片、静态文件和展示素材 |
| [`capabilities/`](capabilities/) | 可独立阅读的能力模块 | 查找具体场景对应的技能入口 |
| [`docs/`](docs/) | 项目说明与参考文档 | 查阅运行、设计与维护约定 |
| [`examples/`](examples/) | 可参考的输入与调用示例 | 用现有样例核对输入格式和调用方式 |
| [`references/`](references/) | 技能规则与输入输出合同 | 核对输入约定、操作细节与适用边界 |
| [`scripts/`](scripts/) | 开发与维护脚本 | 查找构建、验证或维护的现有命令 |
| [`templates/`](templates/) | 可复用模板 | 按当前职责查阅实现及目录内说明 |

<a id="readme-section-11"></a>

<a id="常见问题"></a>

<a id="readme-detail-35"></a>

## ❓ 常见问题

**会自动上传或发布视频吗？** 演示、校验、页面生成都不会。可选交接也只生成文件。使用外部发布集成前先检查命令和授权范围。

**它会自动写标题吗？** AI 助手根据材料准备候选，脚本负责校验和呈现。也可以手工填写 JSON。

**单文件 HTML 能直接分享吗？** 界面、平台图标和视频缩略图在 HTML 内，实际视频、封面引用本机路径。只移动 HTML 可能无法播放；项目搬家后重新构建。分享前检查私人内容和目录。

**复制按钮为什么没反应？** 本地文件的剪贴板权限因浏览器而异。浏览器提供授权时按需允许，或手工选择文字复制；不要绕过安全限制。

**编辑后的内容为什么没了？** 草稿跟随浏览器和存储标识。清理浏览器数据、换浏览器或重新构建不同输入可能影响草稿。替换工作台前保存最新选择。

**只想发一个平台可以吗？** 当前页面构建需要四个基础平台，B 站与 YouTube 在旧输入中可省略。可以只使用需要的复制区域；交接脚本支持 `--platform` 指定目标。

**推荐话题一定能增加流量吗？** 没有这样的保证。演示话题只说明合成内容，活动有效期、参与条件和平台规则需要独立核对。

**为什么拖进来的封面无法交接？** 检查角色、比例、绝对路径、大小和哈希。临时图片需要在允许搜索的目录中找到唯一原文件，能预览不等于发布资产已经就绪。

**可以商用吗？** 源码使用 MIT 许可证。平台名称、图标和你自己的素材另有权利边界，见 [第三方说明](THIRD_PARTY_NOTICES.md)。

<a id="readme-section-12"></a>

<a id="隐私验证与维护"></a>

<a id="readme-detail-37"></a>

## 🔒 隐私、验证与维护

公开仓库没有密钥或私人执行记录。构建脚本和页面没有远程网络请求。生成 HTML、选择数据会含本地路径和内容，请保存在私有项目里；AI 服务如何处理材料，需要另外决定。浏览器草稿和剪贴板可能保留你选择的文字。

```bash
python3 scripts/test_build_publish_review.py
python3 scripts/test_yijianfa_handoff.py
```

测试使用临时合成素材，默认离线。只有明确设置 `RUN_YIJIANFA_INTEGRATION=1` 才会调用已安装 CLI 的 prepare，不要随意启用。测试覆盖构建、可用时的 JavaScript 语法、第一帧比例、数量门禁和任务映射，不代替浏览器实看或真实平台发布验收。

私人文件放到仓库外。`output/`、`local/`、环境文件和 Python 缓存已忽略。反馈问题时提供可复现的合成输入，去掉账号信息。许可条款见 [LICENSE](LICENSE)。

<a id="readme-section-13"></a>

<a id="先跑一个安全的演示"></a>

<a id="readme-detail-39"></a>

## 🚀 先运行合成演示

克隆仓库，或下载 ZIP 后解压，保留完整目录。需要 Python 3.10 或更新版本，以及 PATH 中可用的 FFmpeg、FFprobe。Pillow 只用于生成演示图片；Node.js 可选，用于测试生成页面的 JavaScript 语法。通过适合你系统的可信安装渠道准备这些工具。

```bash
python3 -m venv .venv
# macOS/Linux:
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python3 -m pip install -r requirements.txt
python3 scripts/make_demo.py
```

打开 `output/demo/review.html`。里面有一秒钟合成视频、三张合成封面、五个标题、三个正文版本和六个平台的话题区域。你可以选择标题、修改正文、勾选话题，再尝试复制。**这些操作不会发布内容。** 生成器只输出本地路径，不自动打开浏览器或启动服务器。Windows 中若 Python 命令是 `python`，可以把命令里的 `python3` 换为 `python`。

用 `--output-dir /absolute/path/demo` 可以指定演示输出位置。生成文件会包含本机路径，分享或提交前需要检查隐私。

![示意：预览、标题、正文、话题与复制的页面结构](docs/page-map.svg)

workflow 与 page-map 两张 SVG 用于说明流程和页面区域；前面的教学效果图与局部截图用于理解操作，都不表示本次发生了真实发布。
