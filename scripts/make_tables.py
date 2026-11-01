"""Render reported tables directly from preserved analysis outputs. No new fits."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/tables'
def read(name):return json.loads((ROOT/'results'/f'{name}.json').read_text(encoding='utf-8-sig'))
def fmt(x,n=6):return f'{x:.{n}f}'
def pm(v):return '$'+rf"{v['intercept']:.6f}\pm{v['se']:.6f}"+'$'
def prob(p):return f'{p:.3g}'
def esc(s):return str(s).replace('_',r'\_').replace('&',r'\&')
def table(name,caption,heads,rows,long=False,spec=None):
    OUT.mkdir(parents=True,exist_ok=True);spec=spec or 'l'+'r'*(len(heads)-1)
    if long:
        text=r'{\small\setlength{\tabcolsep}{3.5pt}'+'\n'+rf'\begin{{longtable}}{{{spec}}}'+'\n'+rf'\caption{{{caption}}}\\'+'\n'
        header=r'\toprule'+'\n'+' & '.join(heads)+r'\\'+'\n'+r'\midrule'+'\n'
        text+=header+r'\endfirsthead'+'\n'+header+r'\endhead'+'\n'+r'\bottomrule\endfoot'+'\n'
    else:
        text=rf'\begin{{table}}[htbp]\centering\small\caption{{{caption}}}'+'\n'+rf'\begin{{tabular}}{{{spec}}}\toprule'+'\n'+' & '.join(heads)+r'\\\midrule'+'\n'
    text+='\n'.join(' & '.join(str(x) for x in row)+r'\\' for row in rows)+'\n'
    text+=(r'\end{longtable}}' if long else r'\bottomrule\end{tabular}\end{table}')+'\n'
    (OUT/f'{name}.tex').write_text(text,encoding='utf-8')
GEOM={'cube':'Cube','rect':'Wide slab','gap':'Gap, wall A','wall2':'Gap, wall B','neck':'Constriction','retro':'Retroreflection'}
OBS={'r2':r'$v$','r3':r'$h$','r4':r'$\kappa_4/\kappa_1$','covXY_over_n3':r'$\mathrm{Cov}(X,Y)/\mu_3$','idA':r'$d_A$','idB':r'$d_B$','idC':r'$d_C$','equal12_13':r'$e_{12,13}$','equal12_23':r'$e_{12,23}$','equal13_23':r'$e_{13,23}$'}
EXP={'vN':r'$v_N$','hN':r'$h_N$','v_half':r'$v_{1/2,1}$','v_quarter_strip':'Quarter strip','v_quarter_square':'Square','h_half':r'$h_{1/2,1}$','v_square_minus_strip':'Square minus strip'}
def build():
    c=read('t3c_analysis');b=read('t3b_analysis');o=read('original_final');e=read('exploratory')
    table('primary','Half-open stripe ratios. Errors are bootstrap standard errors; both prescribed extrapolations use all four sizes.',['$m$','Theory','Linear','Quadratic'],[[m,fmt(c['targets'][f'r{m}'],9),pm(c['joint'][f'r{m}']['1']),pm(c['joint'][f'r{m}']['2'])] for m in [1,2,4]])
    rows=[]
    for name in ['H1_cube_r2','H3_gap','H3_wall2','H4_retro']:
        x=next(v for v in o['endpoints'] if v['name']==name)
        for r,fs in x['fits'].items():rows.append([GEOM[x['geom']],r.title(),pm(fs['a+b/L']),pm(fs['a+b/L+c/L2'])])
    table('baselines',r'Original boundary tests, with one-standard-error uncertainties. Cube and retroreflection were tested against $2/3$. The covariance target for each gapped wall is $0.5138587$ with a deterministic allowance $0.0018720$, distinct from a statistical error.',['Geometry / observable','Rule','Linear','Quadratic'],rows,spec='llrr')
    rows=[]
    for x in e['cohort_fits']:
        if x['cohort']=='pooled_old_diagnostics' and x['rule']=='joint' and x['observable'] in ['v_quarter_strip','v_quarter_square','v_square_minus_strip']:
            rows.append([EXP[x['observable']],fmt(x['linear']['target'],9),pm(x['linear']),pm(x['quadratic'])])
    table('exploratory','Exploratory quarter-open results. Joint fits are descriptive; neither batch nor rule is discarded.',['Observable','Target','Linear','Quadratic'],rows)
    status={'COMPATIBLE_AT_ACHIEVED_PRECISION':'C','INCONCLUSIVE_FIT':'F','INCONCLUSIVE_PRECISION':'P','INCONCLUSIVE_DISAGREEMENT_OR_GUARD':'D','ROBUST_REJECTION':'R'}
    rows=[]
    for i,x in enumerate(o['endpoints'],1):rows.append([i,GEOM[x['geom']],OBS[x['key']],fmt(x['target'],6),status[x['status']],prob(x['p_endpoint'])])
    table('decisions','All 30 original decisions. C: consistency at attained precision; F: fit criterion failed; P: insufficient precision; D: disagreement or guard; R: robust rejection. C is not an equivalence result.',['ID','Geometry','Observable','Target','Result','$p$'],rows,True,'rllrrr')
    rows=[]
    for i,x in enumerate(o['endpoints'],1):
        for r,fs in x['fits'].items():
            for j,(form,f) in enumerate(fs.items(),1):rows.append([i,r[0].upper(),j,pm(f),prob(f['p_fit']),fmt(f['chi2'],3),f['dof']])
    table('original_fits','All 120 original fits. S/O: standard/orthogonal; degree 1/2 means the prescribed linear/quadratic fit in inverse size. All use sizes 16, 32, 64, 96.',['ID','Rule','Degree','Intercept','$p_{\\rm fit}$','$\\chi^2$','dof'],rows,True)
    ordered=sorted(enumerate(o['endpoints'],1),key=lambda q:q[1]['p_endpoint']);alpha=0.002699796063260207;rows=[];stopped=False
    for rank,(i,x) in enumerate(ordered,1):
        threshold=alpha/(31-rank);passed=not stopped and x['p_endpoint']<=threshold;stopped=stopped or not passed
        rows.append([rank,i,prob(x['p_endpoint']),prob(threshold),'yes' if passed else 'no'])
    table('holm','Original Holm step-down sequence across all 30 tests; the family level is the fixed two-sided three-standard-error probability. Rejection also requires the physical and fit guards.',['Rank','ID','$p$','Threshold','Step rejects'],rows,True)
    p=json.loads((ROOT/'preregistration/preregistration.json').read_text(encoding='utf-8-sig'));rows=[]
    for stage,label in [('G3','Initial'),('G4','Fixed addition')]:
        for x in p['datasets'][stage]:rows.append([label,GEOM[x['geom']],x['rule'][0].upper(),x['L'],f"{x['N']:,}"])
    table('allocations','Complete original sample allocation. The fixed addition does not change the original second-cumulant or covariance samples.',['Data','Geometry','Rule','$L$','Environments'],rows,True,'lllrr')
    rows=[]
    for stage,label in [('t3b','Layout'),('t3c','Absolute')]:
        p=json.loads((ROOT/'preregistration'/f'{stage}_preregistration.json').read_text(encoding='utf-8-sig'))
        for x in p['cells']:rows.append([label,x['rule'].title(),x['L'],f"{x['N']:,}",x['bootstrap_seed']])
    table('stripe_allocations','Stripe sample allocation and fixed bootstrap seeds. Physical seeds are recorded separately.',['Data','Rule','$L$','Environments','Bootstrap seed'],rows,True,'llrrr')
    rows=[]
    for r in ['standard','orthogonal','joint']:
        fs=c['joint'] if r=='joint' else c['separate'][r]
        for k in ['rN','r1','r2','r4','raw1','raw2','raw4','delta41']:
            for degree,f in fs[k].items():rows.append([r[0].upper(),esc(k),degree,pm(f),prob(f['p_fit'])])
    table('absolute_fits','All absolute-data fits, including full-face, raw fixed-mask and contrast diagnostics. The three symmetry-averaged stripe ratios alone belong to the primary family.',['Rule','Quantity','Degree','Intercept','$p_{\\rm fit}$'],rows,True)
    rows=[]
    for r,fs in b['separate'].items():
        for k,ds in fs.items():
            for degree,f in ds.items():rows.append([r[0].upper(),esc(k),degree,pm(f),prob(f['p_fit'])])
    for degree,f in b['joint_delta'].items():rows.append(['J',r'$\Delta v$',degree,pm(f),prob(f['p_fit'])])
    table('layout_fits','All layout-data fits. Absolute ratios are secondary diagnostics; the paired difference is primary.',['Rule','Quantity','Degree','Intercept','$p_{\\rm fit}$'],rows,True)
    rows=[]
    for name,label in [('t3b_analysis','Layout'),('t3c_analysis','Absolute')]:
        x=read(name)
        for k,pv in x['primary_pvalues'].items():rows.append([label,esc(k),prob(pv),'yes' if k in x['holm_rejected'] else 'no'])
    table('stripe_tests','All raw primary probabilities and Holm rejections for the two independent stripe families.',['Family','Test','$p$','Rejected'],rows,True,'llrr')
    rows=[]
    for x in e['cohort_fits']:
        cohort={'D1_calibration':'Calibration','D2_previous_holdout':'Held-out','pooled_old_diagnostics':'Combined'}[x['cohort']]
        for degree,f in [(1,x['linear']),(2,x['quadratic'])]:rows.append([cohort,x['rule'][0].upper(),EXP[x['observable']],degree,pm(f),prob(f['pfit'])])
    table('exploratory_fits','All exploratory diagnostic fits, including both batches separately and together, both rules and descriptive joint fits. No additional confirmation decision is made.',['Data','Rule','Observable','Degree','Intercept','$p_{\\rm fit}$'],rows,True,'lllrrr')
    rows=[]
    for x in e['legacy_sixth_fits']:rows.append([x['rule'][0].upper(),esc(x['observable']),x['degree'],fmt(x['target'],9),pm(x),prob(x['p_fit'])])
    table('third_fits','All auxiliary third-cumulant fits for the fresh half-open data, with refined deterministic targets.',['Rule','Quantity','Degree','Target','Intercept','$p_{\\rm fit}$'],rows,True)
    rows=[]
    for variant,fs in read('pooled')['fits'].items():
        for rule,obs in fs.items():
            for key,ds in obs.items():
                for degree,f in ds.items():rows.append(['Fixed' if variant=='fixed_masks_both_campaigns' else 'Mixed',rule[0].upper(),key,degree,pm(f),prob(f['p_fit'])])
    table('pooled_fits','All retrospective all-size pooled fits. Fixed uses fixed-mask estimators in both batches; Mixed uses orbit averaging for the later batch. Neither changes a primary analysis.',['Method','Rule','Quantity','Degree','Intercept','$p_{\\rm fit}$'],rows,True)
    rows=[]
    for rule,obs in read('retro_reconstruction')['derived_fits'].items():
        for key,ds in obs.items():
            for degree,f in enumerate(ds.values(),1):rows.append([rule[0].upper(),esc(key),degree,pm(f),prob(f['p_fit'])])
    table('retro_fits','All retrospective reconstructed full-face and difference statistics. They reuse the original retroreflecting environments.',['Rule','Quantity','Degree','Intercept','$p_{\\rm fit}$'],rows,True)
    rows=[]
    for rule,obs in read('spectrum')['fits'].items():
        for key,ds in obs.items():
            for degree,f in ds.items():rows.append([rule[0].upper(),key,degree,pm(f),prob(f['p_fit'])])
    table('spectrum_fits','All auxiliary spatial-spectrum fits. Modes share environments and are correlated.',['Rule','Mode','Degree','Intercept','$p_{\\rm fit}$'],rows,True)
if __name__=='__main__':build()
