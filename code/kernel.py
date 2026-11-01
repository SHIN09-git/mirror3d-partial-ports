"""Full-open left endpoint tracing; paired mask counts share each environment."""
import numpy as np
from numba import njit

@njit(cache=True)
def trace_left(M,P,L):
    out=np.full(L*L,-1,np.int32)
    for k in range(L*L):
        if out[k]>=0:continue
        x=0;y=k//L;z=k%L;din=1;steps=0
        while True:
            d=P[M[(x*L+y)*L+z],din]
            if d==0:
                if x==L-1:out[k]=L*L+y*L+z;break
                x+=1
            elif d==1:
                if x==0:
                    e=y*L+z;out[k]=e;out[e]=k;break
                x-=1
            elif d==2:y=(y+1)%L
            elif d==3:y=(y-1)%L
            elif d==4:z=(z+1)%L
            else:z=(z-1)%L
            din=d^1;steps+=1
            if steps>24*L**3:raise ValueError('nonterminating path')
    return out

@njit(cache=True)
def counts_from_dest(dest,L):
    counts=np.zeros(4,np.int32)
    for e in dest:
        if e<L*L:continue
        y=(e-L*L)//L;counts[0]+=1
        for k in range(3):
            m=1<<k;phase=(m*y)%L
            if L<=4*phase<3*L:counts[k+1]+=1
    return counts

@njit(cache=True)
def sample(n,P,L,seed):
    np.random.seed(seed);out=np.empty((n,4),np.uint16);M=np.empty(L**3,np.int32)
    for i in range(n):
        for v in range(len(M)):M[v]=np.random.randint(len(P))
        c=counts_from_dest(trace_left(M,P,L),L)
        assert c[0]%2==0 and c[0]<=L*L
        for k in range(1,4):assert 0<=c[k]<=c[0]
        out[i]=c
    return out
