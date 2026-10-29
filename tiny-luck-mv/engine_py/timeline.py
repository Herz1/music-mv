# -*- coding: utf-8 -*-
"""Shot timeline for TINY LUCK fan MV (skill phases 5-6: storyboard -> timeline).
Times come from analysis/lyrics_translation.json (lyric onsets snapped to beats/bars).
Each lyric line maps to 1-2 shots; choruses split for beat-cut density.
Shot fields: bg, char, h=(start,end frame-height fraction), x=(start,end center fraction),
text: bottom|behind|center|slam|small|none, grade, fx list, cam=(bg zoom start,end)
"""
import json, os
ROOT = os.path.join(os.path.dirname(__file__), "..")

# per-lyric directives: lyric index -> list of shot specs (see analysis output for indices)
D = {
 0: [dict(kind="title", bg="bg_sky", char=None, text="small", grade="night", fx=["motes_low"])],
 1: [dict(bg="bg_wagon", char="pose_back", h=(0.60,0.64), x=(0.50,0.50), text="small", grade="warm", fx=["motes_low"])],
 2: [dict(bg="bg_night_field", char="pose_back", h=(0.74,0.80), x=(0.50,0.50), text="bottom", grade="night", fx=["motes_low"], cam=(1.04,1.12))],
 3: [dict(bg="bg_wagon", char="pose_sing_close", h=(1.02,1.08), x=(0.50,0.50), text="bottom", grade="warm", fx=[])],
 4: [dict(bg="bg_sky", char="pose_reach", h=(0.68,0.74), x=(0.52,0.52), text="bottom", grade="night", fx=["motes_low"])],
 5: [dict(bg="bg_night_field", char="pose_hurt", h=(0.82,0.86), x=(0.50,0.50), text="bottom", grade="dark", fx=[])],
 6: [dict(bg="bg_night_field", char="pose_reach", h=(0.78,0.98), x=(0.50,0.50), text="slam", grade="night", fx=["motes"], cam=(1.05,1.28))],
 7: [dict(bg="bg_wagon", char="pose_sing_close", h=(1.10,1.18), x=(0.50,0.50), text="bottom", grade="storm", fx=["ca"])],
 8: [dict(bg="bg_sky", char="pose_reach", h=(0.86,0.94), x=(0.50,0.50), text="behind", grade="night", fx=["starburst","motes"]),
     dict(bg="bg_night_field", char="REF_master", h=(0.92,1.00), x=(0.50,0.50), text="bottom", grade="night", fx=["motes","starburst_small"])],
 9: [dict(bg="bg_night_field", char="pose_back", h=(0.70,0.76), x=(0.44,0.44), companions=True, text="bottom", grade="night", fx=["motes"]),
     dict(bg="bg_wagon", char="REF_master", h=(0.88,0.94), x=(0.50,0.50), text="bottom", grade="warm", fx=["motes"])],
 10:[dict(bg="bg_wagon", char="pose_hold_light", h=(1.04,1.12), x=(0.50,0.50), text="bottom", grade="warm", fx=["glow"]),
     dict(bg="bg_night_field", char="pose_hold_light", h=(0.78,0.84), x=(0.50,0.50), text="bottom", grade="night", fx=["glow","motes"])],
 11:[dict(bg="bg_night_field", char="pose_sing_close", h=(1.14,1.22), x=(0.50,0.50), text="bottom", grade="darkred", fx=["star_rain_low"])],
 12:[dict(bg="bg_sky", char="pose_smile", h=(0.96,1.02), x=(0.50,0.50), text="center", grade="memory", fx=["motes_low"])],
 13:[dict(bg="bg_night_field", char="pose_back", h=(0.72,0.76), x=(0.36,0.58), text="bottom", grade="night", fx=["motes_low"], cam=(1.10,1.04))],
 14:[dict(bg="bg_night_field", char="REF_master", h=(0.54,0.58), x=(0.50,0.50), text="bottom", grade="night", fx=["motes_low"])],
 15:[dict(bg="bg_wagon", char="pose_sing_close", h=(0.98,1.04), x=(0.50,0.50), text="bottom", grade="warm", fx=[])],
 16:[dict(bg="bg_wagon", char="pose_sing_close", h=(1.06,1.12), x=(0.52,0.52), text="bottom", grade="warm", fx=["glow_low"])],
 17:[dict(bg="bg_sky", char="pose_reach", h=(0.80,1.00), x=(0.50,0.50), text="slam", grade="night", fx=["motes"], cam=(1.05,1.30))],
 18:[dict(bg="bg_night_field", char="pose_hold_light", h=(0.90,0.97), x=(0.50,0.50), text="bottom", grade="night", fx=["glow","motes_low"])],
 19:[dict(bg="bg_sky", char="pose_back", h=(0.76,0.82), x=(0.50,0.50), text="bottom", grade="dark", fx=["star_rain"])],
 20:[dict(bg="bg_night_field", char="pose_hurt", h=(0.92,0.98), x=(0.50,0.50), text="bottom", grade="darkred", fx=["heart_crack","shake"])],
 21:[dict(bg="bg_wagon", char="pose_sing_close", h=(1.18,1.26), x=(0.50,0.50), text="center", grade="warm", fx=[])],
 22:[dict(bg="bg_night_field", char="pose_hold_light", h=(1.12,1.20), x=(0.50,0.50), text="bottom", grade="night", fx=["stitch","glow"])],
 23:[dict(bg="bg_night_field", char="pose_smile", h=(0.94,1.00), x=(0.50,0.50), companions=True, text="behind", grade="memory", fx=["motes"])],
 24:[dict(kind="typo_black", bg=None, char=None, text="echo", grade="black", fx=[])],
 25:[dict(kind="typo_black", bg=None, char=None, text="slam_white", grade="black", fx=[])],
 26:[dict(bg="bg_wagon", char="REF_master", h=(0.72,0.78), x=(0.46,0.46), companions=True, text="bottom", grade="warm", fx=["motes"])],
 27:[dict(bg="bg_sky", char="pose_reach", h=(0.90,0.98), x=(0.50,0.50), text="behind", grade="night", fx=["starburst","shooting","motes"]),
     dict(bg="bg_sky", char="REF_master", h=(0.94,1.02), x=(0.50,0.50), text="bottom", grade="night", fx=["starburst_small","shooting"])],
 28:[dict(bg="bg_night_field", char="REF_master", h=(0.84,0.90), x=(0.46,0.46), companions=True, text="bottom", grade="night", fx=["motes","shooting"]),
     dict(bg="bg_wagon", char="pose_smile", h=(0.94,1.00), x=(0.50,0.50), companions=True, text="bottom", grade="warm", fx=["motes","glow_low"])],
 29:[dict(bg="bg_wagon", char="pose_hold_light", h=(1.06,1.14), x=(0.50,0.50), text="bottom", grade="warm", fx=["glow","motes"]),
     dict(bg="bg_sky", char="pose_hold_light", h=(0.80,0.86), x=(0.50,0.50), text="bottom", grade="night", fx=["starburst_small","glow"])],
 30:[dict(bg="bg_night_field", char="pose_back", h=(0.62,0.50), x=(0.50,0.56), text="bottom", grade="dark", fx=["motes_low"], dissolve=True)],
 31:[dict(bg="bg_night_field", char="pose_sing_close", h=(1.14,1.20), x=(0.50,0.50), text="bottom", grade="memory", fx=["motes"]),
     dict(bg="bg_sky", char="pose_smile", h=(1.00,1.06), x=(0.50,0.50), text="center", grade="memory", fx=["starburst_small","motes"], fade_in_char=True)],
}
SPECIALS_AFTER = {
 "interlude": [  # inserted between lyric 12 and 13 by time (88.5-98.8)
   dict(bg="bg_wagon", char="pose_back", h=(0.48,0.52), x=(0.62,0.60), text="none", grade="warm", fx=["motes"], note="interlude"),
   dict(bg="bg_night_field", char=None, text="none", grade="night", fx=["motes"], note="interlude")],
 "outro": [
   dict(bg="bg_night_field", char="pose_back", h=(0.44,0.40), x=(0.50,0.52), text="none", grade="night", fx=["motes_low"], note="outro_credits"),
   dict(bg="bg_sky", char=None, text="none", grade="night", fx=["last_star"], note="outro_star")],
}

