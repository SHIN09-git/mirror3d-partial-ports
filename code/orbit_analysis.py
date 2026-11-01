import numpy as np
KEYS=['rN','r1','r2','r4','raw1','raw2','raw4','delta41']

def bootstrap_features(a,L,seed,B):
    n=len(a);integer=a
    assert integer.shape[1]==7
    u,w=np.unique(integer,axis=0,return_counts=True);u=u.astype(float);u[:,1:4]/=2*L
    counts=u[:,[0,4,5,6]];mu=w@counts/n;d=counts-mu
    F=np.c_[d,d*d,u[:,1:4]]
    def calc(W):
        v=W@F/n;dm=v[...,:4];mean=mu+dm;var=(v[...,4:8]-dm*dm)*n/(n-1)
        raw=var/mean;orb=(.5*var[...,0,None]+2*v[...,8:11])/mean[...,0,None]
        return np.concatenate([raw[...,0,None],orb,raw[...,1:],(orb[...,2]-orb[...,0])[...,None]],axis=-1)
    point=calc(w);rng=np.random.default_rng(seed);reps=[];check=0.
    for first in range(0,B,16):
        W=rng.multinomial(n,w/n,size=min(16,B-first));v=calc(W);reps.extend(v)
        if first==0:
            for j in range(8):
                m=np.average(counts,axis=0,weights=W[j]);vr=np.sum(W[j,:,None]*(counts-m)**2,axis=0)/(n-1)
                q=np.average(u[:,1:4],axis=0,weights=W[j]);orb=(.5*vr[0]+2*q)/m[0]
                direct=np.r_[vr[0]/m[0],orb,vr[1:]/m[1:],orb[2]-orb[0]]
                check=max(check,float(abs(direct-v[j]).max()))
    assert check<1e-9
    reps=np.array(reps)
    return dict(n=n,means_counts=(w@counts/n).tolist(),estimate=dict(zip(KEYS,map(float,point))),
        se=dict(zip(KEYS,map(float,reps.std(axis=0,ddof=1)))),bootstrap_replicates={k:reps[:,j].tolist() for j,k in enumerate(KEYS)},
        seed=seed,B=B,unique_rows=len(u),max_independent_weighted_error=check)

