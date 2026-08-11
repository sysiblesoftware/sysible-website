#!/usr/bin/env python3
"""Render the website OG social cards + README badges from the canonical marks."""
import io, os
import cairosvg
from PIL import Image, ImageDraw, ImageFont
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS=os.path.join(ROOT,"branding/sysible-mark.svg")
CTL=os.path.join(ROOT,"branding/sysible-controller-mark.svg")
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def mark(url,s):
    return Image.open(io.BytesIO(cairosvg.svg2png(url=url,output_width=s,output_height=s))).convert("RGBA")
def fit(text,maxw,cap,tr_ratio):
    d=ImageDraw.Draw(Image.new("RGBA",(4,4)));sz=cap
    while sz>10:
        f=ImageFont.truetype(FONT,sz);tr=sz*tr_ratio
        w=sum(d.textlength(c,font=f) for c in text)+tr*(len(text)-1)
        if w<=maxw:return f,tr
        sz-=2
    return ImageFont.truetype(FONT,10),0
def tracked(d,text,f,cx,y,fill,tr):
    ws=[d.textlength(c,font=f) for c in text];tot=sum(ws)+tr*(len(text)-1);x=cx-tot/2
    for c,w in zip(text,ws):d.text((x,y),c,font=f,fill=fill);x+=w+tr
def card(out,markurl,title,sub):
    W,H=1280,640
    im=Image.new("RGBA",(W,H),(13,16,23,255))
    d=ImageDraw.Draw(im)
    # subtle vertical lift (top slightly lighter), then the accent bar
    for yi in range(H):
        t=yi/H;c=(int(18-6*t),int(22-7*t),int(32-10*t));d.line([(0,yi),(W,yi)],fill=c)
    # top accent bar green->blue
    for xi in range(W):
        t=xi/W;c=(int(99+(85-99)*t),int(219+(128-219)*t),int(115+(238-115)*t));d.line([(xi,0),(xi,7)],fill=c)
    ms=232;im.alpha_composite(mark(markurl,ms),((W-ms)//2,96))
    d=ImageDraw.Draw(im)
    f1,t1=fit(title,W*0.8,96,0.005);tracked(d,title,f1,W/2,398,(238,242,250),t1)
    f2,t2=fit(sub,W*0.72,36,0.30);tracked(d,sub,f2,W/2,516,(120,140,175),t2)
    im.convert("RGB").save(os.path.join(ROOT,out));print("wrote",out)
def badge(out,fg):
    W,H=980,260;im=Image.new("RGBA",(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    s=int(H*0.80);im.alpha_composite(mark(SYS,s),(int(W*0.06),(H-s)//2))
    f,tr=fit("SYSIBLE",W*0.5,int(H*0.34),0.04)
    x0=int(W*0.06)+s+int(H*0.12);d2=ImageDraw.Draw(im);asc,desc=f.getmetrics()
    tracked(d2,"SYSIBLE",f,x0+ (sum(d2.textlength(c,font=f) for c in "SYSIBLE")+tr*6)/2,(H-(asc+desc))//2,fg,tr)
    im.save(os.path.join(ROOT,out));print("wrote",out)
card("social-card.png",SYS,"Sysible","ENTERPRISE SOFTWARE")
card("controller-card.png",CTL,"Sysible Controller","IT INFRASTRUCTURE MANAGEMENT")
badge(".github/sysible-logo-dark.png",(233,240,247))
badge(".github/sysible-logo-light.png",(20,33,58))
