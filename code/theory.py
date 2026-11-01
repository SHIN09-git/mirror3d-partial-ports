import mpmath as mp
import numpy as np

def kernel(k): return mp.coth(k)/(2*k)-1/(2*mp.sinh(k)**2)


def stripe(a,b,m):
    p=mp.mpf(a)/b
    closed=1-p/3-(mp.zeta(3)-mp.re(mp.polylog(3,mp.exp(2j*mp.pi*p))))/(4*mp.pi**3*m*p)
    correction=-2/p*sum(mp.sin(mp.pi*j*p)**2/(mp.pi*j)**2*(kernel(2*mp.pi*m*j)-1/(4*mp.pi*m*j)) for j in range(1,31))
    # Alternative: rational-period Hurwitz sums; kernel obtained by integration.
    S=sum(mp.sin(mp.pi*r*p)**2*mp.zeta(3,mp.mpf(r)/b)/b**3 for r in range(1,b+1))
    alt=1-p/3-S/(2*mp.pi**3*m*p)
    quadrature_errors=[]
    for j in range(1,13):
        k=2*mp.pi*m*j
        integ=mp.quad(lambda x:(mp.sinh(k*x)/mp.sinh(k))**2,[0,mp.mpf('.5'),1])
        quadrature_errors.append(abs(integ-kernel(k)))
        alt-=2/p*mp.sin(mp.pi*j*p)**2/(mp.pi*j)**2*(integ-1/(2*k))
    exact=closed+correction
    assert abs(exact-alt)<mp.mpf('1e-45')
    return dict(p=float(p),m=m,series=str(exact),closed=str(closed),exponential_correction=str(correction),independent=str(alt),difference=str(abs(exact-alt)),max_quadrature_error=str(max(quadrature_errors)))


def square(K=8192):
    # All nonzero coefficients of a half interval are odd. Positive quadrant.
    n=np.arange(1,K+1,2,dtype=float);a2=1/(np.pi*n)**2
    def ik(k):
        e=np.exp(-2*k)
        return (1+e)/(1-e)/(2*k)-2*e/(1-e)**2
    axis=float(np.sum(a2*ik(2*np.pi*n)))
    cross=0.
    for start in range(0,len(n),128):
        ns=n[start:start+128]
        cross+=float(np.sum(a2[start:start+128,None]*a2[None,:]*ik(2*np.pi*np.hypot(ns[:,None],n[None,:]))))
    J=.25**2/3+axis+4*cross
    upper=1-J/.25
    # Union bound: omitted coefficient mass <= 2/(pi² K),
    # I(k)<=coth(2piK)/(4piK); divide by area 1/4.
    tail=2/(np.pi**3*K*K)*float(mp.coth(2*mp.pi*K))
    return dict(K=K,lower=upper-tail,upper=upper,tail_bound=tail)

