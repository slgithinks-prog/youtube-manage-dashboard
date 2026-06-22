#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
채널 관리 도구 (공개 dashboard repo).

3명이 각자 터미널에서 관리할 유튜브 채널을 추가/삭제하고
git push 하면, 다음 일일 수집부터 대시보드에 반영된다.

사용 예:
  python manage.py list
  python manage.py add --handle @채널핸들 --name "표시이름"
  python manage.py add --id UCxxxxxxxx --name "표시이름"
  python manage.py remove --id UCxxxxxxxx
"""
import os
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.join(HERE, "channels.json")


def load():
    if not os.path.exists(CH):
        return {"channels": []}
    with open(CH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(CH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"저장됨: {CH}")


def cmd_list(_):
    chs = load().get("channels", [])
    if not chs:
        print("(등록된 채널 없음)")
    for i, c in enumerate(chs, 1):
        ident = c.get("channel_id") or c.get("handle") or "?"
        print(f"{i}. {c.get('name','(이름없음)')}  [{ident}]")


def cmd_add(a):
    if not (a.id or a.handle):
        print("오류: --id 또는 --handle 중 하나는 필요합니다.")
        return
    data = load()
    entry = {"name": a.name or ""}
    if a.id:
        entry["channel_id"] = a.id
    if a.handle:
        entry["handle"] = a.handle
    if a.member_note:
        entry["member_note"] = a.member_note
    data.setdefault("channels", []).append(entry)
    save(data)
    print("채널 추가 완료. git commit/push 하면 다음 수집부터 반영됩니다.")


def cmd_remove(a):
    data = load()
    chs = data.get("channels", [])
    before = len(chs)
    data["channels"] = [c for c in chs
                        if c.get("channel_id") != a.id and c.get("handle") != a.id]
    save(data)
    print(f"제거됨 {before - len(data['channels'])}건.")


def build_parser():
    p = argparse.ArgumentParser(description="채널 관리 도구")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    a = sub.add_parser("add")
    a.add_argument("--id", help="채널ID (UC...)")
    a.add_argument("--handle", help="핸들 (@name)")
    a.add_argument("--name", help="대시보드 표시 이름")
    a.add_argument("--member-note", dest="member_note", help="공개 가능한 메모")
    a.set_defaults(func=cmd_add)
    r = sub.add_parser("remove")
    r.add_argument("--id", required=True, help="채널ID 또는 핸들")
    r.set_defaults(func=cmd_remove)
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
