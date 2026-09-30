import numpy as np, soundfile as sf
sr=44100; T=60; n=sr*T; t=np.arange(n)/sr
bpm=120; beat=60/bpm
out=np.zeros(n)
def env(length,a=0.005,d=0.3):
    x=np.arange(int(length*sr))/sr; return np.minimum(1,x/a)*np.exp(-x/d)
def add(sig,start):
    i=int(start*sr); j=min(n,i+len(sig)); out[i:j]+=sig[:j-i]
# kick on every beat from 4s to 58s (intro soft)
for k in range(int(T/beat)):
    s=k*beat
    if s<3.9 or s>58.5: continue
    L=0.35; x=np.arange(int(L*sr))/sr; f=50+90*np.exp(-x*30)
    kick=np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-x*9)*0.55
    add(kick,s)
# hats on off-beats
rng=np.random.default_rng(1)
for k in range(int(T/beat)):
    s=k*beat+beat/2
    if s<4 or s>58.5: continue
    L=0.06; h=rng.standard_normal(int(L*sr))*np.exp(-np.arange(int(L*sr))/sr*80)*0.08
    h=np.diff(np.concatenate([[0],h]))  # brighten
    add(h,s)
# bass / pad chord progression Am F C G, 2 bars each (4s)
chords=[(57,60,64),(53,57,60),(48,52,55),(55,59,62)]
mid=lambda m:440*2**((m-69)/12)
for bar in range(15):
    s=bar*4; c=chords[bar%4]; L=4
    x=np.arange(int(L*sr))/sr
    pad=sum(np.sin(2*np.pi*mid(m)*x)+0.3*np.sin(2*np.pi*mid(m)*2.003*x) for m in c)/len(c)
    pad*=np.minimum(1,x/0.8)*np.minimum(1,(L-x)/0.8)*0.10
    bass=np.sign(np.sin(2*np.pi*mid(c[0]-24)*x))*0.06
    gate=(np.sin(2*np.pi*x/(beat/2))>-0.2)*1.0
    add(pad+bass*gate*np.minimum(1,x/0.05),s)
# whooshes at scene changes
for s in [4,11,15,23,29,36,43,49,54]:
    L=0.7; x=np.arange(int(L*sr))/sr; w=rng.standard_normal(len(x))
    # simple lowpass via moving average with sweeping window
    w=np.convolve(w,np.ones(30)/30,'same')*np.sin(np.pi*x/L)**2*0.35
    add(w,s-0.5)
# logo 'land' thump at 1.2s and 55s
for s in [1.15,55.0]:
    L=0.6; x=np.arange(int(L*sr))/sr; add(np.sin(2*np.pi*(45+60*np.exp(-x*20))*x)*np.exp(-x*6)*0.7,s)
fade=np.ones(n); fo=int(2.5*sr); fade[-fo:]=np.linspace(1,0,fo); fade[:int(.3*sr)]=np.linspace(0,1,int(.3*sr))
out*=fade; out/=np.max(np.abs(out))*1.12
sf.write('music.wav',np.stack([out,out],1),sr)
print('ok')
