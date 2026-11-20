#!/usr/bin/env python3
"""Render the Point Roberts map documentary. See production/README.md."""
import argparse
import json
from importlib.metadata import distribution
import subprocess
import wave
import zipfile
from functools import lru_cache
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
import shapefile
from PIL import Image, ImageDraw, ImageFont
from scipy import signal
from shapely.geometry import LineString, Point, Polygon, box, shape
from shapely.ops import clip_by_rect, linemerge, unary_union

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parents[1] / '.cache'
DATA = CACHE / 'pr_data'
VOICE = ROOT / 'production' / 'voice'
W, H, FPS, LEN = 720, 1280, 30, 55
MAP_W, MAP_H, KM = 3700, 5350, 75
WEST, NORTH, KX, KY = -123.26, 49.275, 73.16, 111.19
ANCHOR = (350, 527)
BORDER = 49.002075
PORT = (-123.06794, BORDER)
POINT = (-123.061, 48.986)
SCHOOL = (-122.738176, 48.992658)
GOLD = '#ffcd73'
WHITE = '#f7f3e8'
MUTED = '#afd5d2'
DARK = '#102930'
RED = '#ae483e'
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
cv2.setNumThreads(1)

# Editorial cue anchors referenced to dialogue clips, not travel time.
CLIPS = [('01', .06), ('02b', 6.03), ('03', 12.26), ('04', 19.99), ('05', 31.09), ('06', 42.23)]
CROSSINGS = [7.57, 34.02, 46.78, 48.64]
SLIP = (40.23, 42.21)
CAPS = [
    (0.00,1.20,'This school bus'), (1.20,2.38,'leaves the country'), (2.38,3.82,'just to take kids\nto high school.'),
    (4.06,6.00,'And the school is\nin the same state.'), (6.03,6.94,'First stop:'), (7.16,8.08,'Canada.'),
    (8.18,9.82,'That’s the only road\nout of'),(9.82,11.72,'Point Roberts,\nWashington.'),
    (12.26,14.55,'That’s Blaine, right\nacross Boundary Bay.'),(15.23,16.23,'It’s right there.'),
    (16.49,17.52,'Unfortunately,'),(17.58,19.32,'the bus is not a boat.'),
    (19.99,22.12,'Why is this tip\neven American?'),(22.30,24.17,'In 1846,'),
    (24.22,25.80,'the Oregon Treaty\nextended the border'),(25.80,28.08,'along the\n49th parallel.'),
    (28.24,30.85,'That left the tip\non the U.S. side.'),
    (31.09,32.94,'So the bus goes through\nBritish Columbia,'),(33.02,35.60,'crosses back into\nthe U.S. at Blaine,'),
    (35.60,36.90,'and pulls up\nto high school.'),(36.98,38.94,'That’s about forty\nminutes on the bus.'),
    (39.36,40.12,'One way.'), (42.23,43.71,'Then the last bell rings,'),(43.71,45.46,'and they do it all again.'),
    (46.33,47.40,'Into Canada.'),(47.78,49.14,'Back into Washington.'),(49.28,50.56,'Four border crossings,'),
    (50.56,51.77,'just to go to school'),(51.77,53.19,'in their own district.'),
]


def grid(coords):
    a = np.asarray(coords, dtype=np.float64)
    return np.column_stack(((a[:, 0]-WEST)*KX*KM, (NORTH-a[:, 1])*KY*KM))


def xy(lon, lat):
    return (lon-WEST)*KX*KM, (NORTH-lat)*KY*KM


def polys(g):
    if g.geom_type == 'Polygon':
        if not g.is_empty:
            yield g
    elif hasattr(g, 'geoms'):
        for k in g.geoms:
            yield from polys(k)


