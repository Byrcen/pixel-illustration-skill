#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
像素风文章配图 - 单张图生成脚本 (apimart / gemini-3-pro-image-preview)

只负责"机械"工作：提交生成任务 -> 轮询到完成 -> 立刻下载图片到本地。
画图 prompt 由 Claude 在 SKILL.md 的流程里生成后传进来。

用法:
  python3 generate.py --prompt "画面描述(已含像素风后缀)" \
                      --out "/Users/cry/Desktop/文章配图/某文章/01_前段.png" \
                      [--size 16:9] [--resolution 2K]

退出码 0 表示成功并已落盘；非 0 表示失败(stderr 有原因)。
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://api.apimart.ai"
MODEL = "gemini-3-pro-image-preview"
POLL_INTERVAL = 5      # 秒，每次轮询间隔
POLL_TIMEOUT = 300     # 秒，最长等待


def load_api_key():
    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(here, "config.json")
    if not os.path.exists(cfg_path):
        sys.exit("找不到 config.json，请在 skill 文件夹里创建并填入 api_key")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    key = (cfg.get("api_key") or "").strip()
    if not key or key.startswith("在这里"):
        sys.exit("config.json 里的 api_key 还没填，请填入你的 apimart key")
    return key


def http_json(method, url, key, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        sys.exit("API 请求失败 HTTP %s: %s" % (e.code, detail))
    except urllib.error.URLError as e:
        sys.exit("网络错误: %s" % e.reason)


def submit_task(key, prompt, size, resolution):
    url = API_BASE + "/v1/images/generations"
    body = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "n": 1,
        "resolution": resolution,
    }
    res = http_json("POST", url, key, body)
    try:
        return res["data"][0]["task_id"]
    except (KeyError, IndexError, TypeError):
        sys.exit("提交任务返回格式异常: %s" % json.dumps(res, ensure_ascii=False))


def poll_task(key, task_id):
    url = API_BASE + "/v1/tasks/%s?language=en" % task_id
    waited = 0
    while waited <= POLL_TIMEOUT:
        res = http_json("GET", url, key)
        data = res.get("data", {})
        status = data.get("status")
        if status == "completed":
            imgs = (data.get("result") or {}).get("images") or []
            if not imgs:
                sys.exit("任务完成但没有返回图片")
            url_field = imgs[0].get("url")
            # url 可能是数组，也可能是字符串
            if isinstance(url_field, list):
                if not url_field:
                    sys.exit("任务完成但图片 url 为空")
                return url_field[0]
            return url_field
        if status in ("failed", "cancelled"):
            sys.exit("任务 %s: %s" % (status, json.dumps(data, ensure_ascii=False)))
        # pending / processing
        progress = data.get("progress", 0)
        sys.stderr.write("  ...生成中 status=%s progress=%s\n" % (status, progress))
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL
    sys.exit("等待超时(%ss)，任务仍未完成" % POLL_TIMEOUT)


def download(image_url, out_path):
    # 按图片真实后缀修正输出文件名(模型可能返回 .jpg/.webp 等)
    url_ext = os.path.splitext(image_url.split("?")[0])[1].lower()
    if url_ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        base, _ = os.path.splitext(out_path)
        out_path = base + url_ext
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    req = urllib.request.Request(image_url)
    # 图床会拦截 python-urllib 的默认 UA，必须伪装成浏览器
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            content = resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        sys.exit("下载图片失败: %s" % e)
    with open(out_path, "wb") as f:
        f.write(content)
    return out_path, len(content)


def main():
    p = argparse.ArgumentParser(description="apimart 像素风配图生成")
    p.add_argument("--prompt", required=True, help="完整画图描述(已含像素风格后缀)")
    p.add_argument("--out", required=True, help="输出图片的本地完整路径(.png)")
    p.add_argument("--size", default="16:9", help="比例，如 16:9 / 1:1 / 4:3 / auto")
    p.add_argument("--resolution", default="2K", help="清晰度: 1K / 2K / 4K")
    args = p.parse_args()

    key = load_api_key()
    sys.stderr.write("提交任务 (size=%s, resolution=%s)...\n" % (args.size, args.resolution))
    task_id = submit_task(key, args.prompt, args.size, args.resolution)
    sys.stderr.write("task_id=%s，开始轮询...\n" % task_id)
    image_url = poll_task(key, task_id)
    saved_path, size_bytes = download(image_url, args.out)
    sys.stderr.write("完成 ✅ 已保存: %s (%d KB)\n" % (saved_path, size_bytes // 1024))
    # stdout 只输出最终路径，方便上层程序读取
    print(saved_path)


if __name__ == "__main__":
    main()
