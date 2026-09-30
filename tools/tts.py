#!/usr/bin/env python3
"""Neural-voice audio for WhyItLands briefings (Kokoro, voice af_heart).

python3 tools/tts.py plan            -> prints a JSON list of slugs whose audio is missing or stale
python3 tools/tts.py make <slug>     -> writes site/assets/audio/<slug>.m4a and <slug>.meta.json
python3 tools/tts.py apply           -> copies minutes/hash from .meta.json files into the briefing JSONs
Needs kokoro-onnx, soundfile, numpy, ffmpeg and kokoro-v1.0.onnx + voices-v1.0.bin in the working directory.
"""
import glob, hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BR = os.path.join(ROOT, "content", "briefings")
AUD = os.path.join(ROOT, "site", "assets", "audio")
SAY = {"VAT", "NATO", "ASEAN", "APEC", "OPEC", "IATA", "CENTCOM", "UNCTAD", "MERCOSUR", "ECLAC", "IMEC", "BEUC", "MOFCOM", "PGSA", "IOSS", "UKGT", "OFCOM", "CEPAL", "SISSE", "USMCA", "EUCA"}
CUR = {"€": "euros", "$": "dollars", "£": "pounds", "¥": "yen"}


def acr(m):
    k = m.group(1)
    return k if (k in SAY or len(k) > 5 or not k.isalpha()) else " ".join(k)


def money(m):
    unit = {"bn": " billion", "billion": " billion", "m": " million", "million": " million", "k": " thousand"}.get((m.group(3) or "").strip().lower(), "")
    return f"{m.group(2)}{unit} {CUR[m.group(1)]}"


def clean(s):
    s = re.sub(r"\[\[([^\]]+)\]\]", acr, s)
    s = re.sub(r"([€$£¥])\s?([\d.,]+)\s?(bn|billion|million|m|k)?\b", money, s)
    s = s.replace("%", " percent").replace("&", " and ").replace("/", " or ").replace("–", " to ")
    return re.sub(r"\s+", " ", s).strip()


def texts(b):
    out = [b["title"] + ".", clean(b["dek"]), "Key points."] + [clean(k) for k in b["keypoints"]]
    for x in b["body"]:
        if "p" in x: out.append(clean(x["p"]))
        elif "h" in x: out.append(clean(x["h"]) + ".")
        elif "views" in x: out += [clean(v["actor"]) + ". " + clean(v["stance"]) + " " + clean(v["text"]) for v in x["views"]]
        elif "doctrines" in x: out += [clean(d["school"]) + ". " + clean(d["reading"]) + " For the parcel: " + clean(d["parcel"]) for d in x["doctrines"]]
        elif "scenarios" in x: out += ["Scenarios."] + [clean(s["name"]) + ". " + clean(s["text"]) for s in x["scenarios"]]
        elif "csuite" in x: out += ["For the C-suite."] + [clean(c) for c in x["csuite"]]
        elif "impact" in x: out.append("Bottom line. " + clean(x["impact"]))
    return out


def text_hash(b):
    return hashlib.sha1("\n".join(texts(b)).encode()).hexdigest()[:12]


def load():
    return {json.load(open(f))["slug"]: (f, json.load(open(f))) for f in sorted(glob.glob(os.path.join(BR, "*.json")))}


def plan():
    todo = []
    for slug, (f, b) in load().items():
        a = b.get("audio") or {}
        if not os.path.exists(os.path.join(AUD, slug + ".m4a")) or a.get("hash") != text_hash(b):
            todo.append(slug)
    print(json.dumps(todo))


def make(slug):
    import numpy as np, soundfile as sf
    from kokoro_onnx import Kokoro
    f, b = load()[slug]
    k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
    out, sr = [], 24000
    for p in texts(b):
        parts, buf = [], ""
        for c in re.split(r"(?<=[.!?:;])\s+", p):
            if len(buf) + len(c) > 280 and buf: parts.append(buf); buf = c
            else: buf = (buf + " " + c).strip()
        if buf: parts.append(buf)
        for c in parts:
            a, sr = k.create(c, voice="af_heart", speed=1.0, lang="en-us")
            out += [a, np.zeros(int(sr * .25))]
        out.append(np.zeros(int(sr * .45)))
    w = np.concatenate(out)
    os.makedirs(AUD, exist_ok=True)
    sf.write("tmp.wav", w, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "tmp.wav", "-af", "loudnorm=I=-16:TP=-1.5", "-c:a", "aac", "-b:a", "56k", "-movflags", "+faststart", os.path.join(AUD, slug + ".m4a")], check=True)
    json.dump({"minutes": max(1, round(len(w) / sr / 60)), "hash": text_hash(b)}, open(os.path.join(AUD, slug + ".meta.json"), "w"))
    print(slug, round(len(w) / sr / 60, 1), "min")


def apply():
    for slug, (f, b) in load().items():
        m = os.path.join(AUD, slug + ".meta.json")
        if os.path.exists(m):
            meta = json.load(open(m))
            b["audio"] = {"src": f"/assets/audio/{slug}.m4a", "minutes": meta["minutes"], "hash": meta["hash"]}
            json.dump(b, open(f, "w"), ensure_ascii=False, indent=2)
            os.remove(m)


if __name__ == "__main__":
    {"plan": lambda: plan(), "make": lambda: make(sys.argv[2]), "apply": lambda: apply()}[sys.argv[1]]()
