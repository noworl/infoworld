#!/usr/bin/env python3
"""
YouTube 新影片檢查器
檢查指定頻道是否有新影片，回傳標題與縮圖
"""

import json
import os
import subprocess
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from googleapiclient.discovery import build

# 設定
API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("請設定環境變數 YOUTUBE_API_KEY")

ROOT = Path(__file__).parent.parent
HISTORY_FILE = ROOT / "data" / "checked_videos.json"
THUMBNAIL_DIR = ROOT / "thumbnails"
CHANNELS_FILE = ROOT / "data" / "channels.json"
OUTPUT_FILE = ROOT / "new_videos.html"


def load_checked_videos() -> dict:
    """載入已檢查過的影片記錄"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checked_videos(data: dict):
    """儲存已檢查過的影片記錄"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_channel_id(youtube, channel_input: str) -> str:
    """
    從頻道網址或名稱取得頻道 ID
    支援格式：
    - 頻道 ID (UC...)
    - 頻道網址 (youtube.com/channel/UC...)
    - 自訂網址 (youtube.com/@username)
    - 使用者名稱 (@username)
    """
    # 如果已經是頻道 ID 格式
    if channel_input.startswith("UC") and len(channel_input) == 24:
        return channel_input

    # 處理 @username 格式
    if channel_input.startswith("@"):
        username = channel_input[1:]
    elif "youtube.com/@" in channel_input:
        username = channel_input.split("@")[-1].split("/")[0].split("?")[0]
    elif "youtube.com/channel/" in channel_input:
        return channel_input.split("channel/")[-1].split("/")[0].split("?")[0]
    else:
        username = channel_input

    # 使用 search API 尋找頻道
    request = youtube.search().list(
        part="snippet",
        q=username,
        type="channel",
        maxResults=1
    )
    response = request.execute()

    if response.get("items"):
        return response["items"][0]["snippet"]["channelId"]

    raise ValueError(f"找不到頻道: {channel_input}")


def get_latest_videos(youtube, channel_id: str, max_results: int = 5) -> list:
    """取得頻道最新影片列表"""
    # 先取得頻道的上傳播放清單 ID
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()

    if not response.get("items"):
        raise ValueError(f"找不到頻道: {channel_id}")

    uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # 取得播放清單中的影片
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        video_id = snippet["resourceId"]["videoId"]

        # 取得最高解析度的縮圖
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("maxres", {}).get("url") or
            thumbnails.get("high", {}).get("url") or
            thumbnails.get("medium", {}).get("url") or
            thumbnails.get("default", {}).get("url", "")
        )

        videos.append({
            "video_id": video_id,
            "title": snippet["title"],
            "published_at": snippet["publishedAt"],
            "thumbnail_url": thumbnail_url,
            "channel_title": snippet["channelTitle"],
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    return videos


def format_date(iso_date: str) -> str:
    """將 ISO 日期格式化為易讀格式"""
    dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d")


def is_this_week(iso_date: str) -> bool:
    """判斷影片是否在近 7 天內發布"""
    dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) - dt < timedelta(days=7)


def generate_html(all_results: dict, output_file=OUTPUT_FILE):
    """生成 HTML 檔案，縮圖在滑鼠懸停時顯示"""
    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube 新影片</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            color: #333;
        }}
        h1 {{ font-size: 1.4rem; font-weight: 600; }}
        h2 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 5px; font-size: 1rem; font-weight: 600; }}
        .video-item {{
            position: relative;
            margin: 10px 0;
        }}
        .video-link {{
            color: #0066cc;
            text-decoration: none;
            font-size: 0.9rem;
        }}
        .video-link:hover {{
            text-decoration: underline;
        }}
        .video-link.new {{
            background-color: #dbeafe;
            padding: 0 3px;
            border-radius: 2px;
        }}
        .video-date {{
            color: #888;
            font-size: 0.75rem;
            margin-left: 8px;
        }}
        .thumbnail-popup {{
            display: none;
            position: absolute;
            left: 0;
            top: 100%;
            z-index: 100;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border-radius: 8px;
            overflow: hidden;
        }}
        .thumbnail-popup img {{
            width: 320px;
            height: auto;
            display: block;
        }}
        .video-item:hover .thumbnail-popup {{
            display: block;
        }}
        .update-time {{
            color: #888;
            font-size: 0.8rem;
        }}
    </style>
