"""Replay recorded stripe blocks; never creates new seeds."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
import argparse,hashlib,json,pathlib,sys,time
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'))
from pairings import pairing_table
from kernel import sample
from sampler import sample_marginals
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def generate(stage,block):
    fn=sample if stage=='t3b' else sample_marginals
    parts=[fn(min(250,block['n']-250*i),pairing_table(block['rule']),block['L'],s) for i,s in enumerate(block['seeds']) if 250*i<block['n']]
    return np.concatenate(parts)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',choices=['t3b','t3c','both'],default='both')
    ap.add_argument('--all-recorded-blocks',action='store_true',help='Slow: regenerates the entire selected stripe data set.')
    ap.add_argument('--output-dir',type=pathlib.Path,default=ROOT/'replayed_blocks')
    args=ap.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    cases=read(ROOT/'preregistration/replay_cases.json');records=[];t=time.perf_counter();cpu=time.process_time()
    for stage in ['t3b','t3c'] if args.stage=='both' else [args.stage]:
        blocks=read(ROOT/'preregistration'/f'{stage}_chunk_index.json')
        chosen={int(pathlib.PurePosixPath(c['original_file']).stem.split('_')[1]):c for c in cases if c['stage']==stage}
        for b in blocks:
            if not args.all_recorded_blocks and b['index'] not in chosen:continue
            a=generate(stage,b);raw=hashlib.sha256(a.tobytes()).hexdigest()
            p=args.output_dir/f"{stage}_chunk_{b['index']:05d}.npy";np.save(p,a,allow_pickle=False)
            filehash=hashlib.sha256(p.read_bytes()).hexdigest()
            expected=chosen.get(b['index'])
            good=filehash==b['sha256'] and (expected is None or raw==expected['array_sha256'])
            records.append(dict(stage=stage,index=b['index'],rule=b['rule'],L=b['L'],n=len(a),seeds=b['seeds'],shape=list(a.shape),dtype=str(a.dtype),array_sha256=raw,npy_sha256=filehash,passed=good))
            print(stage,b['index'],len(a),'PASS' if good else 'FAIL',flush=True)
    report=dict(passed=all(r['passed'] for r in records),records=records,cpu_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,new_seeds=0)
    (args.output_dir/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
