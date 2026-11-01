"""Replay the original environment bootstrap and both polynomial extrapolations."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
import argparse,json,pathlib,sys,time
import numpy as np
from scipy.stats import norm
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'))
from orbit_analysis import bootstrap_features,KEYS as ORBIT_KEYS
from paired_analysis import bootstrap,fit,holm,KEYS as PAIRED_KEYS

def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def compare(a,b,path='',report=None):
    if report is None:report=dict(numbers=0,max_abs_difference=0.,max_difference_path='',structural_differences=[])
    if isinstance(a,dict):
        if not isinstance(b,dict) or a.keys()!=b.keys():report['structural_differences'].append(path+'/keys');return report
        for k in a:compare(a[k],b[k],path+'/'+str(k),report)
    elif isinstance(a,list):
        if len(a)!=len(b):report['structural_differences'].append(path+'/length');return report
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i),report)
    elif isinstance(a,(int,float)) and not isinstance(a,bool):
        report['numbers']+=1;d=abs(a-b)
        if d>report['max_abs_difference']:report.update(max_abs_difference=d,max_difference_path=path)
    elif a!=b:report['structural_differences'].append(path)
    return report

def analyse(stage):
    cfg=read(ROOT/'preregistration'/f'{stage}_preregistration.json');rows=[];checks=[];keys=ORBIT_KEYS if stage=='t3c' else PAIRED_KEYS
    for cell in cfg['cells']:
        a=np.load(ROOT/'data'/f"{stage}_{cell['rule']}_L{cell['L']}.npz",allow_pickle=False)['observations']
        assert len(a)==cell['N']
        stats=bootstrap_features(a,cell['L'],cell['bootstrap_seed'],cfg['B']) if stage=='t3c' else bootstrap(a,cell['bootstrap_seed'],cfg['B'])
        ref=read(ROOT/'results'/f'{stage}_cells'/f"{cell['rule']}_L{cell['L']}.json")
        c=compare(stats,ref);c.update(rule=cell['rule'],L=cell['L']);checks.append(c)
        rows.append(dict(rule=cell['rule'],L=cell['L'],stats=stats));print('REPLAY',stage,cell['rule'],cell['L'],c['max_abs_difference'],flush=True)
    separate={r:{k:{str(p):fit([row for row in rows if row['rule']==r],k,p) for p in [1,2]} for k in keys} for r in cfg['rules']}
    result=read(ROOT/'results'/f'{stage}_analysis.json')
    if stage=='t3c':
        joint={k:{str(p):fit(rows,k,p,True) for p in [1,2]} for k in keys};pvals={};gates={}
        for k in ['r1','r2','r4']:
            gates[k]={}
            for p in ['1','2']:
                a=separate['standard'][k][p];b=separate['orthogonal'][k][p];v=joint[k][p]
                z=(v['intercept']-cfg['targets'][k])/v['se'];pvals[k+'_'+p]=float(2*norm.sf(abs(z)));v['theory_z']=z
                gates[k][p]=dict(fit=min(v['p_fit'],a['p_fit'],b['p_fit'])>=cfg['minimum_fit_p'],rule_agreement=abs(a['intercept']-b['intercept'])<=3*np.hypot(a['se'],b['se']),precision=v['se']<=cfg['maximum_joint_se'])
        rejected=holm(pvals,cfg['family_alpha']);verdict={}
        for k in ['r1','r2','r4']:
            ok=all(all(gates[k][p].values()) for p in ['1','2']);neg=all(k+'_'+p in rejected for p in ['1','2']);signs=joint[k]['1']['theory_z']*joint[k]['2']['theory_z']>0
            verdict[k]='inconclusive_gate' if not ok else ('robust_rejection' if neg and signs else ('compatible_at_resolution' if all(k+'_'+p not in rejected for p in ['1','2']) else 'inconclusive_form'))
        fresh=dict(separate=separate,joint=joint,gates=gates,primary_pvalues=pvals,holm_rejected=rejected,verdict=verdict)
    else:
        joint={};pvals={};agreement=[]
        for power in [1,2]:
            v=fit(rows,'delta41',power,True);joint[str(power)]=v
            for name,target in [('zero',0.),('theory',cfg['targets']['delta41'])]:
                z=(v['intercept']-target)/v['se'];pvals[f'{name}_{power}']=float(2*norm.sf(abs(z)));v[name+'_z']=z
            va=separate['standard']['delta41'][str(power)];vb=separate['orthogonal']['delta41'][str(power)]
            agreement.append(dict(power=power,z=(va['intercept']-vb['intercept'])/np.hypot(va['se'],vb['se'])))
        rejected=holm(pvals,cfg['family_alpha'])
        fit_ok=all(v['p_fit']>=cfg['minimum_fit_p'] for v in joint.values()) and all(separate[r]['delta41'][str(p)]['p_fit']>=cfg['minimum_fit_p'] for r in cfg['rules'] for p in [1,2])
        rule_ok=all(abs(v['z'])<=3 for v in agreement);precise=all(v['se']<=cfg['maximum_joint_se'] for v in joint.values())
        fresh=dict(separate=separate,joint_delta=joint,primary_pvalues=pvals,holm_rejected=rejected,rule_agreement=agreement,gates=dict(fit=fit_ok,rule_agreement=rule_ok,precision=precise),geometry_dependent_contrast_supported=fit_ok and rule_ok and all(f'zero_{p}' in rejected and joint[str(p)]['intercept']>0 for p in [1,2]),theory_contrast_compatible_at_resolution=fit_ok and rule_ok and precise and all(f'theory_{p}' not in rejected for p in [1,2]))
    c=compare(fresh,{k:result[k] for k in fresh});checks.append(dict(kind='all_fits_and_decisions',**c))
    maximum=max(x['max_abs_difference'] for x in checks);struct=sum(len(x['structural_differences']) for x in checks)
    return dict(stage=stage,passed=maximum<=1e-12 and struct==0,max_abs_difference=maximum,numeric_comparisons=sum(x['numbers'] for x in checks),structural_differences=struct,checks=checks,samples=sum(r['stats']['n'] for r in rows),bootstrap_seeds=[c['bootstrap_seed'] for c in cfg['cells']],tolerance=1e-12)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['t3b','t3c','both'],default='t3c');ap.add_argument('--output',type=pathlib.Path,default=ROOT/'reproduction_analysis.json');args=ap.parse_args()
    t=time.perf_counter();c=time.process_time();results=[analyse(s) for s in (['t3b','t3c'] if args.stage=='both' else [args.stage])]
    report=dict(passed=all(r['passed'] for r in results),results=results,cpu_s=time.process_time()-c,wall_s=time.perf_counter()-t,python=sys.version.split()[0],numpy=np.__version__)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('RESULT',report['passed'],report['cpu_s'],flush=True)
    if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