def read_assets():
    with zipfile.ZipFile(DATA/'pr.zip') as z:
        base = next(name.split('/')[0] for name in z.namelist() if name.endswith('/assets/osm/features.json')) + '/assets/'
        local = json.loads(z.read(base+'osm/features.json'))
        dems = []
        for suffix in ['', '_far']:
            meta = json.loads(z.read(base+f'terrain/meta{suffix}.json'))['grid']
            v = np.frombuffer(z.read(base+f'terrain/heightmap{suffix}.bin'), dtype='<i2')
            dems.append((meta, v.reshape(meta['nrows'], meta['ncols']).astype(np.float32)*meta['scale_m']))
    reader = shapefile.Reader(shp=str(DATA/'ne.shp'))
    extent = box(WEST-.01, NORTH-MAP_H/(KY*KM)-.01, WEST+MAP_W/(KX*KM)+.01, NORTH+.01)
    us, ca = [shape(reader.shape(i).__geo_interface__).buffer(0).intersection(extent) for i in (154,155)]
    data_dir = distribution('basemap-data-hires').locate_file('mpl_toolkits/basemap_data')
    points = np.memmap(data_dir/'gshhs_f.dat', dtype='<f4', mode='r')
    south, north = extent.bounds[1], extent.bounds[3]
    west, east = extent.bounds[0], extent.bounds[2]
    shore = []
    for row in (data_dir/'gshhsmeta_f.dat').read_text().splitlines():
        level, _, _, a, b, offset, length, _ = row.split()
        if level != '1' or float(a)>north or float(b)<south:
            continue
        sl = int(offset)//4
        pts = points[sl:sl+int(length)//4].reshape(-1,2)
        if pts[:,0].min() > east or pts[:,0].max() < west:
            continue
        clipped = clip_by_rect(Polygon(pts), *extent.bounds).buffer(0)
        if not clipped.is_empty:
            shore.append(clipped)
    land = unary_union(shore)
    # Replace coarse Natural Earth shoreline on the peninsula with OSM ways.
    coast = linemerge([LineString([(lon,lat) for lat,lon in row['coords']]) for row in local['coastline']])
    coast = max(coast.geoms, key=lambda g:g.length) if hasattr(coast, 'geoms') else coast
    c = list(coast.coords)
    local_land = Polygon(c + [(c[-1][0],49.035),(c[0][0],49.035)]).buffer(0)
    patch = box(-123.109,48.966,-123.018,49.0121)
    land = land.difference(patch).union(local_land.intersection(patch))
    # Natural Earth admin geometry in this area is generalized; recolor the
    # land segment at the mapped parallel near Point Roberts and mainland Blaine.
    # No straight maritime boundary is asserted or drawn.
    southern = box(extent.bounds[0],extent.bounds[1],extent.bounds[2],BORDER)
    us_parts = []
    for p in polys(land):
        if p.covers(Point(*SCHOOL)):
            us_parts.append(p.intersection(southern))
        else:
            us_hit, ca_hit = p.intersection(us).area, p.intersection(ca).area
            if us_hit > ca_hit or (us_hit == ca_hit == 0 and p.distance(us)<p.distance(ca)):
                us_parts.append(p)
    us = unary_union(us_parts)
    return land, us, local, dems


def paint_mask(g):
    m = np.zeros((MAP_H,MAP_W), dtype=np.uint8)
    for p in polys(g):
        cv2.fillPoly(m, [np.round(grid(p.exterior.coords)).astype(np.int32)], 255)
        for r in p.interiors:
            cv2.fillPoly(m, [np.round(grid(r.coords)).astype(np.int32)], 0)
    return m


def transform_dem(meta, vals):
    west_x, north_y = xy(meta['west_lon'],meta['north_lat'])
    step_x = meta['cellsize_deg']*KX*KM
    step_y = meta['cellsize_deg']*KY*KM
    v = vals.copy()
    mask = (v>-1200).astype(np.float32)
    v[mask==0] = 0
    a = np.float32([[step_x,0,west_x],[0,step_y,north_y]])
    height = cv2.warpAffine(v, a, (MAP_W,MAP_H), flags=cv2.INTER_LINEAR)
    weight = cv2.warpAffine(mask, a, (MAP_W,MAP_H), flags=cv2.INTER_LINEAR)
    height /= np.maximum(weight, .01)
    return height, weight


def render_map():
    cache = DATA/'map-v11.png'
    land, us, local, dems = read_assets()
    road = [[(x,y) for y,x in r['coords']] for r in local['roads'] if r['kind'] in ('residential','secondary','tertiary','primary','unclassified')]
    route = [(x,y) for i in [241,826,13,478,479,471] for y,x in (local['roads'][i]['coords'][::-1] if i in (241,826) else local['roads'][i]['coords'])]
    coast_parts = land.intersection(LineString([(-123.2,BORDER),(-122.60,BORDER)]))
    if cache.exists():
        return cv2.imread(str(cache)), road, route, coast_parts
    print('Building relief map…', flush=True)
    m, u = paint_mask(land), paint_mask(us)
    combined = np.zeros(m.shape,np.float32)
    valid = np.zeros(m.shape,np.float32)
    for (meta, arr),width in zip(dems[::-1],(110,18)):
        v,w = transform_dem(meta, arr)
        # Feather the DEM edges to avoid raster tile seams.
        blend = np.minimum(1,cv2.distanceTransform((w>.6).astype(np.uint8),cv2.DIST_L2,5)/width)
        blend = blend*blend*(3-2*blend)
        combined = combined*(1-blend) + v*blend
        valid = np.maximum(valid,blend)
        del v,w,blend
    rng = np.random.default_rng(1208)
    fine = rng.normal(0,1.25,m.shape).astype(np.float32)
    little = cv2.resize(rng.normal(0,1,(186,145)).astype(np.float32),(MAP_W,MAP_H),interpolation=cv2.INTER_CUBIC)
    broad = cv2.resize(rng.normal(0,1,(23,17)).astype(np.float32),(MAP_W,MAP_H),interpolation=cv2.INTER_CUBIC)
    distw = cv2.distanceTransform(255-m,cv2.DIST_L2,5)
    distl = cv2.distanceTransform(m,cv2.DIST_L2,5)
    bath = (1-np.exp(np.minimum(combined,0)/7))*np.exp(np.minimum(combined,0)/41)*np.minimum(1,valid)*np.exp(-distw/145)
    ocean_rim = np.exp(-distw/32)
    ocean_tint = bath*8 + ocean_rim*18 + broad*2 + little*.55 + fine*.4
    # Coastal drop shadow sits to the south-east in map space.
    soft = cv2.GaussianBlur(m,(0,0),12).astype(np.float32)/255
    contact = np.roll(np.roll(soft,11,0),7,1)*21
    grad_x = cv2.Sobel(combined,cv2.CV_32F,1,0,ksize=3)/8
    grad_y = cv2.Sobel(combined,cv2.CV_32F,0,1,ksize=3)/8
    relief = np.tanh((grad_x+grad_y)*.55)*18*np.minimum(valid*1.5,1)
    elev = np.minimum(np.maximum(combined,0)/80,1.4)
    grain = fine+little*2.5+broad*3 + relief + elev*9 + np.exp(-distl/5)*15
    buf = np.empty((MAP_H,MAP_W,3),np.uint8)
    # BGR ocean, CA and WA palettes; coherent color management in RGB export.
    for i,(wa,ca,oc,k) in enumerate(zip((113,159,180),(103,136,109),(55,46,19),(1.22,1.28,1.0))):
        land_chan = np.where(u>0, wa,ca) + grain
        water_chan = oc + k*ocean_tint - contact
        buf[:,:,i] = np.where(m>0,land_chan.clip(0,255),water_chan.clip(0,255)).astype(np.uint8)
    for line in road:
        cv2.polylines(buf,[np.round(grid(line)).astype(np.int32)],False,(114,148,141),1,cv2.LINE_AA)
    cv2.imwrite(str(cache),buf, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return buf, road, route, coast_parts


def smooth(x):
    x = min(1.,max(0.,x))
    return x*x*(3-2*x)


def ramp(t,a,b):
    return smooth((t-a)/(b-a))


def window(t,a,b,edge=.22):
    return min(ramp(t,a,a+edge),1-ramp(t,b-edge,b))


def ease_keys(t, keys, loglast=False):
    if t <= keys[0][0]: return keys[0][1:]
    for a,b in zip(keys,keys[1:]):
        if t <= b[0]:
            q = ramp(t,a[0],b[0])
            values = [v+(z-v)*q for v,z in zip(a[1:],b[1:])]
            if loglast:
                values[-1] = a[-1]*(b[-1]/a[-1])**q
            return values
    return keys[-1][1:]


CAM = [(0,-123.067,48.993,8.2),(3.95,-123.067,48.994,8.55), (7.5,-123.066,49.000,8.7),
       (10.50,-123.064,49.000,10.4),(14.55,-122.905,48.980,32.8),(19.4,-122.901,48.981,34.0),
       (23.0,-123.041,48.990,14.1),(27.3,-123.061,48.992,8.5),(30.64,-123.057,48.994,10.5),
       (33.12,-122.897,48.982,33.0),(36.93,-122.756,48.985,13.0), (41.90,-122.757,48.987,13.5),
       (45.48,-122.897,48.981,33.2),(48.00,-122.900,48.982,33.2),(50.07,-123.055,48.993,12.0),
       (52.62,-123.061,48.994,10.0),(54.64,-123.067,48.993,8.2),(55,-123.067,48.993,8.2)]


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))