</head>
<body>
    <h1>YouTube 新影片</h1>
    <p class="update-time">更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
"""

    total_videos = sum(len(videos) for videos in all_results.values())
    if total_videos == 0:
        html += "    <p>沒有新影片</p>\n"
    else:
        for channel, videos in all_results.items():
            if not videos:
                continue

            channel_title = videos[0].get('channel_title', channel)
            html += f"    <h2>{channel_title}</h2>\n"

            for video in videos:
                title = video["title"]
                url = video["url"]
                thumbnail = video.get("thumbnail_url", "")
                date = format_date(video["published_at"])
                link_class = "video-link new" if is_this_week(video["published_at"]) else "video-link"

                html += f"""    <div class="video-item">
        <a class="{link_class}" href="{url}" target="_blank">{title}</a>
        <span class="video-date">{date}</span>
        <div class="thumbnail-popup">
            <img src="{thumbnail}" alt="縮圖">
        </div>
    </div>
"""

    html += """</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n已輸出至 {output_file}")
    return output_file


def publish_to_github(source_file=OUTPUT_FILE) -> bool:
    """git add / commit / push new_videos.html"""
    original_dir = os.getcwd()
    try:
        os.chdir(ROOT)
        rel_file = "new_videos.html"

        result = subprocess.run(
            ["git", "status", "--porcelain", rel_file],
            capture_output=True, text=True
        )
        if not result.stdout.strip():
            print("沒有變更需要發佈")
            return True

        subprocess.run(["git", "add", rel_file], check=True)
        commit_msg = f"更新 YouTube 新影片 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 已發佈到 GitHub")
            return True
        else:
            print(f"❌ Push 失敗: {result.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失敗: {e}")
        return False
    finally:
        os.chdir(original_dir)


def download_thumbnail(video: dict, output_dir: Path) -> str:
    """下載影片縮圖"""
    output_dir.mkdir(parents=True, exist_ok=True)

    thumbnail_url = video["thumbnail_url"]
    if not thumbnail_url:
        return ""

    # 建立檔名（移除不合法字元）
    safe_title = "".join(c for c in video["title"] if c.isalnum() or c in " -_").strip()
    filename = f"{video['video_id']}_{safe_title[:50]}.jpg"
    filepath = output_dir / filename

    try:
        response = requests.get(thumbnail_url, timeout=10)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        return str(filepath)
    except requests.RequestException as e:
        print(f"下載縮圖失敗: {e}")
        return ""


def check_new_videos(channel_input: str, download_thumbnails: bool = True) -> list:
    """
    檢查頻道是否有新影片

    Args:
        channel_input: 頻道 ID、網址或 @username
        download_thumbnails: 是否下載縮圖到本地

    Returns:
        新影片列表，包含標題、網址和縮圖路徑
    """
    youtube = build("youtube", "v3", developerKey=API_KEY)

    # 取得頻道 ID
    channel_id = get_channel_id(youtube, channel_input)
    print(f"頻道 ID: {channel_id}")

    # 載入已檢查過的影片
    checked = load_checked_videos()
    checked_ids = set(checked.get(channel_id, []))

    # 取得最新影片
    videos = get_latest_videos(youtube, channel_id)

    # 找出新影片
    new_videos = []
    for video in videos:
        if video["video_id"] not in checked_ids:
            if download_thumbnails:
                video["thumbnail_path"] = download_thumbnail(video, THUMBNAIL_DIR)
            new_videos.append(video)
            checked_ids.add(video["video_id"])

    # 更新記錄
    checked[channel_id] = list(checked_ids)
    save_checked_videos(checked)

    return new_videos