def load_lyrics():
    with open(os.path.join(ROOT,"analysis","lyrics_translation.json"),encoding="utf-8") as f:
        return json.load(f)

def build_shots():
    lyrics = load_lyrics()
    shots=[]; n=0
    def add(start,end,spec,lyric_idx=None):
        nonlocal n; n+=1
        s=dict(spec); s.update(id=f"s{n:02d}", start=round(float(start),3), end=round(float(end),3), lyric=lyric_idx)
        s.setdefault("kind","illust"); s.setdefault("text","bottom"); s.setdefault("grade","night"); s.setdefault("fx",[])
        shots.append(s)
    for i,line in enumerate(lyrics):
        start=line["start"]
        end=lyrics[i+1]["start"] if i+1<len(lyrics) else 208.5
        if i==12: end=88.5
        if i==13: start=98.8
        specs=D[i]
        # split line duration among its shots (55/45 for two)
        bounds=[start]
        for k in range(len(specs)):
            frac=(k+1)/len(specs) if len(specs)==1 else (0.55 if k==0 else 1.0)
            bounds.append(start+(end-start)*frac)
        for k,spec in enumerate(specs): add(bounds[k],bounds[k+1],spec,lyric_idx=i)
        if i==12:
            add(88.5,93.6,SPECIALS_AFTER["interlude"][0]); add(93.6,98.8,SPECIALS_AFTER["interlude"][1])
    add(208.5,215.0,SPECIALS_AFTER["outro"][0]); add(215.0,221.04,SPECIALS_AFTER["outro"][1])
    add(221.04,224.04,dict(kind="endcard",bg=None,char=None,text="none",grade="black",fx=[]))
    return lyrics, shots

if __name__=="__main__":
    lyrics,shots=build_shots()
    print(len(shots),"shots")
    for s in shots: print(s["id"],s["start"],s["end"],s["kind"],s.get("bg"),s.get("char"),"lyric=",s["lyric"],"text=",s["text"])
