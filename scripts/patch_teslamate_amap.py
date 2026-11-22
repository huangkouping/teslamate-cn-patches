#!/usr/bin/env python3
"""Create the Amap-enabled TeslaMate 4.5.0 frontend asset.

This tool only accepts the exact upstream 4.5.0 asset hash.  It writes a new
file and never changes the source asset in place.
"""
import argparse
import hashlib
from pathlib import Path

UPSTREAM_SHA256 = "435929fe4c1f37c3b406f423fd3428addb1337ff44ca66d9e8fe398defad521e"
AMAP_LAYER = ('(a=>{a.url="https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",'
              'a.options=Object.assign({},a.options,{maxZoom:18,attribution:"&copy; <a href=\\"https://ditu.amap.com/\\" target=\\"_blank\\" rel=\\"noopener\\">高德地图</a>"});return a})')
GCJ = ('function tmAmapGcjCoord(a,n){if(n<72.004||n>137.8347||a<.8293||a>55.8271)return[a,n];let l=300+(n-105)+2*(a-35)+.1*(n-105)*(n-105)+.1*(n-105)*(a-35)+.1*Math.sqrt(Math.abs(n-105))+(20*Math.sin(6*(n-105)*Math.PI)+20*Math.sin(2*(n-105)*Math.PI))*2/3+(20*Math.sin((n-105)*Math.PI)+40*Math.sin((n-105)/3*Math.PI))*2/3+(150*Math.sin((n-105)/12*Math.PI)+300*Math.sin((n-105)/30*Math.PI))*2/3,u=-100+2*(n-105)+3*(a-35)+.2*(a-35)*(a-35)+.1*(n-105)*(a-35)+.2*Math.sqrt(Math.abs(n-105))+(20*Math.sin(6*(n-105)*Math.PI)+20*Math.sin(2*(n-105)*Math.PI))*2/3+(20*Math.sin((a-35)*Math.PI)+40*Math.sin((a-35)/3*Math.PI))*2/3+(160*Math.sin((a-35)/12*Math.PI)+320*Math.sin((a-35)*Math.PI/30))*2/3,b=a/180*Math.PI,p=1-.00669342162296594323*Math.sin(b)**2,v=Math.sqrt(p);return[a+u*180/((6335552.717000426*(1-.00669342162296594323))/(p*v)*Math.PI),n+l*180/(6378245/v*Math.cos(b)*Math.PI)]}')

def once(text, before, after, label):
    if text.count(before) != 1:
        raise SystemExit(f"Unexpected {label} anchor; stop without writing output.")
    return text.replace(before, after, 1)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path, help="original TeslaMate 4.5.0 app-*.js")
parser.add_argument("output", type=Path, help="new Amap-enabled asset")
args = parser.parse_args()
raw = args.source.read_bytes()
if hashlib.sha256(raw).hexdigest() != UPSTREAM_SHA256:
    raise SystemExit("Unsupported source asset: expected the official TeslaMate 4.5.0 file. Stop without writing output.")
text = raw.decode("utf-8")
text = once(text, "function gc(a){", GCJ + "function gc(a){", "map factory")
text = once(text, "renderer:xf()})),{url:l,options:u}", "renderer:xf()}));n.attributionControl&&n.attributionControl.setPrefix(false);let{url:l,options:u}", "attribution")
text = once(text, "tileLayer:JSON.parse(this.el.dataset.tileLayer),zoomControl", "tileLayer:" + AMAP_LAYER + "(JSON.parse(this.el.dataset.tileLayer)),zoomControl", "vehicle map layer")
text = once(text, "[p,v,x]=a.value.split(\",\"),D=b?", "[p,v,x]=a.value.split(\",\");[p,v]=tmAmapGcjCoord(Number(p),Number(v));let D=b?", "vehicle map coordinate")
text = once(text, "[Ae,Ue,Ye]=a.value.split(\",\");D.setHeading", "[Ae,Ue,Ye]=a.value.split(\",\");[Ae,Ue]=tmAmapGcjCoord(Number(Ae),Number(Ue)),D.setHeading", "live marker coordinate")
text = once(text, "tileLayer:JSON.parse(this.el.dataset.tileLayer),enableHybridLayer", "tileLayer:" + AMAP_LAYER + "(JSON.parse(this.el.dataset.tileLayer)),enableHybridLayer", "geofence map layer")
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(text, encoding="utf-8")
print(f"created={args.output}")