def load_channels() -> list:
    """從設定檔載入要追蹤的頻道列表"""
    if CHANNELS_FILE.exists():
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("channels", [])
    return []


def print_video_info(video: dict, index: int):
    """印出影片資訊"""
    print(f"  [{index}] {video['title']}")
    print(f"      網址: {video['url']}")
    print(f"      發布時間: {video['published_at']}")
    if video.get("thumbnail_path"):
        print(f"      縮圖: {video['thumbnail_path']}")
    elif video.get("thumbnail_url"):
        print(f"      縮圖網址: {video['thumbnail_url']}")
    print()


def check_all_channels(download_thumbnails: bool = True, publish: bool = True) -> dict:
    """檢查所有設定檔中的頻道"""
    channels = load_channels()
    if not channels:
        print(f"找不到頻道設定檔 {CHANNELS_FILE} 或頻道列表為空")
        return {}

    all_results = {}
    total_new = 0

    print(f"開始檢查 {len(channels)} 個頻道...\n")
    print("=" * 60)

    for channel in channels:
        print(f"\n頻道: {channel}")
        print("-" * 40)
        try:
            new_videos = check_new_videos(channel, download_thumbnails=download_thumbnails)
            all_results[channel] = new_videos

            if new_videos:
                print(f"發現 {len(new_videos)} 部新影片:")
                for i, video in enumerate(new_videos, 1):
                    print_video_info(video, i)
                total_new += len(new_videos)
            else:
                print("沒有新影片")

        except Exception as e:
            print(f"錯誤: {e}")
            all_results[channel] = []

    print("=" * 60)
    print(f"\n總計: 發現 {total_new} 部新影片")

    # 生成 HTML 檔案並發佈
    if total_new > 0:
        generate_html(all_results)
        if publish:
            publish_to_github()

    return all_results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="檢查 YouTube 頻道新影片")
    parser.add_argument("channel", nargs="?", help="頻道 ID、網址或 @username（不指定則檢查 channels.json 中的所有頻道）")
    parser.add_argument("--no-download", action="store_true", help="不下載縮圖")
    parser.add_argument("--reset", action="store_true", help="重設該頻道的檢查記錄")
    parser.add_argument("--all", "-a", action="store_true", help="檢查 channels.json 中的所有頻道")
    parser.add_argument("--no-publish", action="store_true", help="不自動發佈到 GitHub")
    parser.add_argument("--publish-only", action="store_true", help="只發佈現有的 HTML 檔案（不檢查新影片）")
    args = parser.parse_args()

    # 只發佈模式
    if args.publish_only:
        if OUTPUT_FILE.exists():
            publish_to_github()
        else:
            print(f"找不到 {OUTPUT_FILE}，請先執行檢查")
        return 0

    # 如果沒有指定頻道或使用 --all，檢查所有頻道
    if args.all or (not args.channel and not args.reset):
        check_all_channels(download_thumbnails=not args.no_download, publish=not args.no_publish)
        return 0

    if args.reset:
        if not args.channel:
            print("請指定要重設的頻道")
            return 1
        checked = load_checked_videos()
        youtube = build("youtube", "v3", developerKey=API_KEY)
        try:
            channel_id = get_channel_id(youtube, args.channel)
            if channel_id in checked:
                del checked[channel_id]
                save_checked_videos(checked)
                print(f"已重設頻道 {channel_id} 的檢查記錄")
        except Exception as e:
            print(f"錯誤: {e}")
        return 0

    try:
        new_videos = check_new_videos(args.channel, download_thumbnails=not args.no_download)

        if new_videos:
            print(f"\n發現 {len(new_videos)} 部新影片:\n")
            for i, video in enumerate(new_videos, 1):
                print_video_info(video, i)
            generate_html({args.channel: new_videos})
            if not args.no_publish:
                publish_to_github()
        else:
            print("沒有新影片")

    except Exception as e:
        print(f"錯誤: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
