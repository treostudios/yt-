"""Read archived OSM road geometry and calculate the visual comparison."""
import math
from pathlib import Path
from shapely.geometry import LineString, Point

DATA=Path(__file__).parent/'route_data'
# WGS84 lon/lat endpoints at the Point Roberts and Blaine shorelines, snapped by
# shoreline_measurement() to the nearest mapped waterfront for this comparison.
WATER_START=(-123.0310,48.9960)
WATER_END=(-122.7760,48.9810)


def decode(name):
    text=(DATA/(name+'.polyline')).read_text().strip()
    it=iter(text)
    def delta(first):
        value, shift=0,0
        ch=first
        while True:
            n=ord(ch)-63
            if not 0<=n<=63 or shift>30: raise ValueError('Malformed polyline')
            value|=(n&31)<<shift
            if n<32: return -(value>>1)-1 if value&1 else value>>1
            shift+=5; ch=next(it)
    lat=lon=0; out=[]
    for ch in it:
        lat+=delta(ch); lon+=delta(next(it)); out.append((lon/1e5,lat/1e5))
    if any(not -123.10<x<-122.71 or not 48.98<y<49.16 for x,y in out):
        raise ValueError(f'{name} is outside expected roadway extent')
    return out


def distance(a,b):
    x,y,u,v=map(math.radians,(*a,*b)); q=math.sin((v-y)/2)**2+math.cos(y)*math.cos(v)*math.sin((u-x)/2)**2
    return 6371.0088*2*math.asin(math.sqrt(q))


def shoreline_measurement(land):
    from shapely.ops import nearest_points
    ends=[nearest_points(Point(v),land.boundary)[1] for v in (WATER_START,WATER_END)]
    probe=LineString(ends)
    # The east locator may be behind the spit. Use the first eastern shore hit,
    # rather than measuring across the land on the far side of the spit.
    cut=probe.intersection(land.boundary)
    hits=[]
    def scan(g):
        if g.geom_type=='Point':
            if probe.project(g)>probe.length*.7: hits.append(g)
        elif hasattr(g,'geoms'):
            for part in g.geoms: scan(part)
    scan(cut)
    if hits: ends[1]=min(hits,key=probe.project)
    ll=[(p.x,p.y) for p in ends]
    line=LineString(ll)
    if line.intersection(land).length>line.length*.025:
        raise ValueError('Water comparison crosses too much mapped land')
    return ll,distance(*ll)
