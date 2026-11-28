#!/usr/bin/env python3
"""Post the approved video to Facebook Page Fonzi.stays.fit and Instagram @fonzi.stays.fit (Meta Graph API).

    python3 scripts/post_to_meta.py --dry-run             # stage + show exactly what would be posted. Posts nothing.
    python3 scripts/post_to_meta.py                       # really post the Reel (needs QA pass + Alfonso's approval)
    python3 scripts/post_to_meta.py --carousel            # also post the exercises carousel
    python3 scripts/post_to_meta.py --platform instagram  # one platform only

Safety rules built in:
  * tokens come from .env only (see .env.example); nothing is hardcoded and tokens are never printed
  * refuses unless the Final Approval Agent passed the video AND output/staged/approval.json matches it
  * never posts the same video twice: posted/ledger.json remembers every post (exact file, same raw
    footage, or a visually identical re-export are all refused)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import LEDGER, OUT, ROOT, die, fingerprint, fingerprint_distance, load_json, rel, save_json, sha256  # noqa: E402

STAGED = OUT / "staged"


def load_env() -> dict:
    env = {}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("META_PAGE_ID", "META_PAGE_ACCESS_TOKEN", "META_IG_USER_ID", "META_GRAPH_VERSION"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


class Graph:
    def __init__(self, env: dict):
        import requests
        self.r = requests
        self.token = env["META_PAGE_ACCESS_TOKEN"]
        self.v = env.get("META_GRAPH_VERSION", "v24.0")
        self.base = f"https://graph.facebook.com/{self.v}"

    def call(self, method: str, path: str, **params) -> dict:
        files = params.pop("_files", None)
        url = path if path.startswith("http") else f"{self.base}/{path}"
        kw = {"params": {**params, "access_token": self.token}} if method == "GET" else {
            "data": {**params, "access_token": self.token}, "files": files}
        res = self.r.request(method, url, timeout=120, **kw)
        try:
            body = res.json()
        except ValueError:
            body = {"raw": res.text[:300]}
        if res.status_code >= 400 or "error" in body:
            err = body.get("error", body)
            die(f"Meta API error on {path.split('?')[0]}: {err.get('message', err)} (code {err.get('code')})")
        return body

    def upload(self, url: str, video: Path) -> dict:
        size = video.stat().st_size
        with open(video, "rb") as fh:
            res = self.r.post(url, data=fh, timeout=900, headers={
                "Authorization": f"OAuth {self.token}", "offset": "0", "file_size": str(size)})
        if res.status_code >= 400:
            die(f"Meta upload failed ({res.status_code}): {res.text[:300]}")
        return res.json()

    # --- Facebook Page ---
    def facebook_reel(self, page: str, video: Path, caption: str) -> str:
        start = self.call("POST", f"{page}/video_reels", upload_phase="start")
        self.upload(start["upload_url"], video)
        self.call("POST", f"{page}/video_reels", upload_phase="finish", video_id=start["video_id"],
                  video_state="PUBLISHED", description=caption)
        return start["video_id"]

    def facebook_photos(self, page: str, slides: list[Path]) -> list[str]:
        ids = []
        for s in slides:
            with open(s, "rb") as fh:
                ids.append(self.call("POST", f"{page}/photos", published="false", _files={"source": fh})["id"])
        return ids

    def facebook_carousel(self, page: str, photo_ids: list[str], caption: str) -> str:
        media = {f"attached_media[{i}]": json.dumps({"media_fbid": pid}) for i, pid in enumerate(photo_ids)}
        return self.call("POST", f"{page}/feed", message=caption, **media)["id"]

    # --- Instagram ---
    def wait_ready(self, container: str):
        for _ in range(60):
            st = self.call("GET", container, fields="status_code,status").get("status_code")
            if st == "FINISHED":
                return
            if st == "ERROR":
                die("Instagram could not process the upload")
            time.sleep(5)
        die("Instagram took too long to process the upload")

    def instagram_reel(self, ig: str, video: Path, caption: str) -> str:
        c = self.call("POST", f"{ig}/media", media_type="REELS", upload_type="resumable", caption=caption,
                      share_to_feed="true")
        self.upload(c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{self.v}/{c['id']}", video)
        self.wait_ready(c["id"])
        return self.call("POST", f"{ig}/media_publish", creation_id=c["id"])["id"]

    def instagram_carousel(self, ig: str, image_urls: list[str], caption: str) -> str:
        kids = [self.call("POST", f"{ig}/media", image_url=u, is_carousel_item="true")["id"] for u in image_urls]
        c = self.call("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)
        self.wait_ready(c["id"])
        return self.call("POST", f"{ig}/media_publish", creation_id=c["id"])["id"]

    def photo_url(self, photo_id: str) -> str:
        return self.call("GET", photo_id, fields="images")["images"][0]["source"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="stage and show the plan; post nothing")
    ap.add_argument("--platform", choices=["both", "facebook", "instagram"], default="both")
    ap.add_argument("--carousel", action="store_true", help="also post the exercises carousel")
    a = ap.parse_args()
    platforms = ["facebook", "instagram"] if a.platform == "both" else [a.platform]

    video, post = STAGED / "final_edit.mp4", load_json(STAGED / "post.json", default={})
    report = load_json(OUT / "qa_report.json", default={})
    problems = []
    if report.get("verdict") != "PASS" or not video.exists() or not post:
        problems.append("the Final Approval Agent has not passed and staged a video (output/staged/ is empty)")
    vsha = sha256(video) if video.exists() else None
    if vsha and vsha != report.get("sha256"):
        problems.append("the staged video is not the file QA checked")
    approval = load_json(STAGED / "approval.json", default={})
    approved = bool(vsha) and approval.get("sha256") == vsha
    if not approved:
        problems.append("Alfonso has not approved this video yet (no matching output/staged/approval.json)")

    # never post the same video twice
    ledger = load_json(LEDGER, default={"posted": []})
    fp = fingerprint(video) if video.exists() else []
    entry = None
    for e in ledger["posted"]:
        same = (e.get("sha256") == vsha or (post.get("source_sha256") and e.get("source_sha256") == post["source_sha256"])
                or (fp and e.get("fingerprint") and fingerprint_distance(fp, e["fingerprint"]) <= 6.0))
        if same:
            entry = e
            break
    todo = [p for p in platforms if not (entry and entry.get("reel", {}).get(p))]
    carousel_todo = [p for p in platforms if a.carousel and not (entry and entry.get("carousel", {}).get(p))]
    if entry and not todo and not carousel_todo:
        problems.append(f"DUPLICATE: this video was already posted on {entry.get('posted_at')} "
                        f"({', '.join(k for k in entry.get('reel', {}))}). Not posting it again.")

    env = load_env()
    need = ["META_PAGE_ACCESS_TOKEN"] + (["META_PAGE_ID"] if "facebook" in platforms or a.carousel else []) + (
        ["META_IG_USER_ID"] if "instagram" in platforms else [])
    missing = [k for k in need if not env.get(k)]
    caption = post.get("caption", "")
    car = post.get("carousel") or {}
    slides = [ROOT / s for s in car.get("slides", [])]
    if a.carousel and len(slides) < 2:
        problems.append("--carousel asked for, but this video has no carousel (needs 2+ exercises)")

    if a.dry_run:
        plan = {"mode": "DRY RUN - nothing posted", "video": rel(video) if video.exists() else None, "sha256": vsha,
                "would_post_reel_to": {"facebook": "Page Fonzi.stays.fit", "instagram": "@fonzi.stays.fit"},
                "platforms_pending": todo, "caption": caption,
                "carousel": {"slides": car.get("slides", []), "caption": car.get("caption", ""),
                             "will_post": bool(a.carousel)} if car else None,
                "approved_by_alfonso": approved, "env_missing": missing,
                "blocking_a_real_post": problems + ([f"missing in .env: {', '.join(missing)}"] if missing else [])}
        if video.exists():
            save_json(STAGED / "dry_run.json", plan)
        print(json.dumps(plan, indent=2))
        print("\nDRY RUN: nothing was sent to Meta.")
        return

    if problems:
        die("not posting:\n  - " + "\n  - ".join(problems))
    if missing:
        die(f"missing in .env: {', '.join(missing)} (copy .env.example to .env and fill it in)")

    g = Graph(env)
    if entry is None:
        entry = {"sha256": vsha, "source_sha256": post.get("source_sha256"), "fingerprint": fp,
                 "title": post.get("title"), "posted_at": time.strftime("%Y-%m-%d %H:%M:%S"), "reel": {}, "carousel": {}}
        ledger["posted"].append(entry)

    def remember(kind: str, platform: str, post_id: str):
        entry.setdefault(kind, {})[platform] = post_id
        save_json(LEDGER, ledger)   # saved after every single post so a crash can never cause a double post
        print(f"posted {kind} to {platform}: {post_id}")

    if "facebook" in todo:
        remember("reel", "facebook", g.facebook_reel(env["META_PAGE_ID"], video, caption))
    if "instagram" in todo:
        remember("reel", "instagram", g.instagram_reel(env["META_IG_USER_ID"], video, caption))
    if carousel_todo:
        photo_ids = g.facebook_photos(env["META_PAGE_ID"], slides)
        if "instagram" in carousel_todo:
            urls = [g.photo_url(p) for p in photo_ids]
            remember("carousel", "instagram", g.instagram_carousel(env["META_IG_USER_ID"], urls, car.get("caption", caption)))
        if "facebook" in carousel_todo:
            remember("carousel", "facebook", g.facebook_carousel(env["META_PAGE_ID"], photo_ids, car.get("caption", caption)))
    print("done. Recorded in posted/ledger.json")


if __name__ == "__main__":
    main()
