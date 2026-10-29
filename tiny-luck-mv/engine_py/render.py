#!/usr/bin/env python3
"""Render stills / contact sheets / full video (skill 08 equivalent, ffmpeg pipe, x264)."""
import os, sys, argparse, subprocess, json, time
sys.path.insert(0, os.path.dirname(__file__))
from mv_engine import Engine
from PIL import Image, ImageDraw

def stills(times, outdir, sheet, W=960, H=540, vertical=False):
    eng=Engine(W,H,vertical=vertical); os.makedirs(outdir,exist_ok=True)
    imgs=[]
    for t in times:
        im=eng.render(t); p=os.path.join(outdir,f"t{t:07.2f}.png"); im.save(p); imgs.append((t,im)); print(f"still {t:.2f}s ok",flush=True)
    cols=4; tw,th=W//2,H//2; rows=(len(imgs)+cols-1)//cols
    sh=Image.new("RGB",(cols*tw,rows*(th+22)),(8,10,22)); d=ImageDraw.Draw(sh)
    for i,(t,im) in enumerate(imgs):
        thumb=im.resize((tw,th)); x=(i%cols)*tw; y=(i//cols)*(th+22)
        sh.paste(thumb,(x,y)); d.text((x+8,y+th+4),f"{t:.2f}s",fill=(255,220,150))
    sp=os.path.join(outdir,sheet+".jpg"); sh.save(sp,quality=88); print("sheet",sp)

def video(out, W=1280, H=720, fps=24, vertical=False, start=0.0, end=224.04, crf=20, preset="veryfast"):
    eng=Engine(W,H,vertical=vertical)
    audio=os.path.join(os.path.dirname(__file__),"..","audio","song.wav")
    dur=end-start; n=int(dur*fps)
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(fps),"-i","-",
         "-ss",str(start),"-i",audio,
         "-filter_complex","[1:a]apad=whole_dur="+str(dur)+"[a]",
         "-map","0:v","-map","[a]","-c:v","libx264","-preset",preset,"-crf",str(crf),
         "-pix_fmt","yuv420p","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709",
         "-c:a","aac","-b:a","256k","-ar","48000","-t",str(dur),"-movflags","+faststart",out]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    t0=time.time()
    try:
        for i in range(n):
            frame=eng.render(start+i/fps)
            proc.stdin.write(frame.tobytes())
            if i%240==0: print(f"frame {i}/{n} {time.time()-t0:.0f}s elapsed",flush=True)
        proc.stdin.close(); err=proc.stderr.read().decode()[-2000:]; proc.wait()
    except BrokenPipeError:
        print(proc.stderr.read().decode()[-3000:]); raise
    print("ffmpeg rc",proc.returncode); print(err[-800:])
    print(f"done {out} in {time.time()-t0:.0f}s")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",default="stills")
    ap.add_argument("--times",default=""); ap.add_argument("--out",default="")
    ap.add_argument("--outdir",default="render/stills/pass1"); ap.add_argument("--sheet",default="pass1")
    ap.add_argument("--width",type=int,default=960); ap.add_argument("--height",type=int,default=540)
    ap.add_argument("--fps",type=int,default=24); ap.add_argument("--start",type=float,default=0.0)
    ap.add_argument("--end",type=float,default=224.04); ap.add_argument("--crf",type=int,default=20)
    ap.add_argument("--preset",default="veryfast"); ap.add_argument("--vertical",action="store_true")
    a=ap.parse_args()
    if a.mode=="stills":
        times=[float(x) for x in a.times.split(",") if x]
        stills(times,a.outdir,a.sheet,a.width,a.height,a.vertical)
    else:
        video(a.out,a.width,a.height,a.fps,a.vertical,a.start,a.end,a.crf,a.preset)
