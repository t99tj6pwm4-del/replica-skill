"""Effect 3 Speed hook test: 3.000 s, 90 frames. Picture from his clip, audio = his song (+ our sfx)."""
import subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path("/home/user/replica-skill/fonzi-gym-video-editor")
sys.path.insert(0, str(ROOT / "scripts"))
import style_fx as sf  # zoom(), W, H

SRC = ROOT / "input/icloud_0dfgTLSk.mp4"
SONG = ROOT / "songs/alfonso_music_063BT4Xb.mp3"
OUT = Path.home() / "workspace/upload_staging/2026-11-21_speed_test.mp4"
W, H, FPS = 1080, 1920, 30
A0, A1 = 0, 24            # normal start: src frames 0-23 (0.8 s)
SPEED, BOUT = 15, 22      # burst: 22 output frames from 330 src frames (24-353)
B0, B1 = A1, A1 + SPEED * BOUT
C0, C1 = B1, B1 + (90 - (A1 - A0) - BOUT)   # normal after landing: src 354-397
LAND = (A1 - A0) + BOUT   # output frame 46
DROP = 65.445             # drop in the song (librosa onset peak + RMS jump)
SONG_IN = DROP - LAND / FPS
BLEND = 20                # frames averaged per burst frame (CapCut Blend ~20)

tmp = ROOT / "output/hooks/.speed_pic.mkv"
fc = (f"[0:v]scale={W}:{H}:flags=lanczos,setsar=1,split=3[a][b][c];"
      f"[a]trim=start_frame={A0}:end_frame={A1},setpts=PTS-STARTPTS[va];"
      f"[b]trim=start_frame={B0 - BLEND + SPEED}:end_frame={B1},setpts=PTS-STARTPTS,tmix=frames={BLEND},"
      f"select='gte(n\\,{BLEND - 1})*eq(mod(n-{BLEND - 1}\\,{SPEED})\\,0)',setpts=N/{FPS}/TB[vb];"
      f"[c]trim=start_frame={C0}:end_frame={C1},setpts=PTS-STARTPTS[vc];"
      f"[va][vb][vc]concat=n=3:v=1:a=0,fps={FPS}[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[v]",
                "-c:v", "ffv1", "-pix_fmt", "rgb24", tmp], check=True)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", tmp, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     check=True, capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).copy()
assert len(fr) == 90, len(fr)
# small impact shake on the landing (style_fx snap shake, no flash, gentler punch)
shake = [(14, -10), (-12, 8), (8, -6), (-5, 4), (3, -2), (0, 0)]
for d, (dx, dy) in enumerate(shake):
    k = LAND + d
    f = sf.zoom(fr[k].astype(np.float32) / 255, 1 + 0.05 * (1 - d / 5) ** 2, W / 2, H / 2, dx, dy)
    fr[k] = (np.clip(f, 0, 1) * 255).astype(np.uint8)
pic = ROOT / "output/hooks/.speed_pic2.mkv"
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                      "-r", str(FPS), "-i", "-", "-c:v", "ffv1", str(pic)], stdin=subprocess.PIPE)
p.stdin.write(fr.tobytes()); p.stdin.close(); assert p.wait() == 0
w_at, i_at = 0.95, LAND / FPS
afc = (f"[1:a]atrim=start={SONG_IN:.4f}:duration=3,asetpts=PTS-STARTPTS,aresample=48000,"
       f"aformat=channel_layouts=stereo,afade=t=in:d={2/FPS:.4f}[s];"
       f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=-14dB,adelay={int(w_at*1000)}|{int(w_at*1000)}[w];"
       f"[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=-10dB,adelay={round(i_at*1000)}|{round(i_at*1000)}[i];"
       f"[s][w][i]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89,atrim=duration=3[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", SONG, "-i", ROOT / "sfx/whoosh.wav",
                "-i", ROOT / "sfx/impact.wav", "-filter_complex", afc, "-map", "0:v", "-map", "[a]",
                "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "192k", "-t", "3", "-movflags", "+faststart", OUT], check=True)
tmp.unlink(); pic.unlink()
print(f"landing frame {LAND} (t={LAND/FPS:.4f}s), song in {SONG_IN:.4f} out {SONG_IN+3:.4f}, drop {DROP}")
print(f"src: A 0-{A1-1}, burst {B0}-{B1-1} x{SPEED} blend {BLEND}, C {C0}-{C1-1} ({C0/30:.3f}-{C1/30:.3f}s)")
