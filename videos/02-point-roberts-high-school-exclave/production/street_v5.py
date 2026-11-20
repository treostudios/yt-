"""CPU perspective street vignette; local coordinates in metres, north along +Y."""
from functools import lru_cache
import math
import cv2
import numpy as np

W,H=720,1280

def b(s): return tuple(bytes.fromhex(s.lstrip('#'))[::-1])

def sm(x):
    x=np.clip(x,0,1); return x*x*(3-2*x)

def box(x0,x1,y0,y1,z0,z1,colors):
    a=np.array([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],float)
    return [(a[list(idx)],col) for idx,col in zip([(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],colors)]

def flat(x0,x1,y0,y1,z,col):
    return np.array([(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)],float),col

@lru_cache(maxsize=14)
def flank(pose):
    """Near-side material, including students and seat backs, behind the window reflections."""
    im=np.full((220,820,3),b('ffbc36'),np.uint8)
    def rect(x,y,r,d,c,w=-1):cv2.rectangle(im,(x,y),(r,d),b(c),w,cv2.LINE_AA)
    def ln(a,z,c,w=2):cv2.line(im,a,z,b(c),w,cv2.LINE_AA)
    def circ(a,r,c,w=-1):cv2.circle(im,a,r,b(c),w,cv2.LINE_AA)
    rect(0,0,819,19,'ffdf69');rect(0,160,819,219,'e88e25')
    for j in range(7):
        x=23+103*j
        rect(x,28,x+96,117,'262f31');rect(x+5,34,x+90,112,'354c56')
        rect(x+7,94,x+88,111,'223640');rect(x+10,69,x+42,111,'526571')
        if j in (1,2,3,4,6):
            if j==6: h=0; skin='d7b08a'; shirt='97abba'
            else:
                h=round(math.sin(pose*.42+j*1.7)*2);skin=['d99866','85634f','eed0aa','ad7956'][j-1];shirt='ecede4'
            xx=x+58; yy=66+h
            cv2.ellipse(im,(xx-18,97),(13,17),0,0,360,b('d87757' if j==2 else '568f9a'),-1,cv2.LINE_AA)
            ln((xx-13,95),(xx-12,107),'1b3039',7)
            cv2.ellipse(im,(xx,97+h),(17,16),0,180,360,b(shirt),-1,cv2.LINE_AA)
            ln((xx-13,98+h),(xx-9,89+h),'314c68',4)
            ln((xx+10,89+h),(xx+13,98+h),'314c68',3)
            circ((xx,yy),15,skin);cv2.ellipse(im,(xx-2,yy-5),(15,12),0,180,355,b('252d32'),-1,cv2.LINE_AA)
            glance=3 if j==2 and 3<pose<9 else 0
            circ((xx+glance,yy),2,'19262b');circ((xx+7+glance,yy),2,'19262b')
            cv2.ellipse(im,(xx+4,yy+6),(4,2),0,6,158,b('654b44'),1,cv2.LINE_AA)
            ln((xx-6,87+h),(xx,91+h),'ddece9',2);ln((xx,91+h),(xx+5,87+h),'ddece9',2)
        ln((x+8,39),(x+84,39),'779697',1)
        ln((x+84,47),(x+75,62),'88a6a9',1)
        ln((x+4,113),(x+91,113),'16252c',2)
    rect(750,33,808,120,'26363b');rect(755,38,803,113,'66818a');ln((777,38),(777,113),'293c45',4)
    ln((750,30),(750,213),'9c642c',2);ln((809,30),(809,213),'9c642c',2)
    for y in (129,142,162): ln((8,y),(811,y),'333840',5 if y==142 else 3)
    cv2.putText(im,'SCHOOL BUS',(324,156),cv2.FONT_HERSHEY_DUPLEX,.41,b('253039'),1,cv2.LINE_AA)
    for x in range(17,806,69): circ((x,195),2,'bf7b29')
    return im

@lru_cache(maxsize=1)
def scenery():
    scene=[flat(-280,280,-250,430,-.055,'788f74'),flat(-4.6,4.6,-230,330,0,'88887f'),flat(-3.65,3.65,-230,330,.012,'454c51')]
    for x in [-3.53,3.53]:scene.append(flat(x-.042,x+.042,-230,330,.02,'e5ddd0'))
    for y in range(-110,230,11): scene.append(flat(-.07,.07,y,y+4.4,.023,'dfb65e'))
    rng=np.random.default_rng(43)
    for j in range(100):
        y=float(rng.uniform(-105,190)); x=float(rng.uniform(5.1,67))*int(rng.choice([-1,1]));
        width=float(rng.uniform(.9,3.8)); ht=width*float(rng.uniform(1.7,3.2)); z=0.
        # Keep the camera-side shoulder clear during the travelling student reveal.
        if 5<x<29 and -23<y<35: continue
        if j%3==0:
            scene.append(flat(x-1.2,x+width*.9,y-2,y+2,.003,'657f69'))
        top=np.array([x,y,ht]); pts=[np.array([x+width*math.cos(a),y+width*math.sin(a),ht*.3]) for a in np.arange(6)*math.pi/3]
        for k in range(6):
            scene.append((np.array([pts[k],pts[(k+1)%6],top]),['728e80','5b776c','506e65','4b685f','68867a','7d9787'][k]))
        if abs(x)<26:
            scene+=box(x-.09,x+.09,y-.09,y+.09,0,ht*.36,['685c4d']*5)
    return scene


def bus_geometry(s):
    faces=box(.36,2.91,s-5.3,s+3.8,.65,3.22,['df982b','texture','edab2c','efa62c','ffdb67'])
    # Beveled cap, front windscreen, hood and bumper.
    faces+=box(.49,2.78,s-5.15,s+3.65,3.18,3.43,['f2b93d','ffc344','f9c04b','f4b53a','ffe494'])
    faces+=box(.51,2.76,s+3.69,s+5.62,.68,1.98,['c88622','efac31','e6a126','eba02d','ffd15b'])
    faces+=box(.39,2.88,s+5.54,s+5.83,.65,.87,['27313a']*5)
    x=s+3.812
    faces.append((np.array([(.52,x,2.05),(2.74,x,2.05),(2.74,x,3.075),(.52,x,3.075)]),'374d56'))
    for a in (.63,2.42):
        faces+=box(a,a+.24,s+5.609,s+5.64,1.13,1.38,['faf0c6']*5)
    faces+=box(1.03,2.24,s+5.61,s+5.647,1.04,1.45,['38434b']*5)
    for y in (s-3.35,s+3.27):
        for x in (.345,2.925):
            outer=x+(.06 if x>1 else -.06); ang=np.arange(24)*math.pi/12
            def wheel(r,xx,col,phase=0):
                return np.column_stack((np.full(len(ang),xx),y+r*np.cos(ang+phase),.58+r*np.sin(ang+phase))),col
            faces.append(wheel(.57,x,'232b31')); faces.append(wheel(.53,outer,'2b3239'));faces.append(wheel(.29,outer+.009,'879296'))
            for k in range(4):
                a=k*math.tau/4-s/.58; u,v=math.cos(a),math.sin(a); xx=outer+.013
                faces.append((np.array([(xx,y+u*.09-v*.028,.58+v*.09+u*.028),(xx,y+u*.24-v*.015,.58+v*.24+u*.015),(xx,y+u*.24+v*.022,.58+v*.24-u*.022),(xx,y+u*.09+v*.028,.58+v*.09-u*.028)]),'56666c'))
    return faces


def render(frame, *, align=None, lift=0):
    """frame is continuous through zero at the loop; align can steer the lift target."""
    t=frame/60.; s=t*10.5  # ~24 mph while photographed at street scale
    u=sm((frame+4)/69); q=sm(lift)
    target=np.array([1.64,s,1.58]); pos=np.array([12+12*u,s-20+15*u,13-10.1*u]);
    if q:
        # Turn the road to screen-up while high, before the map enters.
        target=(1-q)*target+q*np.array([1.64,s+.17,0.])
        r=(1-q)*22+q*3.75; az=(-.21-1.358*sm((q-.17)/.74))
        pos=np.array([target[0]+r*math.cos(az),target[1]+r*math.sin(az),(1-q)*pos[2]+q*86.]);
    fw=target-pos;fw/=np.linalg.norm(fw); right=np.cross(fw,[0,0,1.]);right/=np.linalg.norm(right);up=np.cross(right,fw)
    mat=np.stack((right,up,fw),axis=1); fp=1165-70*q
    cx,cy=(350.,565.) if align is None else (350+(align[0]-350)*q,565+(align[1]-565)*q)
    def project(a):
        return np.column_stack((cx+fp*a[:,0]/a[:,2],cy-fp*a[:,1]/a[:,2]))
    sky=np.linspace(b('183248'),b('a8b5a0'),H).astype(np.uint8); im=np.broadcast_to(sky[:,None,:],(H,W,3)).copy()
    def visible(objs):
        for xyz,color in objs:
            a=(xyz-pos)@mat; good=a[:,2]>.28
            if not good.any():continue
            if not good.all():
                clipped=[]
                for a0,a1 in zip(a,np.roll(a,-1,axis=0)):
                    if a0[2]>=.28: clipped.append(a0)
                    if (a0[2]>.28)!=(a1[2]>.28):clipped.append(a0+(a1-a0)*(.28-a0[2])/(a1[2]-a0[2]))
                a=np.array(clipped)
                if len(a)<3:continue
            p=project(a)
            if not (-5<p[:,0].max() and p[:,0].min()<W+5 and -5<p[:,1].max() and p[:,1].min()<H+5):continue
            yield a[:,2].mean(),p,color
    def paint(o):
        for z,p,c in o:
            if c=='texture' and len(p)==4:
                m=cv2.getPerspectiveTransform(np.float32([[0,219],[819,219],[819,0],[0,0]]),p.astype('f'))
                patch=cv2.warpPerspective(flank(int(np.clip(frame//9,0,13))),m,(W,H),borderMode=cv2.BORDER_REPLICATE)
                mask=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(mask,np.round(p).astype('i'),255);cv2.copyTo(patch,mask,im)
            elif c!='texture':
                col=np.array(b(c)); fog=np.clip((z-50)/480,0,.32);col=tuple((col*(1-fog)+np.array(b('a5af9d'))*fog).astype(int).tolist())
                cv2.fillConvexPoly(im,np.round(p).astype('i'),col,cv2.LINE_AA)
    base=scenery()
    paint(visible(base[:3])); paint(sorted(visible(base[3:]),key=lambda x:-x[0]))
    shadow=np.array([(.28,s-6.0,.03),(3.3,s-6.5,.03),(3.85,s+4,.03),(.85,s+5.6,.03)])
    sh=list(visible([(shadow,'273c41')]))
    if sh:
        stencil=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(stencil,np.round(sh[0][1]).astype('i'),255,cv2.LINE_AA)
        shade=cv2.GaussianBlur(stencil,(11,11),3).astype(np.float32)*(.39/255);im[:]=(im*(1-shade[:,:,None])).astype(np.uint8)
    paint(sorted(visible(bus_geometry(s)),key=lambda x:-x[0]))
    y=np.arange(H)/H; x=np.arange(W)/W; vign=(.98-.27*np.clip((y-.56)/.44,0,1)**1.1)[:,None]*(1-.16*(2*x-1)**2)[None,:]
    im[:]=(im*vign[:,:,None]).astype(np.uint8)
    return im
