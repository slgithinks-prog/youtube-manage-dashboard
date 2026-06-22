#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 채널 일일 자료 수집기 (비공개 repo에서 실행)

channels.json에 등록된 채널들의 자료를 YouTube Data API v3로 수집해서
대시보드(공개 repo)가 읽을 JSON으로 출력한다.

출력 위치: 환경변수 OUTPUT_DIR (기본 ../youtube-manage-dashboard/data)
  - channels.json : 최신 스냅샷 (채널·영상 현황)
  - history.json  : 날짜별 누적 (조회수/구독자 추이 그래프용)

표준 라이브러리만 사용한다 (pip 설치 불필요).
"""
import os
import sys
import json
import datetime
import urllib.parse
import urllib.request
import urllib.error

API = "https://www.googleapis.com/youtube/v3"
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "data")
HERE = os.path.dirname(os.path.abspath(__file__))

# 채널당 최근 몇 개 영상을 가져올지
RECENT_VIDEOS = int(os.environ.get("RECENT_VIDEOS", "10"))


def api_get(endpoint, params):
    params = dict(params)
    params["key"] = API_KEY
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print(f"[API 오류] {endpoint} {e.code}: {body}", file=sys.stderr)
        raise


def load_channels():
    path = os.path.join(HERE, "channels.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("channels", [])


def resolve_channel_id(entry):
    """channel_id가 있으면 그대로, 없으면 handle(@name)로 조회."""
    cid = (entry.get("channel_id") or "").strip()
    if cid:
        return cid
    handle = (entry.get("handle") or "").strip()
    if not handle:
        return None
    if not handle.startswith("@"):
        handle = "@" + handle
    data = api_get("channels", {"part": "id", "forHandle": handle})
    items = data.get("items", [])
    return items[0]["id"] if items else None


def fetch_channel(cid, display_name):
    """채널 기본정보 + 최근 영상 목록 수집."""
    info = api_get("channels", {
        "part": "snippet,statistics,contentDetails",
        "id": cid,
    })
    items = info.get("items", [])
    if not items:
        print(f"[건너뜀] 채널 없음: {cid}", file=sys.stderr)
        return None
    ch = items[0]
    snip = ch.get("snippet", {})
    stats = ch.get("statistics", {})
    uploads = ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")

    # 업로드 재생목록에서 최근 영상 ID 수집
    video_ids = []
    if uploads:
        pl = api_get("playlistItems", {
            "part": "contentDetails",
            "playlistId": uploads,
            "maxResults": RECENT_VIDEOS,
        })
        video_ids = [it["contentDetails"]["videoId"] for it in pl.get("items", [])]

    videos = []
    if video_ids:
        vinfo = api_get("videos", {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
        })
        for v in vinfo.get("items", []):
            vs = v.get("snippet", {})
            vst = v.get("statistics", {})
            videos.append({
                "video_id": v["id"],
                "title": vs.get("title", ""),
                "published_at": vs.get("publishedAt", ""),
                "views": int(vst.get("viewCount", 0)),
                "likes": int(vst.get("likeCount", 0)),
                "comments": int(vst.get("commentCount", 0)),
                "url": f"https://youtu.be/{v['id']}",
            })
        videos.sort(key=lambda x: x["published_at"], reverse=True)

    return {
        "channel_id": cid,
        "name": display_name or snip.get("title", ""),
        "title": snip.get("title", ""),
        "thumbnail": snip.get("thumbnails", {}).get("default", {}).get("url", ""),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "recent_videos": videos,
        "channel_url": f"https://www.youtube.com/channel/{cid}",
    }


def main():
    if not API_KEY:
        print("[오류] 환경변수 YOUTUBE_API_KEY 가 없습니다.", file=sys.stderr)
        sys.exit(1)

    today = datetime.date.today().isoformat()
    channels_in = load_channels()
    if not channels_in:
        print("[경고] channels.json 에 등록된 채널이 없습니다.", file=sys.stderr)

    collected = []
    for entry in channels_in:
        cid = resolve_channel_id(entry)
        if not cid:
            print(f"[건너뜀] 채널ID 확인 실패: {entry}", file=sys.stderr)
            continue
        data = fetch_channel(cid, entry.get("name", ""))
        if data:
            data["member_note"] = entry.get("member_note", "")  # 공개 가능한 메모만
            collected.append(data)
            print(f"[수집됨] {data['name']} (구독 {data['subscribers']:,})")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1) 최신 스냅샷
    snapshot = {"updated_at": today, "channels": collected}
    with open(os.path.join(OUTPUT_DIR, "channels.json"), "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    # 2) 날짜별 추이 누적
    hist_path = os.path.join(OUTPUT_DIR, "history.json")
    history = []
    if os.path.exists(hist_path):
        try:
            with open(hist_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    today_row = {
        "date": today,
        "channels": {
            c["channel_id"]: {
                "name": c["name"],
                "subscribers": c["subscribers"],
                "total_views": c["total_views"],
            } for c in collected
        },
    }
    history = [h for h in history if h.get("date") != today]  # 같은 날 중복 제거
    history.append(today_row)
    history.sort(key=lambda h: h["date"])
    history = history[-365:]  # 최근 1년치만 보관
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"\n완료: 채널 {len(collected)}개, 출력 {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
