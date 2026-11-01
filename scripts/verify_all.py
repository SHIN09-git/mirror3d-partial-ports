"""Verify the sealed release, rebuild every table/figure, and repeat continuum checks."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
import argparse,hashlib,json,pathlib,sys,time
import numpy as np
import mpmath as mp
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'))
from theory import stripe,square
from numeric_sources import verify_registry,read
from make_tables import build as tables
from make_figures import build as figures
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=pathlib.Path,default=ROOT/'reproduction_verification.json');args=ap.parse_args()
    started=time.perf_counter();cpu=time.process_time()
    manifest=read(ROOT/'results/release_manifest.json')
    for name,h in manifest['files'].items():assert sha(ROOT/name)==h,'Input hash mismatch: '+name
    nums=verify_registry();count=0
    for cell in read(ROOT/'data/manifest.json'):
        a=np.load(ROOT/cell['file'],allow_pickle=False)['observations']
        assert list(a.shape)==cell['shape'] and str(a.dtype)==cell['dtype'];count+=len(a)
    mp.mp.dps=65;ref=read(ROOT/'results/closed_form.json');d=0.
    for abm,v in zip([(1,2,1),(1,2,2),(1,2,4),(3,10,1),(1,10,1),(1,4,1),(1,1,1)],ref['stripes']):
        fresh=stripe(*abm);err=abs(mp.mpf(fresh['series'])-mp.mpf(v['series']));d=max(d,float(err));assert err<mp.mpf('1e-50')
    sq=square();assert max(abs(sq[k]-ref['square'][k]) for k in ['lower','upper','tail_bound'])<=1e-12
    tables();figures()
    outputs={p.relative_to(ROOT).as_posix():sha(p) for folder in ['paper/tables','paper/figures'] for p in sorted((ROOT/folder).iterdir()) if p.is_file()}
    for name,h in outputs.items():assert h==manifest['files'][name],'Rebuilt output differs: '+name
    report=dict(passed=True,python=sys.version.split()[0],numpy=np.__version__,numeric_registry=nums,compact_environments=count,input_files=len(manifest['files']),closed_form_max_difference=d,square=sq,rebuilt_files=outputs,cpu_s=time.process_time()-cpu,wall_s=time.perf_counter()-started)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS',nums['entries'],'numeric sources;',count,'environments;',len(outputs),'rebuilt outputs;',round(report['wall_s'],2),'seconds')
if __name__=='__main__':main()
