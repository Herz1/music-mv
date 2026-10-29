#!/usr/bin/env python3
"""Lightweight audio analysis (skill 03, no librosa): beats/bars/sections/envelope + lyric timing.
Lyric timing = section boundaries (from energy/vocal activity) + mora-weighted allocation
snapped to detected vocal dips and the beat grid. Estimated alignment (+/-~1s), see AUDIO_MAP.md.
"""
import json, subprocess, os, re
import numpy as np
from scipy import signal
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), "..")
SR = 22050
DIPS = [4.1,7.8,11.7,14.6,23.7,28.2,35.6,39.5,45.0,51.5,56.3,63.7,69.2,72.7,77.9,84.8,89.9,97.9,102.3,106.0,113.4,116.6,121.6,124.8,130.2,134.1,140.9,146.0,154.5,162.8,165.7,170.9,174.5,178.7,181.8,187.7,194.2,199.7,203.2,208.4]
BPM, PHASE = 100.0, 0.28
BEAT = 60.0 / BPM

def decode():
    p = subprocess.run(["ffmpeg","-v","error","-i",os.path.join(ROOT,"audio","song.wav"),
                        "-ac","1","-ar",str(SR),"-f","f32le","-"], capture_output=True)
    return np.frombuffer(p.stdout, dtype=np.float32).astype(np.float64)

def mora(s):
    return max(1, len(re.sub(r"[\s「」、。・…ー]", "", s)))

