#!/usr/bin/env python3
"""Render the website OG social cards + README badges from the canonical marks.

Brand: Sora (SIL OFL, vendored at ../fonts/Sora.ttf) for the wordmark, the new
tile marks (dark rounded square + thin green ring), green (#6ddb73) as the one
accent with blue kept subtle.
"""
import io, os
import cairosvg
from PIL import Image, ImageDraw, ImageFont
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS=os.path.join(ROOT,"branding/sysible-mark.svg")
CTL=os.path.join(ROOT,"branding/sysible-controller-mark.svg")
FONT=os.path.join(ROOT,"fonts/Sora.ttf")          # vendored Sora (variable)
GREEN=(109,219,115); BLUE=(122,162,255)
def sora(sz,weight="SemiBold"):
    f=ImageFont.truetype(FONT,sz)
    for nm in (weight,"SemiBold","Regular"):
        try: f.set_variation_by_name(nm); break
        except Exception: continue
    return f
def mark(url,s):
    return Image.open(io.BytesIO(cairosvg.svg2png(url=url,output_width=s,output_height=s))).convert("RGBA")
def fit(text,maxw,cap,tr_ratio,weight="SemiBold"):
    d=ImageDraw.Draw(Image.new("RGBA",(4,4)));sz=cap
    while sz>10:
        f=sora(sz,weight);tr=sz*tr_ratio
        w=sum(d.textlength(c,font=f) for c in text)+tr*(len(text)-1)
        if w<=maxw:return f,tr
        sz-=2
    return sora(10,weight),0
def tracked(d,text,f,cx,y,fill,tr):
    ws=[d.textlength(c,font=f) for c in text];tot=sum(ws)+tr*(len(text)-1);x=cx-tot/2
    for c,w in zip(text,ws):d.text((x,y),c,font=f,fill=fill);x+=w+tr
    return tot
def card(out,markurl,title,sub):
    W,H=1280,640
    im=Image.new("RGBA",(W,H),(13,16,23,255))
    d=ImageDraw.Draw(im)
    # subtle vertical lift (top slightly lighter)
    for yi in range(H):
        t=yi/H;c=(int(18-6*t),int(22-7*t),int(32-10*t));d.line([(0,yi),(W,yi)],fill=c)
    # top accent bar: green primary, a short subtle blue tail on the far right
    for xi in range(W):
        t=xi/W; k=max(0.0,(t-0.72)/0.28)   # blue only enters in the last ~28%
        c=(int(GREEN[0]+(BLUE[0]-GREEN[0])*k),int(GREEN[1]+(BLUE[1]-GREEN[1])*k),int(GREEN[2]+(BLUE[2]-GREEN[2])*k))
        d.line([(xi,0),(xi,7)],fill=c)
    ms=232;im.alpha_composite(mark(markurl,ms),((W-ms)//2,88))
    d=ImageDraw.Draw(im)
    ty=384
    f1,t1=fit(title,W*0.8,96,0.005);tot=tracked(d,title,f1,W/2,ty,(236,239,243),t1)
    asc,desc=f1.getmetrics();base=ty+asc+desc
    # thin green underline accent beneath the wordmark (clears the descenders)
    uw=min(tot*0.5,240); d.rounded_rectangle([W/2-uw/2,base+14,W/2+uw/2,base+19],radius=2,fill=GREEN)
    f2,t2=fit(sub,W*0.72,34,0.30,"Medium");tracked(d,sub,f2,W/2,base+44,(138,147,160),t2)
    im.convert("RGB").save(os.path.join(ROOT,out));print("wrote",out)
def badge(out,fg):
    W,H=980,260;im=Image.new("RGBA",(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    s=int(H*0.86);im.alpha_composite(mark(SYS,s),(int(W*0.05),(H-s)//2))
    f,tr=fit("SYSIBLE",W*0.5,int(H*0.30),0.02)
    x0=int(W*0.05)+s+int(H*0.12);d2=ImageDraw.Draw(im);asc,desc=f.getmetrics()
    tracked(d2,"SYSIBLE",f,x0+ (sum(d2.textlength(c,font=f) for c in "SYSIBLE")+tr*6)/2,(H-(asc+desc))//2,fg,tr)
    im.save(os.path.join(ROOT,out));print("wrote",out)
card("social-card.png",SYS,"Sysible","ENTERPRISE SOFTWARE")
card("controller-card.png",CTL,"Sysible Controller","IT INFRASTRUCTURE MANAGEMENT")
badge(".github/sysible-logo-dark.png",(233,240,247))
badge(".github/sysible-logo-light.png",(20,33,58))
