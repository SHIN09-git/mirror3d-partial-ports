"""Trace displayed quantities to the stored JSON values, including derived spreads."""
import csv,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES=['t3b_analysis','t3c_analysis','original_final','original_second','original_final_points','original_second_points','closed_form','retro_reconstruction','earlier_diagnostics','pooled','higher','spectrum','components','exploratory','holdout_response','matching_predictions','matching_extrapolations','analysis_replay','seed_replay','resources','derived_values']
SKIP={'bootstrap_intercepts','bootstrap_replicates','replicates','weights'}
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def derived():
    c=read(ROOT/'results/t3c_analysis.json');r=read(ROOT/'results/retro_reconstruction.json');e=read(ROOT/'results/exploratory.json')
    return dict(
      absolute_form_spread={f'r{m}':dict(absolute=c['joint'][f'r{m}']['1']['intercept']-c['joint'][f'r{m}']['2']['intercept'],percent=100*(c['joint'][f'r{m}']['1']['intercept']-c['joint'][f'r{m}']['2']['intercept'])/c['targets'][f'r{m}']) for m in [1,2,4]},
      reconstructed_N_range=[min(v['intercept'] for ds in r['derived_fits'].values() for v in ds['r_N'].values()),max(v['intercept'] for ds in r['derived_fits'].values() for v in ds['r_N'].values())],
      retro_z_range=[min(v['z'] for v in r['original_H4_comparison']),max(v['z'] for v in r['original_H4_comparison'])],
      diagnostic_samples=sum(v['n'] for v in e['pooled_cells']),
      all_stripe_samples=read(ROOT/'results/t3b_analysis.json')['samples']+c['samples'],
      replay_comparisons=sum(v['numeric_comparisons'] for v in read(ROOT/'results/analysis_replay.json')['results']),
      replay_environments=sum(v['n'] for v in read(ROOT/'results/seed_replay.json')['records']),
      note='Algebraic summaries of saved results; no new extrapolation or decision.')
def leaves(value,pointer=''):
    if isinstance(value,dict):
        for k,v in value.items():
            if k not in SKIP:yield from leaves(v,pointer+'/'+k.replace('~','~0').replace('/','~1'))
    elif isinstance(value,list):
        for i,v in enumerate(value):yield from leaves(v,pointer+'/'+str(i))
    elif isinstance(value,(int,float)) and not isinstance(value,bool):
        if math.isfinite(value):yield pointer,value,'integer' if isinstance(value,int) else 'float'
    elif isinstance(value,str):
        try:
            f=float(value)
            if math.isfinite(f):yield pointer,value,'decimal_string'
        except ValueError:pass
def collect():
    rows=[]
    paths=[ROOT/'results'/f'{n}.json' for n in SOURCES]+[ROOT/'preregistration'/f'{n}.json' for n in ['preregistration','t3b_preregistration','t3c_preregistration']]
    for p in paths:
        for pointer,val,kind in leaves(read(p)):rows.append(dict(source=p.relative_to(ROOT).as_posix(),pointer=pointer,value=repr(val) if isinstance(val,float) else str(val),kind=kind))
    return rows
def write_registry():
    (ROOT/'results/derived_values.json').write_text(json.dumps(derived(),indent=2)+'\n',encoding='utf-8')
    with (ROOT/'results/number_sources.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['source','pointer','value','kind']);w.writeheader();w.writerows(collect())
def verify_registry():
    assert derived()==read(ROOT/'results/derived_values.json')
    expected=list(csv.DictReader((ROOT/'results/number_sources.csv').open(encoding='utf-8')))
    actual=collect();assert len(expected)==len(actual)
    maximum=0.
    for a,b in zip(actual,expected):
        assert (a['source'],a['pointer'],a['kind'])==(b['source'],b['pointer'],b['kind'])
        if a['kind']=='float':
            d=abs(float(a['value'])-float(b['value']));maximum=max(maximum,d);assert d<=1e-12,(a,b)
        else:assert a['value']==b['value'],(a,b)
    return dict(entries=len(actual),max_float_difference=maximum,deterministic_quantities_exact=True)