@lru_cache(maxsize=100)
def font(size, weight):
    f = ImageFont.truetype(str(DATA/'Manrope.ttf'),size)
    f.set_variation_by_axes([weight])
    return f


@lru_cache(maxsize=350)
def label(s,size=32,weight=750,fill=WHITE,outline=0,bg='',pad=12):
    f = font(size,weight)
    lines = s.split('\n')
    w = int(max(f.getlength(s) for s in lines)) + 2*pad + 8
    h = int((len(lines)-1)*size*1.18 + size*1.18 + 2*pad)
    im = Image.new('RGBA',(w,h)); d = ImageDraw.Draw(im)
    if bg:
        d.rounded_rectangle((1,1,w-2,h-2),radius=min(15,h//3),fill=(*rgb(bg),235),outline=(213,241,224,35),width=1)
    for i,line in enumerate(lines):
        d.text((w/2,pad+size*.58+i*size*1.18),line,font=f,anchor='mm', fill=fill,
               stroke_width=outline,stroke_fill='#07171e')
    return form(im)


def form(im):
    a=np.array(im)
    return np.ascontiguousarray(a[:,:,:3][:,:,::-1]), np.ascontiguousarray(a[:,:,3],dtype=np.float32)/255


def paste(frame, sp, x,y, opacity=1.0):
    if opacity < .006: return
    b,a = sp
    sh,sw = a.shape
    x,y = round(x-sw/2),round(y-sh/2)
    x0,y0 = max(x,0),max(y,0)
    x1,y1 = min(x+sw,W),min(y+sh,H)
    if x1<=x0 or y1<=y0:return
    m=a[y0-y:y1-y,x0-x:x1-x,None]*opacity
    f=frame[y0:y1,x0:x1]
    f[:] = f*(1-m)+b[y0-y:y1-y,x0-x:x1-x]*m


def drawline(f, points, color, width=2):
    cv2.polylines(f, [np.asarray(points).round().astype(np.int32)], False,rgb(color)[::-1],width,cv2.LINE_AA)


def dot(f,x,y,color,sz):
    cv2.circle(f,(int(x),int(y)),sz,rgb(color)[::-1],-1,cv2.LINE_AA)


def border_rows(parts):
    if not hasattr(parts,'geoms'): parts=[parts]
    else: parts=list(parts.geoms)
    return [list(p.coords) for p in parts if p.geom_type=='LineString' and p.length>.002]


@lru_cache(maxsize=30)
def bus_sprite(angle):
    # Directional top-down bus symbol (not to ground scale).
    im=Image.new('RGBA',(94,126)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((24,19,79,117),14,fill=(3,16,20,113))
    for x in (9,66):
        for y in (28,83):d.rounded_rectangle((x,y,x+14,y+16),4,fill='#171c22')
    d.rounded_rectangle((16,12,74,107),14,fill='#d18031',outline='#112129',width=5)
    d.rounded_rectangle((18,10,72,98),12,fill='#ffcb54',outline='#fff0b5',width=2)
    d.rounded_rectangle((23,19,67,34),5,fill='#263f49')
    d.line((26,21,63,21),fill='#6aa4aa',width=2)
    d.rounded_rectangle((25,39,65,83),5,fill='#f8a62d')
    d.rounded_rectangle((27,43,63,79),4,fill='#ffdb74')
    d.line((27,60,63,60),fill='#ffbc51',width=2)
    d.rounded_rectangle((24,88,67,96),3,fill='#795030')
    d.ellipse((23,13,29,19),fill='#fff7d8'); d.ellipse((61,13,67,19),fill='#fff7d8')
    d.ellipse((23,94,29,99),fill='#bc4231'); d.ellipse((61,94,67,99),fill='#bc4231')
    return form(im.rotate(angle,Image.Resampling.BICUBIC,expand=True))


@lru_cache(maxsize=6)
def flag(which, blink):
    im=Image.new('RGBA',(87,62)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((5,8,85,61),11,fill=(7,17,18,100))
    b=Image.new('RGBA',(80,52),'#f7efe3'); q=ImageDraw.Draw(b)
    if which=='US':
        for i in range(0,13,2):q.rectangle((0,i*4,79,i*4+3),fill='#c75850')
        q.rectangle((0,0,34,28),fill='#37516f')
        for y in (4,10,16,22):
            for x in (5,11,17,23,29):q.ellipse((x,y,x+1,y+1),fill=WHITE)
    else:
        q.rectangle((0,0,18,51),fill='#c55048');q.rectangle((61,0,79,51),fill='#c55048')
        q.polygon([(40,5),(43,14),(48,10),(47,18),(54,16),(51,23),(57,24),(46,34),
                   (47,39),(41,37),(41,47),(39,47),(39,37),(33,39),(34,34),(23,24),(29,23),(26,16),(33,18),(32,10),(37,14)],fill='#c55048')
    clip=Image.new('L',b.size); ImageDraw.Draw(clip).rounded_rectangle((0,0,79,51),10,fill=255); im.paste(b,(1,1),clip)
    d.rounded_rectangle((1,1,81,53),10,outline='#fdf6df',width=1)
    for a in (31,52):
        if blink: d.line((a-4,34,a+4,34),fill='#10252b',width=3)
        else:
            d.ellipse((a-5,26,a+5,42), fill=WHITE,outline='#10252b',width=2)
            d.ellipse((a-1,31,a+3,39), fill='#10252b')
    return form(im)


@lru_cache(maxsize=1)
def late_slip():
    im=Image.new('RGBA',(555,331)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((21,24,551,326),21,fill='#082127bb')
    d.rounded_rectangle((13,8,540,313),16,fill='#efe1bc',outline='#fdf7dd',width=3)
    d.rounded_rectangle((27,23,526,298),9,outline='#b89f79',width=1)
    d.line((49,87,505,87),fill='#8b7254',width=2)
    d.text((50,48),'SCHOOL LATE SLIP',font=font(25,850),fill='#294248')
    d.text((50,111),'REASON FOR TARDINESS:',font=font(29,790),fill='#385155')
    d.text((46,146),'CANADA.',font=font(90,850),fill='#a64137')
    d.line((48,257,503,257),fill='#a08863',width=2)
    d.text((49,270),'ILLUSTRATION',font=font(13,800),fill='#735a43')
    return form(im.rotate(-4,Image.Resampling.BICUBIC,expand=True))


@lru_cache(maxsize=16)
def counter(n):
    im=Image.new('RGBA',(300,67)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((1,1,299,65),15,fill=(8,26,35,235),outline=(206,227,207,74),width=1)
    d.text((20,12),'BORDER CROSSINGS',font=font(13,850),fill=MUTED)
    for i in range(4):
        x=20+i*66
        d.rounded_rectangle((x,34,x+58,51),5,fill=GOLD if i<n else '#34525a')
        d.text((x+29,42.5),str(i+1),font=font(13,800),fill='#152a2c' if i<n else '#a2c5c6',anchor='mm')
    return form(im)


@lru_cache(maxsize=8)
def schematic(back,stage):
    im=Image.new('RGBA',(507,116)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,506,115),18,fill=(8,30,39,235),outline='#4b6e72',width=1)
    d.text((20,13),'RIDE HOME' if back else 'RIDE TO SCHOOL',font=font(17,820),fill=MUTED)
    d.text((490,16),'ROUTE SCHEMATIC',anchor='ra',font=font(12,820),fill='#adc0bd')
    for i,txt in enumerate(('U.S.','CANADA','U.S.')):
        x=19+i*164
        d.rounded_rectangle((x,45,x+139,95),12, fill=GOLD if i==stage else '#23474c')
        d.text((x+69.5,70),txt,anchor='mm',font=font(22,850),fill=DARK if i==stage else WHITE)
        if i<2:
            d.line((x+146,70,x+157,70),fill=MUTED,width=2)
            d.line((x+153,66,x+157,70,x+153,74),fill=MUTED,width=2)
    return form(im)


# Scope vignettes around the panel and text, not independent HUD elements.
y_norm,x_norm=np.ogrid[:H,:W]
SHADE=np.clip(1-(.25*((x_norm-W*.49)/(W*.57))**2+.23*((y_norm-H*.43)/(H*.62))**2),.47,1)
TOP=np.clip((322-y_norm)/300,0,.78)*.66
BOT=np.clip((y_norm-797)/485,0,.95)*.91
SCREEN_GAIN=np.ascontiguousarray((SHADE*(1-TOP)*(1-BOT))[:,:,None],dtype=np.float32)


GRADE=np.ascontiguousarray(np.broadcast_to(SCREEN_GAIN,(H,W,3)))

def render_frames():
    base,_,road,parts = render_map()
    borders=border_rows(parts)
    ys=np.array([r[1] for r in road]); xs=np.array([r[0] for r in road]);
    def frame_at(t):
        cx,cy,wide=ease_keys(t,CAM,True)
        sc=W/(wide*KM)
        xg,yg=xy(cx,cy)
        mx=ANCHOR[0]-xg*sc; my=ANCHOR[1]-yg*sc
        f=cv2.warpAffine(base,np.float32([[sc,0,mx],[0,sc,my]]),(W,H),flags=cv2.INTER_LINEAR,borderValue=(53,41,17))
        # Global grade + edge shading in-place, including safe-zone contrast.
        cv2.multiply(f, GRADE,dst=f,dtype=cv2.CV_8UC3)
        def project(ll):
            a,b=xy(*ll); return a*sc+mx,b*sc+my
        def text(s,x,y,size=32,weight=750,fill=WHITE,outline=0,bg='',pad=12,opacity=1):
            paste(f,label(s,size,weight,fill,outline,bg,pad),x,y,opacity)
        # Cartographic land borders only; the highlight is animated in the treaty scene.
        before = window(t,20.0,30.9,1.05)
        for line in borders:
            pts=[project(r) for r in line]
            drawline(f,pts,'#4b5354',5 if wide<17 else 3)
            drawline(f,pts,'#e8e5cc',2)
            if before>.1:
                p=ramp(t,24.02,28.15)
                a,b=sorted(pts,key=lambda l:l[0])[::max(1,len(pts)-1)][:2]
                end=(b[0]+(a[0]-b[0])*p,b[1]+(a[1]-b[1])*p)
                drawline(f,[end,b],'#ffcc70',4)
        count=sum(t>=v for v in CROSSINGS)
        card = window(t, -.4, 4.22,.4) if t<53.8 else ramp(t,53.8,54.94)
        text('O D D   S T A T E   O U T     /     0 2',350,102,19,820,MUTED,1)
        if card>.02:
            text('THE BORDER',350,198,67,850,WHITE,2,opacity=card)
            text('BUS',350,274,80,850,GOLD,2,opacity=card)
        section=window(t,4.1,54.15,.22)
        if section>.03:
            tag='THE MORNING RIDE' if t<12.1 or 30.90<=t<42.23 else ('THE LONG WAY AROUND' if t<20 else ('THE LINE ON THE MAP' if t<30.90 else 'THE RIDE HOME'))
            text(tag,350,166,19,800,WHITE,0,DARK,10,section)
        # Endpoint labels are attached to geography with short leaders at closer views.
        pp=project(POINT); bh=project(SCHOOL); bp=project(PORT)
        localview=wide<15.8 and cx<-123.004
        treaty=20.6<t<30.9
        if 47.80<t<53.65 or t<42.2 or 44.15<t<47.8:
            if 18<pp[0]<660:
                dot(f,*pp,'#102930',10); dot(f,*pp,GOLD,6)
                if localview:
                    ax=min(558,max(194,pp[0])); ay=pp[1]+39
                    text('POINT ROBERTS, WA',ax,ay,22,850,WHITE,0,DARK,8)
                else:
                    ax=min(568,max(123,pp[0])); ay=pp[1]+44
                    text('POINT ROBERTS, WA',ax,ay,18,850,WHITE,0,DARK,8)
            if 38<bh[0]<682 and not treaty:
                dot(f,*bh,'#102930',10);dot(f,*bh,GOLD,6)
                off=45 if wide>16 else 42
                text('BLAINE, WA' if t<35.6 or wide>18 else 'BLAINE HIGH SCHOOL',max(150,min(582,bh[0])),bh[1]+off,20,850,WHITE,0,DARK,8)
        # Use a checked local OSM line for stop 1; do not fake the cross-border bus route.
        onroad=t<8.48 or t>=53.65
        if onroad:
            if t>=53.65:
                lat=48.99675 + .00027*ramp(t,54.30,55)
            else:
                lat=ease_keys(t,[(0,48.99702),(3.8,49.00035),(6.98,49.00193),(7.57,BORDER),(8.48,49.00246)])[0]
            bus=project((float(np.interp(lat,ys,xs)),lat))
            roadpts=[project(p) for p in road]
            drawline(f,roadpts,'#263c3b',6)
            drawline(f,roadpts,'#f3b85a',2)
            vis=(1-ramp(t,8.18,8.48)) if t<10 else ramp(t,53.65,54.2)
            paste(f,bus_sprite(0),*bus,vis)
        if localview and not treaty:
            can = project((cx-.011,cy+.0135))
            if can[1]>307 and can[1]<463:
                text('BRITISH COLUMBIA',max(136,can[0]),can[1],19,800,WHITE,2)
        if 9<t<20.1 or 42.3<t<48.4:
            x,y=project((-122.965,48.942))
            if 160<x<550 and 600<y<770:
                text('B O U N D A R Y   B A Y',x,y,17,760,'#cce5dc',1)
        if 12.45<t<19.6 and wide>24:
            text('BRITISH COLUMBIA  ·  CANADA',350,382,22,800,WHITE,2,opacity=window(t,12.45,19.6,.52))
        pulse = window(t,15.19,16.82,.45)
        if pulse>.01 and 40<bh[0]<670:
            cv2.circle(f, (round(bh[0]),round(bh[1])), round(14+16*ramp(t,15.19,16.6)),
                       (int(94+21*pulse),int(120+52*pulse),int(124+78*pulse)), 2, cv2.LINE_AA)
        # Optional restrained country cards react around the actual numbered crossing.
        for start_ts,kind,pos in [(7.57,'CA',(-123.058,49.006)), (34.02,'US',None)]:
            op=window(t,start_ts+.05,start_ts+1.47,.24)
            if op>.01:
                x,y=project(pos) if pos else (576,450)
                paste(f,flag(kind,(t-start_ts)>.70 and (t-start_ts)<.85),x,y-22,op)
        if 22.23<t<30.87:
            text('1846',350,278,80,850,GOLD,2,opacity=window(t,22.23,30.87,.55))
            text('THE OREGON TREATY',350,343,22,850,WHITE,1,opacity=window(t,22.56,30.87,.55))
            if 25.75<t<30.5:
                text('49° N  ·  TREATY LINE',max(165,min(535,bp[0]+125)),bp[1]-29,17,800,WHITE,0,DARK,9,window(t,25.75,30.5,.35))
        # The regional panel is intentionally schematic, with no guessed port pins.
        if 30.9<t<36.64:
            paste(f,schematic(False,2 if t>=CROSSINGS[1] else 1),350,736,window(t,30.9,36.64,.27))
        if 43.97<t<51.17:
            paste(f,schematic(True,2 if count==4 else (1 if count==3 else 0)),350,745,window(t,43.97,51.17,.24))
        if 36.99<t<SLIP[0]+.10:
            op=window(t,36.99,SLIP[0]+.10,.31)
            text('≈40 MIN',350,717,63,850,GOLD,2,opacity=op)
            text('ONE WAY',350,764,21,850,WHITE,2,opacity=op)
        if SLIP[0]<t<SLIP[1]:
            a,b=SLIP
            paste(f,late_slip(),351,660-30*ramp(t,a,a+.28),window(t,a,b,.18))
        if count and 7.5<t<53.85 and not SLIP[0]<t<SLIP[1]:
            paste(f,counter(count),350,1006,window(t,7.54,53.85,.26))
        if t>=51.27 and t<53.62:
            text('ONE SCHOOL DISTRICT',350,725,27,820,GOLD,1,opacity=window(t,51.27,53.62,.25))
        if t<9.27 or t>54.35:
            text('© OpenStreetMap contributors  ·  GSHHG  ·  NOAA  ·  GMRT',350,1092,13,740,MUTED,1)
        # Subtitle emphasis and ambient tail are kept separate from graphics.
        for a,b,s in CAPS:
            if a<=t<b:
                hot=s in ('Canada.','One way.','Four border crossings,')
                text(s,350,897,43,830,GOLD if hot else WHITE,4)
                break
        return f
    return frame_at


def make_audio(out, *, crossings=None, whooshes=None, line_hit=27.94, paper=40.27, bell=42.32, dialogue=None, length=None, clicks=(), loop_street=None):
    sr=48000; length=LEN if length is None else length; n=round(sr*length); t=np.arange(n)/sr
    vo=np.zeros(n,np.float32)
    for path,at in ([(VOICE/(clip+'.flac'),at) for clip,at in CLIPS] if dialogue is None else dialogue):
        buf=subprocess.check_output([FFMPEG,'-v','error','-i',str(path),'-af',
            'highpass=f=78,acompressor=threshold=0.1:ratio=2.4:attack=12:release=100','-ar',str(sr),'-ac','1','-f','f32le','-'])
        a=np.frombuffer(buf,dtype='<f4').copy()
        st=round(at*sr); a=a[:min(n-st,len(a))]
        active=a[np.abs(a)>.010]; gain=.126/max(.021,np.sqrt(np.mean(active**2)))
        a[:200]*=np.linspace(0,1,200); a[-450:]*=np.linspace(1,0,450)
        vo[st:st+len(a)]+=a*gain
    rng=np.random.default_rng(44520)
    def filtered(lo,hi,length):
        return signal.sosfilt(signal.butter(2,[lo,hi],btype='bandpass',fs=sr,output='sos'),rng.standard_normal(length))
    # Seam-safe synthetic ambient tones and subdued air. No music/FX licensing dependencies.
    env=.62+.21*np.cos(2*np.pi*2*t/length)+.15*np.sin(2*np.pi*5*t/length)
    drone=sum(np.sin(2*np.pi*(round(f*length)*t/length)+i*.6)*v for i,(f,v) in enumerate([(55,.41),(82.41,.18),(110,.14),(130.81,.08),(164.81,.08)]))
    air=filtered(260,1100,n)
    cross=sr//4; q=np.linspace(0,1,cross,endpoint=False)
    air[:cross]=air[-cross:]* (1-q)+air[:cross]*q
    air[-cross:]=air[:cross][0]*q+air[-cross:]*(1-q)
    bed=drone*env*.021+air*.017
    if loop_street is not None:
        lift_out,lift_in=loop_street
        gate=np.clip((lift_out-t)/.58,0,1)+np.clip((t-lift_in)/.55,0,1)
        road=filtered(120,420,n)
        # Match noise/sine phases across the seam. Dialogue is never wrapped.
        q=np.linspace(0,1,sr//12,endpoint=False); road[-len(q):]=road[-len(q):]*(1-q)+road[0]*q
        pulse=np.sin(2*np.pi*round(77*length)*t/length)
        bed+=np.clip(gate,0,1)*(.010*road+.0045*pulse)
    fx=np.zeros(n)
    def add(at,d,synth):
        m=int(d*sr); s=int(at*sr); u=np.arange(m)/sr
        d=synth(u,m)[:min(m,n-s)]; fx[s:s+len(d)]+=d
    def tick(at,pitch):
        add(at,.23,lambda u,m: .095*(1-np.exp(-u/.004))*np.exp(-u/.048)*(np.sin(2*np.pi*(pitch*u-92*u*u))+.12*filtered(670,2800,m)))
    for idx,a in enumerate(CROSSINGS if crossings is None else crossings):tick(a,[298,341,315,385][idx])
    for a,d in ([(10.67,1.07),(21.94,.76),(31.45,.67),(44.3,.75),(53.36,.70)] if whooshes is None else whooshes):
        add(a,d,lambda u,m: filtered(360,1750,m)*.065*np.sin(np.pi*u/(m/sr))**2)
    tick(line_hit,174)
    for at,pitch in clicks: tick(at,pitch)
    add(paper,.18,lambda u,m:filtered(320,1800,m)*.086*np.exp(-u/.045)*np.minimum(1,u/.009))
    add(bell,1.05,lambda u,m: .047*(1-np.exp(-u/.006))*np.exp(-u/.19)*(np.sin(2*np.pi*785*u)+.31*np.sin(2*np.pi*1270*u)))
    voiced=signal.sosfilt(signal.butter(1,6,fs=sr,output='sos'),np.abs(vo))
    ambient=bed*np.clip(1-voiced*4,.49,1)
    mix=np.stack((vo+ambient+fx*.91,vo+ambient+fx*.96),axis=1)
    peak=np.max(np.abs(mix)); mix*=min(1.,.88/max(peak,.001))
    with wave.open(str(out),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((mix.clip(-1,1)*32767).astype('<i2').tobytes())


def timecode(t):
    ss,ms=divmod(round(t*1000),1000)
    return f'{ss//3600:02d}:{ss//60%60:02d}:{ss%60:02d},{ms:03d}'


def write_editor_data():
    (ROOT/'final_captions.srt').write_text('\n\n'.join(f'{i}\n{timecode(a)} --> {timecode(b)}\n{s}' for i,(a,b,s) in enumerate(CAPS,1))+'\n')
    def frames(t): return round(t*FPS)
    data={'runtime_seconds':LEN,'fps':FPS,'resolution':[1080,1920],'encoded_frames':FPS*LEN,
          'crossings':[{'number':i,'time_sec':t,'nearest_frame':frames(t),'from':('United States','Canada')[(i-1)%2], 'to':('Canada','United States')[(i-1)%2]} for i,t in enumerate(CROSSINGS,1)],
          'camera_keyframes':[{'nearest_frame':frames(t),'longitude':lon,'latitude':lat,'width_km':w} for t,lon,lat,w in CAM],
          'narration_starts_seconds':[at for _,at in CLIPS],
          'late_slip_seconds':SLIP, 'route_mode':'Mapped public Point Roberts approach; country-transition schematic for unconfirmed corridor.',
          'captions':[{'in_seconds':a,'out_seconds':b,'text':s} for a,b,s in CAPS]}
    (ROOT/'final_timeline.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--samples',action='store_true'); args=p.parse_args()
    scene=render_frames()
    if args.samples:
        for t in [0,2.5,7.7,16.1,26.9,33.2,37.9,41.1,47,51.4,54.96]:
            cv2.imwrite(str(DATA/f'frame-{t:05.2f}.jpg'),scene(t))
        return
    audio=DATA/'mix.wav'; make_audio(audio)
    out=ROOT/'final_short.mp4'; temp=DATA/'final-temp.mp4'
    cmd=[FFMPEG,'-y','-hide_banner','-loglevel','error','-threads','2','-f','rawvideo','-pixel_format','bgr24',
         '-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-i',str(audio),'-filter_threads','1',
         '-vf','scale=1080:1920:flags=lanczos:out_color_matrix=bt709,setsar=1','-af','loudnorm=I=-14:TP=-1.2:LRA=8,aresample=48000',
         '-c:v','libx264','-threads','2','-preset','veryfast','-profile:v','high','-crf','18','-pix_fmt','yuv420p',
         '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','256k','-movflags','+faststart',
         '-metadata','title=The School Bus That Leaves the Country','-t',str(LEN),str(temp)]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as enc:
        for i in range(LEN*FPS):
            enc.stdin.write(scene(i/FPS).tobytes())
            if i%300==0: print(f'{i}/{LEN*FPS} frames',flush=True)
        enc.stdin.close()
        if enc.wait(): raise RuntimeError('FFmpeg encode failed')
    temp.replace(out)
    write_editor_data()
    print(f'Complete: {out}',flush=True)

if __name__=='__main__': main()
