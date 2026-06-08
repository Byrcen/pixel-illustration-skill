# Pixel Illustration Skill · 像素风文章配图生成 Skill

> 写完一篇文章后,自动按 **前 30% / 中间 30% / 末尾 30%** 三段内容,各生成一张**像素风**插画——一句话出图,串起文章叙事。

这是一个给 [Claude Code](https://claude.com/claude-code) 用的 Skill。它让 Claude 读懂你的文章,自动切成三段、为每段挑一个最适合视觉化的画面、写好像素风 prompt,再调用 [apimart](https://apimart.ai) 的 `gemini-3-pro-image-preview` 模型出图,自动下载到桌面。

---

## ✨ 特性

- **零操心配图**:给一篇文章(文件或粘贴正文),自动产出 3 张插画,分别对应开头 / 中间 / 结尾。
- **统一像素风**:复古游戏质感、有限色板、色彩温暖明亮、构图干净——风格后缀已固化,出图风格稳定一致。
- **叙事感**:三张图主题各不相同,能把文章的起承转合串起来。
- **图内中文**:画面中若出现文字,一律简体中文。
- **尺寸可调**:默认 16:9 / 2K,每次可临时指定比例(`1:1`、`9:16` 等)与清晰度(`1K`/`2K`/`4K`)。
- **纯标准库**:出图脚本只用 Python 标准库,无需 `pip install`。

## 🎨 风格

像素风 pixel art:复古游戏画面质感,清晰的像素颗粒与有限色板,色彩温暖明亮,氛围亲和、有故事感和生活气息。**不**写实摄影、**不**赛博朋克/霓虹/暗黑。构图干净、主体突出、留白舒适,适合内容平台配图。

## 📦 文件结构

| 文件 | 作用 |
| --- | --- |
| `SKILL.md` | 给 Claude 看的执行说明(切段 / 写 prompt / 调脚本的核心逻辑) |
| `generate.py` | 出图脚本:提交任务 → 轮询完成 → 下载落盘(纯标准库) |
| `config.example.json` | 配置模板,复制为 `config.json` 后填入你的 key |
| `config.json` | 你的本地 API key(已被 `.gitignore` 忽略,**不会**进入仓库) |
| `使用说明.md` | 面向使用者的中文速查 |

## 🚀 快速开始

### 1. 获取并安装

```bash
git clone https://github.com/Byrcen/pixel-illustration-skill.git
```

把整个文件夹放到 Claude Code 能访问到的位置(例如桌面)。

### 2. 配置 API Key(只需一次)

复制配置模板,填入你的 [apimart](https://apimart.ai) key:

```bash
cp config.example.json config.json
```

编辑 `config.json`:

```json
{
  "api_key": "你的-apimart-key"
}
```

> ⚠️ `config.json` 已被 `.gitignore` 排除,不会被提交。请勿把真实 key 写进任何会上传的文件。

### 3. 在 Claude Code 里使用

直接对 Claude 说,例如:

- 「用这个配图 skill 给这篇文章配图」+ 粘贴正文
- 「用配图 skill,文章在 `~/Desktop/我的文章.md`」
- 想改尺寸就补一句:「这次用 `1:1`」「要 `4K`」

Claude 会:**读文章 → 切三段 → 各写一个像素风 prompt → 依次调 `generate.py` 出图**。

### 图片保存位置

```
~/Desktop/文章配图/<文章名>/
├── 01_前段.png
├── 02_中段.png
└── 03_末段.png
```

每篇文章一个子文件夹。

## 🛠 脚本单独使用(可选)

`generate.py` 也能脱离 Claude 单独跑,生成单张图:

```bash
python3 generate.py \
  --prompt "<完整画面描述,已含像素风后缀>" \
  --out "/Users/you/Desktop/文章配图/示例/01_前段.png" \
  --size 16:9 \
  --resolution 2K
```

- `--size`:`16:9` / `1:1` / `4:3` / `3:4` / `9:16` / `auto`
- `--resolution`:`1K` / `2K` / `4K`
- 成功时 stdout 打印保存路径、退出码 `0`;失败时退出码非 `0` 且 stderr 给出原因。

## ⚙️ 技术细节

- 出图接口:`POST https://api.apimart.ai/v1/images/generations`(提交)、`GET /v1/tasks/{task_id}`(轮询)
- 模型:`gemini-3-pro-image-preview`
- 流程:提交任务 → 每 5s 轮询 → 完成后**立即**下载(图片 URL 24 小时过期,必须当场下载)
- 认证:`Authorization: Bearer <config.json 里的 api_key>`

## 🔒 安全提醒

- API key 仅存于本地 `config.json`,已通过 `.gitignore` 排除,不会进入版本库。
- 若 key 曾以明文出现在任何可能被上传的文件中,建议到 apimart 后台**作废并重新生成**。

## 📄 许可证

[MIT](LICENSE)
