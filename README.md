# Video Publish Workbench

**Turn a video’s titles, descriptions, hashtags and covers into one local page where you can review and choose before posting.**

[中文说明](README.zh-CN.md) · [Agent instructions](SKILL.md) · [Input example](examples/demo-input.json)

Preparing the same video for several destinations often means switching between notes, cover files and platform-specific copy. This skill lets an AI prepare options and gives you a page for the final decisions. Local generation needs no platform login, API key or publishing CLI. The page currently uses Chinese interface labels; the documentation is available in both languages.

[Detailed capabilities](#readme-section-1) · [See the workbench](#readme-section-2) · [Typical situations](#readme-section-3) · [Install](#readme-section-4) · [Use it with an AI assistant](#readme-section-7) · [FAQ](#readme-section-12) · [Privacy, verification and maintenance](#readme-section-13)

<a id="readme-section-1"></a>

## Detailed capabilities

### Preparation capabilities

- Research comparable content and facts for the user's topic, recording sources, visible metrics and gaps.
- Reuse supplied images or use an available image tool to make topic-specific assets and covers.
- Optionally follow a user-authorized gallery's layout, palette and typography while preserving originals.
- Draft headline, body and hashtag candidates from actual materials, then build the editable workbench.

**Can preparation run from one request?** Yes, when your assistant has the necessary tools, asset permission and budget. It must report missing access or evidence; the static HTML does not call a model by itself.


| Capability | What you can do | Boundary |
| --- | --- | --- |
| Title-only agent mode | Ask for ten directions and a Top 3 | Uses supplied facts; requires an AI assistant |
| Video review titles | Compare and edit five candidates | Shared default length is 16 Unicode characters |
| Description versions | Switch versions, edit each and see character counts | User edits stay in browser storage, not the original input JSON |
| Media preview | Play the local video and compare 3:4, 4:3 and 16:9 covers | Media is referenced from local files, not fully embedded |
| Covers | Select, drag, replace or clear a cover | Temporary uploads need their original files for handoff |
| Six platform sections | Pick separate tags for Xiaohongshu, Douyin, Kuaishou, WeChat Channels, Bilibili and YouTube | Configured limits are repository defaults, not guaranteed current platform policy |
| Copy | Copy titles, grouped descriptions/hashtags or the full information package for AI | Clipboard access depends on browser permission |
| Selection data | Read `window.getPublishReviewSelection()` for current choices and cover metadata | An authorized agent or user must save that JSON; no automatic write-back |
| Validation | Reject missing fields, invalid cover ratios and over-limit input | Does not fact-check claims or inspect platform moderation |
| Optional handoff | Generate separate yijianfa task files after review | Offline task generation does not prove login, upload or publishing works |

Default tag limits are 10 / 5 / 4 / 7 / 10 / 60 for the platforms above. New inputs should contain all six sections; older four/five-platform inputs remain accepted. Actual platform rules must be checked before posting. The public tag library is empty: add only relevant, sourced preferences or activities. No default traffic directory or campaign is contacted.

<a id="readme-section-2"></a>

## See the workbench

![Privacy-masked video pre-publish workbench preview](docs/screenshots/workbench-preview.png)

Review the video and cover variants alongside headline and description options. Choose hashtags separately for each destination before copying the selected package.

This privacy-masked illustration is based on the presentation example. Conversation content and local paths are covered in pale white; the left card is a suggested invocation, not an execution receipt. The detail screenshots below show the actual teaching interface. The example's video content and hashtags are illustrative, not current platform recommendations or evidence of a successful post.

### Compare headlines

![Video headline options and the selected headline](docs/screenshots/choose-title.png)

### Select topics for each platform

![Separate hashtag choices for Xiaohongshu, Douyin and other destinations](docs/screenshots/platform-tags.png)

The rows show separate selections for Xiaohongshu, Douyin, Kuaishou, WeChat Channels, Bilibili and YouTube. Preparing a destination's copy does not publish it or connect an account.

![Illustrative workflow: prepare, review, copy, optional handoff](docs/workflow.svg)

<a id="readme-section-3"></a>

## Typical situations

- You have a finished video and a transcript, but need several title directions and a concise description.
- You post the same clip to multiple platforms and want different hashtags without rewriting the whole description.
- You want to compare vertical and landscape covers before choosing.
- A teammate prepares drafts, while you keep control over the final text and whether it gets posted.

<a id="readme-section-4"></a>

## Install

```bash
npx skills add mileson/video-publish-workbench
```

<a id="readme-section-5"></a>

## Tell your AI what to prepare

Place the complete repository in a Skill directory supported by your assistant. If it supports slash invocation, use the example below. Otherwise ask it to read this repository's `SKILL.md`; slash syntax is assistant-specific, not a button in the generated page.

```text
/video-publish-workbench
Prepare publishing materials for my desk-organization video for beginners.
Research the topic, draft headline/body/hashtag options, and generate missing covers.
If I supply a reference gallery, use its layout and palette, replacing old subjects and copy.
Build the workbench so I can choose and edit. Do not publish.
```

Supply your video and an existing transcript. If transcription is unavailable, the assistant must explain the gap. This workflow generates covers and publishing materials, not a finished video.

| Option | What to request |
|---|---|
| Research | Research first, or use only my supplied material |
| Images | Generate missing assets, or reuse my images |
| Gallery reference | Follow my authorized gallery layout/palette, or use no gallery |
| Full preparation | Start from the topic, prepare research, assets and copy, then build the workbench |

Research and image-production instructions, prompt templates and the local image utility are bundled in this repository. Your assistant supplies authorized browser/search and native image-generation tools. With no such tools, you can still build from existing material. No accounts, provider credentials or author's other private skills are required. Tool availability, login and any paid budget must be handled explicitly.

See [capability origins and scope](docs/capability-origins.md).

[Preparation brief example](examples/preparation-brief.json) is for the Agent; the renderer still uses its original input schema.

<a id="readme-section-6"></a>

## Try a safe demo

Clone the repository or download and extract its ZIP. Keep the whole directory together. You need Python 3.10+, FFmpeg and FFprobe on PATH. Pillow is used only by the synthetic demo generator. Node.js is optional for JavaScript syntax checks. Install these tools through a trusted package source for your operating system.

```bash
python3 -m venv .venv
# macOS/Linux:
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python3 -m pip install -r requirements.txt
python3 scripts/make_demo.py
```

Open `output/demo/review.html` locally. It contains a one-second synthetic video, three synthetic covers, five title options, three body versions and six platform hashtag sections. Choose a title, edit a description, change hashtags and use the copy buttons. **Nothing is posted.** The generator outputs a local path; it does not start a server or browser. Windows users can use `python` instead of `python3` when that is their Python command.

The demo can be regenerated anywhere with `--output-dir /absolute/path/demo`. Generated files contain your local paths, so do not commit or share them without a privacy review.

![Illustrative page map: media, title, body, tags and copy](docs/page-map.svg)

The workflow and page-map SVGs are explanatory diagrams. The teaching previews above show layout and controls, not evidence of a live posting session.

<a id="readme-section-7"></a>

## Use it with an AI assistant

This is an Agent skill plus deterministic Python scripts. An assistant that can read local files and run Python can follow `SKILL.md`; place the whole directory in that assistant’s supported skill directory, or give it the absolute path explicitly. Installation locations depend on your assistant. The scripts do not generate AI copy by themselves.

You can send:

> Read this repository’s SKILL.md. Use my video and transcript to prepare five title options, three description versions and relevant per-platform hashtags. Build the local video pre-publish workbench. Keep the video private, do not upload it or publish anything. Explain any missing transcript or platform evidence.

Give the assistant actual local paths and factual constraints. If transcription, current platform research or cover design is unavailable, it should explain the missing piece and continue with the material you supplied. No separate author-style, secret-vault or publishing skill is required to generate the page.

<a id="readme-section-8"></a>

## Run it with your own input

1. Copy `examples/demo-input.json` to a private project directory.
2. Replace the synthetic content with five title options, descriptions and relevant tags. Keep title and tag counts within the repository’s defaults.
3. Supply the absolute video path. Optionally register cover paths in `video.cover_candidates`, or use the repeatable CLI flags below.
4. Validate, build and open the generated HTML. Keep the video and cover files in place.

```bash
python3 scripts/validate_publish_review.py --input /absolute/path/review-input.json --video /absolute/path/video.mp4
python3 scripts/build_publish_review.py --input /absolute/path/review-input.json --video /absolute/path/video.mp4 --cover-candidate /absolute/path/vertical-3x4.png --bilibili-cover-candidate /absolute/path/landscape-4x3.png --horizontal-cover-candidate /absolute/path/wide-16x9.png --output /absolute/path/project/review.html
```

Omit cover flags when you have no files for that slot. Without a vertical candidate, the builder crops the first frame to 3:4. This is a fallback preview, so check whether the composition is usable. Horizontal slots can stay empty. JSON defaults control which registered cover is selected; simply adding a landscape candidate does not always select it.

<a id="readme-section-9"></a>

## Optional publishing handoff

Most users can copy the reviewed text and post manually. If you have a compatible yijianfa setup, the supplied converter writes tasks from the latest selection; yijianfa is not a default dependency.

```bash
python3 scripts/build_yijianfa_tasks.py --selection /absolute/path/publish-selection.json --video /absolute/path/video.mp4 --browser-context regular --output-dir /absolute/path/tasks
```

This command writes JSON and a manifest. It does not run any generated publishing commands. Confirm your installed CLI’s capabilities, the logged-in account and current destination requirements before executing anything. A live post needs explicit authorization and a verified result URL. `--mode publish` changes generated tasks; it still does not execute them. The offline contract requires 3:4 plus 4:3 for Douyin, and an enabled 16:9 cover for YouTube. It puts YouTube hashtags in the description and leaves task tags empty. These mappings need live readback with your installed adapter.

<a id="readme-section-10"></a>

## Repository map

| Entry | Contents |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Agent instructions and entry point |
| [`assets/`](assets/) | Images and static assets |
| [`capabilities/`](capabilities/) | Preparation capability modules |
| [`docs/`](docs/) | Project documentation and references |
| [`examples/`](examples/) | Example inputs and usage |
| [`references/`](references/) | Skill rules and input/output contracts |
| [`scripts/`](scripts/) | Development and maintenance scripts |
| [`templates/`](templates/) | Reusable templates |

<a id="readme-section-11"></a>

## Further reading

- [Contributing](CONTRIBUTING.md)
- [Security reporting](SECURITY.md)

<a id="readme-section-12"></a>

## FAQ

**Will this upload or post my video?** Local validation, demo and page building do not. Optional handoff only writes task files. Review generated commands before using a publishing integration.

**Does it write the titles for me?** The AI assistant prepares content from your material; the builder validates and renders that content. You can also edit JSON manually.

**Is the page a completely portable single file?** The interface, platform icons and video thumbnail are inside the HTML. The actual video and covers use local paths. Moving the HTML alone can break playback; rebuild after moving your project.

**Why is copying blocked?** Browser security and clipboard permissions differ for local files. Allow copying if your browser offers it, or manually select the text. Do not bypass security restrictions.

**Why did my edits disappear?** Drafts belong to a browser and storage key. Clearing site data, changing browsers or rebuilding different input may change the draft. Export the current selection before replacing a workbench.

**Can I use just one target platform?** The current builder requires four core platform sections; Bilibili and YouTube are optional for legacy compatibility. You can use only the copy section you need. Handoff supports explicit `--platform` filtering.

**Are hashtags guaranteed to increase reach?** No. Demo tags explain the synthetic content. Activity eligibility and current rules need their own evidence.

**Why does cover handoff fail?** Check aspect ratio, role, absolute path and file metadata. A dragged image must resolve to exactly one original file inside the allowed search roots. Previewing an image alone does not make it publishable.

**Can I use it commercially?** The source is MIT licensed. Platform trademarks, icons and your own media have separate rights. See [third-party notices](THIRD_PARTY_NOTICES.md).

<a id="readme-section-13"></a>

## Privacy, verification and maintenance

No credentials or private history are distributed. The builder and template have no remote network fetches. Generated HTML and selection data expose local file paths and content; keep them private. If an AI service processes your material, that service’s data handling is a separate decision. Browser drafts and the clipboard may retain selected text.

```bash
python3 scripts/test_build_publish_review.py
python3 scripts/test_yijianfa_handoff.py
```

Tests use synthetic temporary assets and run offline by default. An installed publishing CLI is contacted only when you explicitly set `RUN_YIJIANFA_INTEGRATION=1`; do not enable it casually. Regression coverage checks construction, JavaScript syntax when Node is available, fallback ratios, capacity failures and task mapping. It does not certify browser layouts or real platform posting.

Keep private files outside the repository. `output/`, `local/`, environment files and Python caches are ignored. Report reproducible bugs with synthetic input and no account details. See [LICENSE](LICENSE) for the MIT terms.
