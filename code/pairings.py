import numpy as np

def pairing_table(rule):
    if rule=='nsso':
        return np.array([[1,0,3,2],[1,0,3,2],[2,3,0,1],[3,2,1,0]],np.int32)
    def rec(rem):
        if not rem: yield []; return
        a=rem[0]
        for b in rem[1:]:
            for rest in rec([x for x in rem if x not in (a,b)]): yield [(a,b)]+rest
    result=[]
    for pairs in rec(list(range(6))):
        if rule=='orthogonal' and any(b==(a^1) for a,b in pairs): continue
        p=np.empty(6,np.int32)
        for a,b in pairs: p[a]=b; p[b]=a
        result.append(p)
    assert len(result)==(8 if rule=='orthogonal' else 15)
    return np.array(result)

