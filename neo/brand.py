#!/usr/bin/env python3
"""Generate Firefox Neo icons/wordmarks (replaces Mozilla Firefox logo art). Usage: brand.py <fenix app/src/release/res>"""
import sys, pathlib, glob
from PIL import Image, ImageDraw, ImageFont
res = pathlib.Path(sys.argv[1])
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
try: ImageFont.truetype(FONT, 10)
except Exception:
    FONT = glob.glob("/usr/share/fonts/**/*Bold*.ttf", recursive=True)[0]
INK=(12,14,28,255); V=(124,92,255,255); C=(41,224,255,255)

def logo(size, bg=True, round_=False):
    S=size*4
    im=Image.new("RGBA",(S,S),(0,0,0,0)); d=ImageDraw.Draw(im)
    if bg:
        if round_: d.ellipse((0,0,S-1,S-1),fill=INK)
        else: d.rounded_rectangle((0,0,S-1,S-1),radius=S//4.5,fill=INK)
    c=S/2; r=S*0.34; w=max(2,int(S*0.07))
    d.ellipse((c-r,c-r,c+r,c+r),outline=V,width=w)
    f=ImageFont.truetype(FONT,int(S*0.40)); 
    d.text((c,c),"N",font=f,fill=C,anchor="mm")
    return im.resize((size,size),Image.LANCZOS)

def wordmark(w,h,text="Firefox Neo",bg=None):
    S=4
    im=Image.new("RGBA",(w*S,h*S),bg or (0,0,0,0)); d=ImageDraw.Draw(im)
    fs=int(h*S*0.55)
    f=ImageFont.truetype(FONT,fs)
    while d.textlength(text,font=f)>w*S*0.92: fs-=4; f=ImageFont.truetype(FONT,fs)
    d.text((w*S/2,h*S/2),text,font=f,fill=(235,238,255,255),anchor="mm")
    # accent underline
    tw=d.textlength(text,font=f); y=h*S/2+fs*0.62
    d.rounded_rectangle((w*S/2-tw/2,y,w*S/2+tw/2,y+max(4,h*S*0.03)),radius=4,fill=V)
    return im.resize((w,h),Image.LANCZOS)

for f in glob.glob(str(res/"mipmap-*/ic_launcher.webp")):
    s=Image.open(f).size[0]; logo(s).save(f,"WEBP",lossless=True)
for f in glob.glob(str(res/"mipmap-*/ic_launcher_round.webp")):
    s=Image.open(f).size[0]; logo(s,round_=True).save(f,"WEBP",lossless=True)
for f in glob.glob(str(res/"drawable*/ic_logo_wordmark_*.webp"))+glob.glob(str(res/"drawable*/ic_wordmark_text_*.webp")):
    w,h=Image.open(f).size; t="Firefox Neo"+(" Private" if "private" in f else "")
    wordmark(w,h,t).save(f,"WEBP",lossless=True)
for f in glob.glob(str(res/"drawable-nodpi/ic_wordmark_logo.webp")):
    w,h=Image.open(f).size; im=Image.new("RGBA",(w,h),(0,0,0,0)); l=logo(min(w,h)); im.paste(l,((w-l.size[0])//2,(h-l.size[1])//2),l); im.save(f,"WEBP",lossless=True)
for f in glob.glob(str(res/"drawable-*/fenix_search_widget.webp")):
    w,h=Image.open(f).size; im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,w-1,h-1),radius=h//2,fill=(20,22,40,235),outline=V,width=2)
    im.save(f,"WEBP",lossless=True)
# adaptive-icon vectors (foreground + monochrome): ring + N
def vec(color_ring,color_n):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
  <path android:pathData="M54,54m-27,0a27,27 0,1 1,54 0a27,27 0,1 1,-54 0" android:strokeColor="{color_ring}" android:strokeWidth="5" android:fillColor="#00000000"/>
  <path android:pathData="M43,68L43,40L65,68L65,40" android:strokeColor="{color_n}" android:strokeWidth="6" android:strokeLineCap="round" android:strokeLineJoin="round" android:fillColor="#00000000"/>
</vector>
'''
(res/"drawable").mkdir(exist_ok=True)
(res/"drawable/ic_launcher_foreground.xml").write_text(vec("#7C5CFF","#29E0FF"))
mono = res.parent.parent/"main/res/drawable/ic_launcher_monochrome.xml"
if mono.exists(): mono.write_text(vec("#FF000000","#FF000000"))
print("branding done")
