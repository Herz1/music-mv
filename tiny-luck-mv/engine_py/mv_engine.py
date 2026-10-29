# -*- coding: utf-8 -*-
"""Deterministic MV renderer (Python adaptation of the skill's Canvas/WebGL engine).
Every frame is a pure function of song time t: seeded particles, closed-form motion,
beat-grid cuts. Layers: scene(bg+grade) -> behind-text -> companions -> character ->
foreground text/HUD -> post(vignette/grain/CA). See docs/CONCEPT.md.
"""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

HERE = os.path.dirname(__file__); ROOT = os.path.join(HERE, "..")
from timeline import build_shots, load_lyrics

TITLE, ARTIST = "TINY LUCK", "八木海莉"
CREDIT = "作詞：八木海莉　作曲・編曲：eba　歌：八木海莉"
BEATS = None

def _font(name, size, weight=400):
    f = ImageFont.truetype(os.path.join(HERE, "fonts", name), int(size))
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f

class Engine:
    def __init__(self, W, H, vertical=False):
        self.W, self.H, self.vertical = W, H, vertical
        self.lyrics, self.shots = build_shots()
        with open(os.path.join(ROOT, "analysis", "audio.json"), encoding="utf-8") as fh:
            self.beats = json.load(fh)["beats"]
        self.bg_cache, self.char_cache = {}, {}
        self.scale = W / 1280.0
        self.f_serif = lambda s, w=600: _font("NotoSerifJP.ttf", s*self.scale if False else s, w)
        self._mk_post()
        # deterministic particle fields (closed-form, index-seeded)
        self.stars = [( (i*0.6180339887)%1.0, (i*0.7548776662)%1.0, 0.5+((i*7)%10)/14.0, i*1.7) for i in range(110)]
        self.motes = [( (i*0.3819660113)%1.0, (i*0.6180339887)%1.0, 6+((i*13)%22), 0.008+((i*7)%10)*0.0016, i*2.3) for i in range(46)]

    # ---------- assets ----------
    def bg(self, name):
        key=(name,self.W,self.H)
        if key not in self.bg_cache:
            im = Image.open(os.path.join(ROOT,"assets","bg",name+".png")).convert("RGB")
            tw, th = int(self.W*1.30), int(self.H*1.30)
            s = max(tw/im.width, th/im.height)
            im = im.resize((int(im.width*s+0.5), int(im.height*s+0.5)), Image.LANCZOS)
            self.bg_cache[key]=im
        return self.bg_cache[key]
    def char(self, name, target_h):
        target_h = max(40, int(target_h/8)*8)
        key=(name,target_h)
        if key not in self.char_cache:
            im = Image.open(os.path.join(ROOT,"assets","char",name+".png")).convert("RGBA")
            w = int(im.width*target_h/im.height)
            self.char_cache[key]=im.resize((w,target_h), Image.LANCZOS)
        return self.char_cache[key]
    def _mk_post(self):
        W,H=self.W,self.H
        y,x=np.mgrid[0:H,0:W]
        d=np.sqrt(((x-W/2)/(W*0.72))**2+((y-H/2)/(H*0.72))**2)
        vig=np.clip(1.18-0.55*np.clip(d-0.55,0,None)**1.5,0.72,1.0)
        self.vig=vig.astype(np.float32)
        g=Image.new("L",(256,256),0); gd=ImageDraw.Draw(g)
        for r in range(128,0,-4): gd.ellipse([128-r,128-r,128+r,128+r],fill=int(90*(1-r/128)))
        self.glow=g.resize((512,512))

    # ---------- helpers ----------
    def shot_at(self, t):
        for s in self.shots:
            if s["start"]-0.5 <= t < s["end"]: return s
        return self.shots[-1]
    def line_span(self, idx):
        st=self.lyrics[idx]["start"]
        if idx==12: return st,88.5
        if idx+1 < len(self.lyrics): return st, self.lyrics[idx+1]["start"]
        return st, 208.5
    def beat_pulse(self, t):
        import bisect
        i=bisect.bisect_right(self.beats,t)-1
        if i<0: return 0.0
        return math.exp(-(t-self.beats[i])/0.16)
    @staticmethod
    def lerp(a,b,p): return a+(b-a)*p
    @staticmethod
    def ease(p): return p*p*(3-2*p)

    GRADES={"night":((16,22,54),0.10,0.95,0.98,1.02),"warm":((64,38,10),0.16,1.0,1.02,1.0),
            "dark":((6,8,24),0.30,0.75,0.82,1.05),"darkred":((30,6,10),0.20,0.88,0.90,1.06),
            "memory":((52,40,16),0.13,0.92,1.05,0.98),"storm":((10,12,36),0.14,0.96,0.96,1.12),
            "black":((0,0,0),0.0,1.0,1.0,1.0)}
    def grade(self, im, name):
        col,a,sat,bri,con=self.GRADES.get(name,self.GRADES["night"])
        im=ImageEnhance.Color(im).enhance(sat); im=ImageEnhance.Brightness(im).enhance(bri)
        im=ImageEnhance.Contrast(im).enhance(con)
        if a>0: im=Image.blend(im, Image.new("RGB",im.size,col), a)
        return im

    def draw_bg(self, shot, t, p):
        base=self.bg(shot["bg"]); W,H=self.W,self.H
        z0,z1=shot.get("cam",(1.06,1.14)); z=self.lerp(z0,z1,self.ease(p))
        cw=int(base.width*1.22/z); ch=int(base.height*1.22/z)
        cx=base.width/2 + math.sin(t*0.05+shot["start"])*base.width*0.008 + (p-0.5)*base.width*0.02
        cy=base.height/2 + (p-0.5)*base.height*0.012
        box=(int(min(max(cx-cw/2,0),base.width-cw)), int(min(max(cy-ch/2,0),base.height-ch)))
        return base.crop((box[0],box[1],box[0]+cw,box[1]+ch)).resize((W,H), Image.BILINEAR)

    def star(self, d, cx, cy, r, color, alpha=255, width=2):
        d.line([cx-r,cy,cx+r,cy],fill=color+(alpha,),width=width)
        d.line([cx,cy-r,cx,cy+r],fill=color+(alpha,),width=width)
        r2=r*0.32
        d.line([cx-r2,cy-r2,cx+r2,cy+r2],fill=color+(int(alpha*0.7),),width=max(1,width-1))
        d.line([cx-r2,cy+r2,cx+r2,cy-r2],fill=color+(int(alpha*0.7),),width=max(1,width-1))
        d.ellipse([cx-2,cy-2,cx+2,cy+2],fill=(255,240,200,alpha))

    def text_layer(self, lyric, mode, t, shot):
        """Front lyric layer (JP serif + karaoke gold sweep + ZH sub)."""
        W,H=self.W,self.H; layer=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
        st,en=self.line_span(shot["lyric"]); prog=min(1,max(0,(t-st)/max(0.1,en-st)))
        rel=max(0.0,t-st); fade=min(1,rel/0.35)
        jp,zh=lyric["jp"],lyric["zh"]
        if mode=="center": size,cy=int(54*self.scale),H*0.66
        elif mode=="small": size,cy=int(30*self.scale),H*0.80
        elif mode=="slam": size,cy=int(64*self.scale),H*0.60
        else: size,cy=int(50*self.scale),H*(0.84 if not self.vertical else 0.86)
        f=_font("NotoSerifJP.ttf",size,700)
        # slam scale-in
        slam = 1.0
        if mode in ("slam",) and rel<0.22: slam=1.0+0.35*(1-rel/0.22)
        if slam!=1.0:
            f=_font("NotoSerifJP.ttf",int(size*slam),700)
        tw=d.textlength(jp,font=f); x=(W-tw)/2
        # soft shadow plate for readability
        if True:
            pad=18*self.scale
            plate=Image.new("RGBA",(W,H),(0,0,0,0)); pd=ImageDraw.Draw(plate)
            pd.rounded_rectangle([x-pad,cy-size*0.28,W-x+pad,cy+size*1.75],radius=14,fill=(4,6,18,int(105*fade)))
            layer=Image.alpha_composite(layer,plate); d=ImageDraw.Draw(layer)
        col=(245,242,230,int(255*fade))
        d.text((x+2,cy+2),jp,font=f,fill=(0,0,10,int(200*fade)))
        d.text((x,cy),jp,font=f,fill=col)
        # karaoke gold sweep
        if prog>0:
            mask=Image.new("L",(W,H),0); md=ImageDraw.Draw(mask)
            md.rectangle([x,cy-6,x+tw*min(1,prog*1.06),cy+size*1.35],fill=int(255*fade))
            gold=Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(gold)
            gd.text((x,cy),jp,font=f,fill=(255,196,84,255))
            layer.paste(Image.alpha_composite(layer,gold),(0,0),mask)
            d=ImageDraw.Draw(layer)
        if zh:
            fz=_font("NotoSansSC.ttf",int(24*self.scale),400)
            twz=d.textlength(zh,font=fz)
            d.text(((W-twz)/2,cy+size*1.32),zh,font=fz,fill=(232,226,210,int(205*fade)))
        return layer

    def behind_text(self, lyric, t, shot):
        W,H=self.W,self.H; layer=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
        st,en=self.line_span(shot["lyric"]); rel=max(0,t-st); fade=min(1,rel/0.5)
        size=int(92*self.scale); f=_font("NotoSerifJP.ttf",size,700); jp=lyric["jp"]
        tw=d.textlength(jp,font=f)
        while tw>W*0.94 and size>30:
            size=int(size*0.92); f=_font("NotoSerifJP.ttf",size,700); tw=d.textlength(jp,font=f)
        d.text(((W-tw)/2,H*0.20),jp,font=f,fill=(255,214,120,int(120*fade)))
        return layer

    # ---------- main ----------
    def render(self, t):
        W,H=self.W,self.H; shot=self.shot_at(t)
        p=min(1,max(0,(t-shot["start"])/max(0.1,shot["end"]-shot["start"])))
        pulse=self.beat_pulse(t)
        kind=shot.get("kind","illust")
        if kind in ("typo_black","endcard") or shot.get("bg") is None:
            frame=Image.new("RGB",(W,H),(3,4,10))
        else:
            frame=self.draw_bg(shot,t,p).convert("RGB")
            frame=self.grade(frame,shot["grade"])
        layer_all=Image.new("RGBA",(W,H),(0,0,0,0))
        fx=shot.get("fx",[])
        lyric=self.lyrics[shot["lyric"]] if shot["lyric"] is not None else None
        # behind text (text passes behind the singer)
        if lyric and shot["text"] in ("behind","behind_bottom") and kind=="illust":
            frame=Image.alpha_composite(frame.convert("RGBA"), self.behind_text(lyric,t,shot)).convert("RGB")
        d=ImageDraw.Draw(frame,"RGBA")
        # glow behind char
        if "glow" in fx or "glow_low" in fx:
            amp=0.5+0.5*pulse; gs=int(H*0.9*(1+0.03*pulse))
            gl=self.glow.resize((gs,gs))
            a=gl.point(lambda v:int(v*(0.36 if "glow" in fx else 0.18)*amp))
            frame.paste(Image.new("RGB",(gs,gs),(255,176,66)),(int(W/2-gs/2),int(H*0.52-gs/2)),a)
            d=ImageDraw.Draw(frame,"RGBA")
        # companions silhouettes
        if shot.get("companions") and shot.get("char"):
            base=self.char(shot["char"], int(self.lerp(*shot["h"],self.ease(p))*H))
            sil=Image.new("RGBA",base.size,(8,10,26,255)); sil.putalpha(base.split()[3].point(lambda v:int(v*0.82)))
            for dx,hh,flip in [(-0.20,0.90,False),(0.21,0.86,True),(-0.34,0.78,True)]:
                s2=sil.resize((int(base.width*hh),int(base.height*hh)),Image.LANCZOS)
                if flip: s2=s2.transpose(Image.FLIP_LEFT_RIGHT)
                frame.paste(s2,(int((shot["x"][0]+dx)*W-s2.width/2),int(H*0.985-s2.height)),s2)
            d=ImageDraw.Draw(frame,"RGBA")
        # character
        if shot.get("char"):
            hfrac=self.lerp(*shot["h"],self.ease(p))*(1+0.008*pulse)
            spr=self.char(shot["char"], hfrac*H)
            cx=self.lerp(*shot["x"],self.ease(p))*W
            bob=math.sin(t*1.35+shot["start"])*H*0.005
            bottom=H*0.99+bob
            if shot.get("dissolve"): spr=spr.copy(); spr.putalpha(spr.split()[3].point(lambda v:int(v*(1-p*0.65))))
            if shot.get("fade_in_char"): spr=spr.copy(); spr.putalpha(spr.split()[3].point(lambda v:int(v*min(1,p*2.5))))
            # soft shadow
            sh=Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
            sd.ellipse([cx-spr.width*0.32,H*0.965,cx+spr.width*0.32,H*0.995],fill=(0,0,8,110))
            frame=Image.alpha_composite(frame.convert("RGBA"),sh).convert("RGB"); d=ImageDraw.Draw(frame,"RGBA")
            frame.paste(spr,(int(cx-spr.width/2),int(bottom-spr.height)),spr); d=ImageDraw.Draw(frame,"RGBA")
        # ---- FX ----
        if "starburst" in fx or "starburst_small" in fx:
            big="starburst" in fx; cx,cy=W*0.5,H*(0.30 if big else 0.34)
            age=t-shot["start"]; inten=max(0,1-age/(2.2 if big else 1.4))
            if inten>0:
                R=(150 if big else 90)*self.scale*(0.6+inten)
                for k in range(12 if big else 8):
                    ang=k*(math.pi/(6 if big else 4))+0.2
                    d.line([cx,cy,cx+math.cos(ang)*R,cy+math.sin(ang)*R],fill=(255,196,84,int(150*inten)),width=2)
                self.star(d,cx,cy,(46 if big else 28)*self.scale*(0.7+0.3*inten),(255,205,100),int(255*inten),3)
                for i in range(26):
                    ang=i*2.399; dist=((age*130*(1+(i%5)*0.14))% (340*self.scale))
                    x=cx+math.cos(ang)*dist; y=cy+math.sin(ang)*dist*0.7+age*22
                    if 0<x<W and 0<y<H: d.ellipse([x-2,y-2,x+2,y+2],fill=(255,205,110,int(190*inten)))
            else: self.star(d,cx,cy,20*self.scale,(255,205,100),200,2)
        if "last_star" in fx:
            tw=0.75+0.25*math.sin(t*2.1)
            self.star(d,W*0.5,H*0.40,26*self.scale*tw,(255,205,100),int(235*tw),2)
        if "shooting" in fx:
            cyc=(t*0.55)%3.7
            if cyc<0.8:
                q=cyc/0.8; x0,y0=W*(0.15+0.55*q),H*(0.10+0.16*q)
                d.line([x0-130*self.scale,y0-34*self.scale,x0,y0],fill=(200,220,255,190),width=2)
                d.ellipse([x0-3,y0-3,x0+3,y0+3],fill=(255,255,255,220))
        if fx and any(f.startswith("motes") for f in fx):
            n=46 if "motes" in fx else 22
            for (x0,y0,sz,sp,ph) in self.motes[:n]:
                x=((x0+math.sin(t*0.11+ph)*0.012)%1.0)*W; y=((y0 - t*sp)%1.0)*H
                a=int(70+80*(0.5+0.5*math.sin(t*1.7+ph)))
                d.ellipse([x-sz*0.16,y-sz*0.16,x+sz*0.16,y+sz*0.16],fill=(255,196,92,a))
        if "star_rain" in fx or "star_rain_low" in fx:
            n=30 if "star_rain" in fx else 14
            for i in range(n):
                x=((i*0.173 - t*0.03*(1+(i%4)*0.2))%1.0)*W; y=((i*0.291 + t*(0.10+(i%5)*0.02))%1.0)*H
                d.line([x,y,x+16*self.scale,y+5*self.scale],fill=(214,226,255,170),width=2)
        if "heart_crack" in fx:
            cx,cy=W*0.5,H*0.46; age=t-shot["start"]; q=min(1,age/1.1)
            pts=[(cx,cy-54*self.scale),(cx-16*self.scale,cy-10*self.scale),(cx+8*self.scale,cy+22*self.scale),(cx-10*self.scale,cy+52*self.scale),(cx+4*self.scale,cy+86*self.scale)]
            for i in range(len(pts)-1):
                if q> i/(len(pts)-1): d.line([pts[i],pts[i+1]],fill=(255,90,90,220),width=3)
            if age>1.6:  # gold kintsugi stitch
                for i in range(len(pts)-1):
                    xm=(pts[i][0]+pts[i+1][0])/2; ym=(pts[i][1]+pts[i+1][1])/2
                    d.line([xm-12,ym,xm+12,ym],fill=(255,196,84,230),width=3)
        if "stitch" in fx:
            cx,cy=W*0.5,H*0.52
            for i in range(5):
                x=cx+(i-2)*26*self.scale; d.line([x-10,cy,x+10,cy],fill=(255,196,84,220),width=3)
                d.line([x,cy-10,x,cy+10],fill=(255,196,84,150),width=2)
        frame=frame.convert("RGB"); d=ImageDraw.Draw(frame,"RGBA")
        # ---- special kinds ----
        if kind=="title":
            fade=min(1,t/1.1); d2=ImageDraw.Draw(frame,"RGBA")
            f=_font("NotoSansJP.ttf",int(96*self.scale),700); title=TITLE
            tw=sum(d2.textlength(c,font=f) for c in title)+int(22*self.scale)*(len(title)-1)
            x=(W-tw)/2
            for c in title:
                d2.text((x,H*0.34),c,font=f,fill=(248,244,230,int(255*fade))); x+=d2.textlength(c,font=f)+22*self.scale
            self.star(d2,W*0.5,H*0.30,(20+8*math.sin(t*2))*self.scale,(255,205,100),int(230*fade),2)
            f2=_font("NotoSerifJP.ttf",int(27*self.scale),500)
            s=f"{ARTIST}「{TITLE}」"; d2.text(((W-d2.textlength(s,font=f2))/2,H*0.52),s,font=f2,fill=(240,220,170,int(230*fade)))
            f3=_font("NotoSansJP.ttf",int(19*self.scale),400)
            s2="非公式ファンMV — UNOFFICIAL FAN-MADE MV"; d2.text(((W-d2.textlength(s2,font=f3))/2,H*0.60),s2,font=f3,fill=(220,224,238,int(190*fade)))
            if lyric: frame=Image.alpha_composite(frame.convert("RGBA"),self.text_layer(lyric,"small",t,shot)).convert("RGB")
            return self.post(frame,t,shot)
        if kind=="typo_black":
            if lyric:
                if shot["text"]=="echo":
                    f=_font("NotoSerifJP.ttf",int(54*self.scale),700)
                    for k in range(3):
                        a=[64,120,255][k]; tw=d.textlength(lyric["jp"],font=f)
                        col=(200,198,190,a) if k<2 else (255,255,255,255)
                        d.text(((W-tw)/2,H*(0.30+k*0.13)),lyric["jp"],font=f,fill=col)
                else:
                    lay=self.text_layer(lyric,"slam",t,shot); frame=Image.alpha_composite(frame.convert("RGBA"),lay).convert("RGB"); d=ImageDraw.Draw(frame,"RGBA")
                    d.line([W*0.30,H*0.60,W*0.70,H*0.60],fill=(200,50,50,255),width=4)
            return self.post(frame,t,shot)
        if kind=="endcard":
            a=min(1,(t-shot["start"])/0.8)
            self.star(d,W*0.5,H*0.30,24*self.scale,(150,220,255),int(220*a),2)
            f=_font("NotoSansJP.ttf",int(64*self.scale),700); s=TITLE
            d.text(((W-d.textlength(s,font=f))/2,H*0.38),s,font=f,fill=(240,238,230,int(255*a)))
            f2=_font("NotoSerifJP.ttf",int(24*self.scale),500)
            lines=[CREDIT,"Movie：非公式ファンMV（本プロジェクト）","原曲：八木海莉「TINY LUCK」／ 映画『GROTESQQQUE-グロテスク-』劇中歌"]
            for i,s2 in enumerate(lines):
                d.text(((W-d.textlength(s2,font=f2))/2,H*(0.52+i*0.075)),s2,font=f2,fill=(226,222,210,int(235*a)))
            return self.post(frame,t,shot)
        # front lyrics
        if lyric and shot["text"] not in ("none","behind"):
            mode=shot["text"] if shot["text"] in ("bottom","center","slam","small") else "bottom"
            frame=Image.alpha_composite(frame.convert("RGBA"),self.text_layer(lyric,mode,t,shot)).convert("RGB")
            d=ImageDraw.Draw(frame,"RGBA")
        elif lyric and shot["text"]=="small":
            frame=Image.alpha_composite(frame.convert("RGBA"),self.text_layer(lyric,"small",t,shot)).convert("RGB"); d=ImageDraw.Draw(frame,"RGBA")
        # interlude / outro captions
        if shot.get("note")=="interlude" and shot["start"]<92:
            f=_font("NotoSerifJP.ttf",int(22*self.scale),500); s="［ 間奏 ］"
            d.text((W*0.06,H*0.10),s,font=f,fill=(240,230,200,170))
        if shot.get("note")=="outro_credits":
            f=_font("NotoSerifJP.ttf",int(21*self.scale),400)
            for i,s in enumerate([CREDIT,"Movie：非公式ファンMV"]):
                d.text((W*0.055,H*(0.76+i*0.05)),s,font=f,fill=(238,234,222,190))
        # HUD
        if kind=="illust":
            f=_font("NotoSansJP.ttf",int(19*self.scale),500)
            d.text((W*0.035,H*0.045),TITLE,font=f,fill=(245,242,232,150))
            f2=_font("NotoSansJP.ttf",int(16*self.scale),400)
            sec=lyric["section"] if lyric else ""
            if sec: d.text((W*0.965-d.textlength(sec,font=f2),H*0.05),sec,font=f2,fill=(245,242,232,120))
            if self.vertical:
                fv=_font("NotoSansJP.ttf",int(20*self.scale),500); s=f"{TITLE} — {ARTIST}"
                d.text(((W-d.textlength(s,font=fv))/2,H*0.028),s,font=fv,fill=(245,242,232,190))
        return self.post(frame,t,shot)

    def post(self, frame, t, shot):
        arr=np.asarray(frame).astype(np.float32)
        if "ca" in shot.get("fx",[]):
            arr[:,:,0]=np.roll(arr[:,:,0],2,axis=1); arr[:,:,2]=np.roll(arr[:,:,2],-2,axis=1)
        if "shake" in shot.get("fx",[]):
            amp=int(3*self.beat_pulse(t)+1)
            arr=np.roll(arr,int(math.sin(t*39)*amp),axis=1)
        arr*=self.vig[...,None]
        # seeded grain (changes at 12fps, deterministic)
        rng=np.random.default_rng(int(t*12)+777)
        noise=rng.normal(0,5.5,(self.H//6,self.W//6)).astype(np.float32)
        noise=np.asarray(Image.fromarray(((noise+40)*3).clip(0,255).astype(np.uint8)).resize((self.W,self.H))).astype(np.float32)/3-40
        arr+=noise[...,None]*0.55
        out=Image.fromarray(arr.clip(0,255).astype(np.uint8))
        if "starburst" in shot.get("fx",[]) and t-shot["start"]<0.28:
            out=Image.blend(out,Image.new("RGB",out.size,(255,226,170)),0.16*(1-(t-shot["start"])/0.28))
        return out