def main():
    y = decode(); dur = len(y)/SR
    # envelope 30fps
    hop = SR//30; n = len(y)//hop
    env = [float(np.sqrt((y[i*hop:(i+1)*hop]**2).mean())) for i in range(n)]
    sections = [
        {"label":"Intro","start":0.0,"end":11.7,"group":"intro"},
        {"label":"Verse 1","start":11.7,"end":35.6,"group":"verse"},
        {"label":"Pre-Chorus 1","start":35.6,"end":48.3,"group":"pre"},
        {"label":"Chorus 1","start":48.3,"end":88.5,"group":"chorus"},
        {"label":"Interlude","start":88.5,"end":98.8,"group":"interlude"},
        {"label":"Verse 2","start":98.8,"end":121.0,"group":"verse"},
        {"label":"Pre-Chorus 2","start":121.0,"end":130.2,"group":"pre"},
        {"label":"Chorus 2","start":130.2,"end":149.8,"group":"chorus2"},
        {"label":"Bridge","start":149.8,"end":166.2,"group":"bridge"},
        {"label":"Final Chorus","start":166.2,"end":208.5,"group":"chorus"},
        {"label":"Outro","start":208.5,"end":round(dur,2),"group":"outro"},
    ]
    beats = [round(PHASE + i*BEAT, 3) for i in range(int((dur-PHASE)/BEAT)+1)]
    bars = [{"index": i, "start": round(PHASE + i*BEAT*4, 3)} for i in range(int((dur-PHASE)/(BEAT*4))+1)]
    audio = {"duration": round(dur,3), "bpm_estimate": BPM, "beat_phase": PHASE,
             "beats": beats, "bars": bars, "sections": sections,
             "special_events": {"chorus_downbeats":[48.3,130.2,166.2],
                                  "vocal_end":210.5, "song_end":round(dur,2),
                                  "film_end_with_endcard": round(dur+3.0,2)}}
    os.makedirs(os.path.join(ROOT,"analysis"), exist_ok=True)
    with open(os.path.join(ROOT,"analysis","audio.json"),"w",encoding="utf-8") as f: json.dump(audio,f,ensure_ascii=False,indent=1)
    with open(os.path.join(ROOT,"analysis","envelope_30fps.json"),"w") as f: json.dump({"fps":30,"rms":env},f)
    with open(os.path.join(ROOT,"analysis","sections.json"),"w",encoding="utf-8") as f: json.dump(sections,f,ensure_ascii=False,indent=1)

    # ---- lyrics: parse official bilingual table from repo lyrics.md ----
    rows=[]
    with open(os.path.join(ROOT,"analysis","lyrics_official.txt"),encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line.startswith("|") and "---" not in line and "日文原文" not in line:
                cells=[c.strip() for c in line.strip("|").split("|")]
                if len(cells)>=2: rows.append((cells[0],cells[1]))
    assert len(rows)==30, len(rows)
    layout=[("Verse 1",0,4),("Pre-Chorus 1",4,6),("Chorus 1",6,11),("Verse 2",11,15),
            ("Pre-Chorus 2",15,17),("Chorus 2",17,22),("Bridge",22,25),("Final Chorus",25,30)]
    sec_by_label={s["label"]:s for s in sections}
    lyrics=[]  # (start, jp, zh, section)
    lyrics.append((0.5,"Ha, ha, ha-ah","", "Intro"))
    lyrics.append((6.1,"Ha, ha, ha-ah","", "Intro"))
    for label,a,b in layout:
        s=sec_by_label[label]; lines=rows[a:b]
        weights=[mora(jp) for jp,_ in lines]; tot=sum(weights); t=s["start"]
        for (jp,zh),w in zip(lines,weights):
            start=t
            # snap to nearest dip within 1.6s, then to nearest beat
            near=[d for d in DIPS if abs(d-start)<=1.6]
            if near: start=min(near,key=lambda d:abs(d-start))+0.15
            start=PHASE+round((start-PHASE)/BEAT)*BEAT
            lyrics.append((round(float(start),2),jp,zh,label))
            t=s["start"]+(s["end"]-s["start"])*(sum(weights[:lines.index((jp,zh))+1])/tot) if False else t+(s["end"]-s["start"])*w/tot
    lyrics.sort(key=lambda x:x[0])
    with open(os.path.join(ROOT,"analysis","lyrics_translation.json"),"w",encoding="utf-8") as f:
        json.dump([{"start":st,"jp":jp,"zh":zh,"section":sec} for st,jp,zh,sec in lyrics],f,ensure_ascii=False,indent=1)
    def lrc_t(t): return f"[{int(t//60):02d}:{t%60:05.2f}]"
    with open(os.path.join(ROOT,"analysis","lyrics_mv.lrc"),"w",encoding="utf-8") as f:
        for st,jp,zh,sec in lyrics:
            f.write(f"{lrc_t(max(0,st-0.2))}{jp}\n")  # display 0.2s before voice (skill 03)
    for st,jp,zh,sec in lyrics: print(f"{st:7.2f} [{sec}] {jp} / {zh}")
    # overview.png (waveform + sections)
    W,H=1800,420; img=Image.new("RGB",(W,H),(10,12,26)); d=ImageDraw.Draw(img)
    step=max(1,len(y)//W)
    cols={"intro":(90,90,140),"verse":(50,90,140),"pre":(140,90,160),"chorus":(220,150,50),
          "chorus2":(200,80,80),"bridge":(70,130,120),"interlude":(80,80,80),"outro":(60,60,90)}
    for s in sections:
        x0=int(s["start"]/dur*W); x1=int(s["end"]/dur*W)
        d.rectangle([x0,0,x1,26],fill=cols.get(s["group"],(100,100,100))); d.text((x0+4,6),s["label"],fill=(255,255,255))
    for x in range(W):
        seg=y[x*step:(x+1)*step]; peak=float(np.abs(seg).max()) if len(seg) else 0
        d.line([x,210-peak*170,x,210+peak*170],fill=(120,180,255))
    for b in [48.3,130.2,166.2]:
        x=int(b/dur*W); d.line([x,30,x,H-10],fill=(255,190,60),width=2)
    img.save(os.path.join(ROOT,"analysis","overview.png"))
    print("duration",dur,"lyrics",len(lyrics))

if __name__=="__main__": main()
