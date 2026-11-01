"""Frozen paired empirical bootstrap and separate/joint extrapolation."""
import numpy as np
from scipy.stats import chi2,norm


KEYS=['rN','r1','r2','r4','delta41']
def bootstrap(a,seed,B=2000):
    x=a.astype(float);n=len(x);mu=x.mean(axis=0);u,w=np.unique(a,axis=0,return_counts=True);d=u.astype(float)-mu
    F=np.c_[d,d*d]
    def calc(v):
        dm=v[...,:4];v2=v[...,4:];r=(v2-dm*dm)*n/(n-1)/(mu+dm)
        return np.concatenate([r,(r[...,3]-r[...,1])[...,None]],axis=-1)
    point=calc(w@F/n);rng=np.random.default_rng(seed);reps=[];check=0.
    for start in range(0,B,16):
        W=rng.multinomial(n,w/n,size=min(16,B-start));v=calc(W@F/n);reps.extend(v)
        if start==0:
            for j in range(8):
                m=np.average(u,axis=0,weights=W[j]);vv=np.sum(W[j,:,None]*(u-m)**2,axis=0)/(n-1);r=vv/m
                other=np.r_[r,r[3]-r[1]];check=max(check,float(abs(other-v[j]).max()))
    reps=np.array(reps);assert check<1e-10
    direct=x.var(axis=0,ddof=1)/mu;assert np.max(abs(point[:4]-direct))<1e-10
    IF=((x-mu)**2-x.var(axis=0,ddof=1)-direct*(x-mu))/mu
    IF=np.c_[IF,IF[:,3]-IF[:,1]];ise=IF.std(axis=0,ddof=1)/np.sqrt(n);se=reps.std(axis=0,ddof=1)
    assert np.all((ise/se>.85)&(ise/se<1.15))
    return dict(n=n,means=mu.tolist(),estimate=dict(zip(KEYS,map(float,point))),se=dict(zip(KEYS,map(float,se))),
                influence_se=dict(zip(KEYS,map(float,ise))),bootstrap_replicates={k:reps[:,j].tolist() for j,k in enumerate(KEYS)},
                weighted_check_error=check,seed=seed,B=B)

def fit(rows,key,power,joint=False):
    L=np.array([r['L'] for r in rows],float);y=np.array([r['stats']['estimate'][key] for r in rows]);se=np.array([r['stats']['se'][key] for r in rows])
    reps=np.array([r['stats']['bootstrap_replicates'][key] for r in rows]);x=16/L
    if joint:
        X=np.column_stack([np.ones(len(L))]+[x**j*np.array([r['rule']==rule for r in rows]) for rule in ['standard','orthogonal'] for j in range(1,power+1)])
    else:X=np.column_stack([x**j for j in range(power+1)])
    A=X/se[:,None];Q,R=np.linalg.qr(A);P=np.linalg.solve(R,Q.T)/se
    beta=P@y;br=P@reps;c=float(np.sum(((y-X@beta)/se)**2));df=len(y)-len(beta)
    # Independent solve used only for a numerical implementation check.
    other=np.linalg.solve(A.T@A,A.T@(y/se));assert np.max(abs(other-beta))<1e-8
    return dict(intercept=float(beta[0]),se=float(br[0].std(ddof=1)),p_fit=float(chi2.sf(c,df)),chi2=c,dof=df,
                coefficients_scaled_x=beta.tolist(),x_definition='16/L',sizes=L.astype(int).tolist(),
                bootstrap_intercepts=br[0].tolist(),common_intercept=joint)

def holm(pvalues,alpha):
    names=sorted(pvalues,key=pvalues.get);rejected=[]
    for j,k in enumerate(names):
        if pvalues[k]<=alpha/(len(names)-j):rejected.append(k)
        else:break
    return rejected
