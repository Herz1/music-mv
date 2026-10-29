#!/usr/bin/env python3
"""Extract review sheets from a rendered mp4 (skill 09): tile frames every STEP s."""
import subprocess, sys, os
from PIL import Image, ImageDraw
src, step, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
os.makedirs(out, exist_ok=True)
import re
p = subprocess.run(["ffmpeg","-hide_banner","-i",src], capture_output=True, text=True)
m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
dur = int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3))
times = [round(i*step,2) for i in range(int(dur/step)+1) if i*step < dur-0.15]
frames=[]
for t in times:
    path=os.path.join(out,f"f{t:07.2f}.jpg")
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(t),"-i",src,"-frames:v","1","-q:v","4",path],check=True)
    frames.append((t,Image.open(path)))
w,h=frames[0][1].size; tw,th=320,int(320*h/w)
cols=5; rows=(len(frames)+cols-1)//cols
sheet=Image.new("RGB",(cols*tw,rows*(th+20)),(8,10,22)); d=ImageDraw.Draw(sheet)
for i,(t,im) in enumerate(frames):
    thm=im.resize((tw,th)); x=(i%cols)*tw; y=(i//cols)*(th+20)
    sheet.paste(thm,(x,y)); d.text((x+6,y+th+3),f"{t:.0f}s",fill=(255,220,150))
sheet.save(os.path.join(out,"sheet.jpg"),quality=86)
print(src,"dur",dur,"frames",len(frames),"->",os.path.join(out,"sheet.jpg"))
