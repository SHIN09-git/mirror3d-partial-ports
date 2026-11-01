"""Save complete right-face marginals for transverse-orbit averaging."""
import numpy as np
from numba import njit
from kernel import trace_left,counts_from_dest

@njit(cache=True)
def sample_marginals(n,P,L,seed):
    np.random.seed(seed);out=np.zeros((n,4+2*L),np.uint32);M=np.empty(L**3,np.uint8)
    for i in range(n):
        for v in range(len(M)):M[v]=np.random.randint(len(P))
        dest=trace_left(M,P,L);c=counts_from_dest(dest,L)
        for j in range(4):out[i,j]=c[j]
        for e in dest:
            if e>=L*L:
                k=e-L*L;out[i,4+k//L]+=1;out[i,4+L+k%L]+=1
        assert out[i,4:4+L].sum()==c[0] and out[i,4+L:].sum()==c[0]
    return out

def orbit_features(a,L):
    n=len(a);N=a[:,0].astype(float);Y=a[:,4:4+L];Z=a[:,4+L:]
    assert np.all(Y.sum(axis=1)==N) and np.all(Z.sum(axis=1)==N)
    energy=(abs(np.fft.rfft(Y,axis=1))**2+abs(np.fft.rfft(Z,axis=1))**2)/2
    weight=np.full(L//2+1,2.);weight[0]=0.;weight[-1]=1.
    values=[]
    for m in [1,2,4]:
        mask=(L<=4*((m*np.arange(L))%L))&(4*((m*np.arange(L))%L)<3*L)
        assert np.all(Y@mask==a[:,[1,2,3][[1,2,4].index(m)]])
        q=energy@(abs(np.fft.rfft(mask))**2*weight)/(L*L)
        values.append(q)
    return np.column_stack([N,*values])

def estimate_features(f):
    n=len(f);mu=f[:,0].mean();v=f[:,0].var(ddof=1);q=f[:,1:].mean(axis=0)
    point=(.5*v+2*q)/mu
    IF=(.5*((f[:,0]-mu)**2-v)[:,None]+2*(f[:,1:]-q)-point*(f[:,0]-mu)[:,None])/mu
    return point,np.cov(IF,rowvar=False),IF
