"""Rebuild figures from stored estimates and fits; never refit or discard a size."""
import os
os.environ.setdefault('MPLCONFIGDIR',str(__import__('pathlib').Path(__file__).resolve().parents[1]/'.cache/matplotlib'))
import json,pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon,FancyArrowPatch
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'paper/figures'
COL={'standard':'#1f657a','orthogonal':'#b44e31'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'savefig.dpi':180,'pdf.fonttype':42,'svg.hashsalt':'partial-ports-release'})
def read(name):return json.loads((ROOT/'results'/f'{name}.json').read_text(encoding='utf-8-sig'))
def save(fig,name,png=False):
    OUT.mkdir(parents=True,exist_ok=True);fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None,'Creator':'JJIN HANZHE research release'})
    if png:fig.savefig(OUT/f'{name}.png',bbox_inches='tight',metadata={'Software':'JJIN HANZHE research release'})
    plt.close(fig)
def curve(f,x,scaled=False):
    coeff=f.get('coefficients_scaled_x',f.get('coefficients'))
    return np.polynomial.polynomial.polyval(x*(16 if scaled else 1),coeff)
def build():
    c=read('t3c_analysis');b=read('t3b_analysis');o=read('original_final')
    fig,axs=plt.subplots(1,2,figsize=(9.4,3.1))
    for ax,title,retro in zip(axs,['Pure retroreflection','Fully open reference'],[True,False]):
        ax.set(xlim=(-.5,3.8),ylim=(-.3,2.55),title=title);ax.axis('off')
        ax.add_patch(Polygon([[0,0],[2.4,0],[3,0.6],[3,2.1],[.6,2.1],[0,1.5]],closed=True,facecolor='#edf1f1',edgecolor='#616b70'))
        ax.plot([0,2.4,3],[1.5,1.5,2.1],color='#616b70');ax.plot([2.4,2.4],[0,1.5],color='#616b70')
        ax.plot([0,0],[0,1.5],lw=7,color='#1f657a')
        for low,high,open_ in [(0,.375,False),(.375,.75,True),(.75,1.125,False),(1.125,1.5,True)]:
            ax.plot([2.4,2.4],[low,high],lw=7,color='#d08336' if open_ else '#818b90',solid_capstyle='butt')
        ax.text(-.2,.75,'L',ha='right',va='center',color='#1f657a',fontsize=12)
        ax.text(3.08,1.5,'A: counted',fontsize=9,color='#a65717');ax.text(3.08,.3,'W: '+('return' if retro else 'uncounted'),fontsize=9,color='#596268')
        ax.plot([.03,.65,1.25,1.7,2.38],[.65,.8,.4,1.25,1.25],color='#a65717',lw=2)
        ax.plot([.03,.8,1.3,1.9,2.38],[.3,.3,.9,.4,.2],color='#596268',lw=1.5,ls='--')
        if retro:ax.annotate('',xy=(1.9,.4),xytext=(2.38,.2),arrowprops={'arrowstyle':'->','color':'#596268'})
        ax.text(1.2,-.23,r'$C_{\rm retro}=n_{LA}$' if retro else r'$N=n_{LA}+n_{LW}$',ha='center',fontsize=11)
    fig.tight_layout();save(fig,'geometry')
    fig,(ax,ref)=plt.subplots(1,2,figsize=(9.2,3.4),gridspec_kw={'width_ratios':[4,1]})
    xx=np.linspace(0,1.06,300);zz=1.202056903159594
    ax.plot(xx,5/6-7*zz/(8*np.pi**3)*xx,color='#263238',label='Continuum closed expression')
    for power,marker,off,color in [('1','o',-.012,'#1f657a'),('2','s',.012,'#b44e31')]:
        ax.errorbar(np.array([1,.5,.25])+off,[c['joint'][f'r{m}'][power]['intercept'] for m in [1,2,4]],yerr=[c['joint'][f'r{m}'][power]['se'] for m in [1,2,4]],fmt=marker,color=color,capsize=3,label='Linear' if power=='1' else 'Quadratic')
    ax.axhline(5/6,color='#84939b',ls=':');ax.set(xlabel=r'$1/m$',ylabel=r'$v=\kappa_2/\kappa_1$',ylim=(.790,.837));ax.legend(fontsize=8,loc='lower left')
    ref.axhline(2/3,color='#63737d',ls='--');ref.axhline(5/6,color='#84939b',ls=':');ref.set(ylim=(.65,.85),xticks=[],yticks=[2/3,5/6],yticklabels=['2/3','5/6'],title='References');ref.yaxis.tick_right()
    fig.tight_layout();save(fig,'stripe_law',True)
    fig,axs=plt.subplots(1,3,figsize=(10.8,3.1))
    for ax,m in zip(axs,[1,2,4]):
        k=f'r{m}'
        for r in COL:
            pts=[p for p in c['point_rows'] if p['rule']==r];x=[1/p['L'] for p in pts]
            ax.errorbar(x,[p['estimate'][k] for p in pts],yerr=[p['se'][k] for p in pts],fmt='o' if r=='standard' else 's',color=COL[r],capsize=2,label=r)
            xx=np.linspace(0,max(x),150)
            for power,style in [('1','-'),('2','--')]:ax.plot(xx,curve(c['separate'][r][k][power],xx,True),style,color=COL[r],lw=1.1)
        ax.axhline(c['targets'][k],color='#555',ls=':',label='target');ax.set(xlabel=r'$1/L$',title=f'{m} stripe'+('s' if m>1 else ''),ylabel=r'$v_m$')
    axs[0].legend(fontsize=7);fig.tight_layout();save(fig,'finite_size')
    fig,axs=plt.subplots(1,4,figsize=(11,3))
    for ax,name in zip(axs,['H1_cube_r2','H3_gap','H4_retro','contrast']):
        if name=='contrast':
            fs=b['joint_delta'];vals=[fs[p] for p in ['1','2']];ax.errorbar([0,1],[v['intercept'] for v in vals],yerr=[v['se'] for v in vals],fmt='o',capsize=3,color='#1f657a');ax.axhline(b['targets']['delta41'],color='#555',ls=':');ax.axhline(0,color='#999',lw=.7);ax.set(xticks=[0,1],xticklabels=['Linear','Quadratic'],title='Layout difference')
        else:
            x=next(q for q in o['endpoints'] if q['name']==name)
            for r,off in [('standard',-.08),('orthogonal',.08)]:
                vals=list(x['fits'][r].values());ax.errorbar(np.array([0,1])+off,[v['intercept'] for v in vals],yerr=[v['se'] for v in vals],fmt='o' if r=='standard' else 's',capsize=2,color=COL[r])
            ax.axhline(x['target'],color='#555',ls=':')
            if name=='H3_gap':ax.axhspan(x['target']-.00187195956248,x['target']+.00187195956248,color='#aaa',alpha=.2)
            if name=='H4_retro':ax.axhline(c['targets']['r2'],color='#ad7336',ls='--')
            ax.set(xticks=[0,1],xticklabels=['Linear','Quadratic'],title={'H1_cube_r2':'Full face','H3_gap':'Gapped covariance','H4_retro':'Retroreflection'}[name])
    fig.tight_layout();save(fig,'other_checks')
    second=read('original_second_points');final=read('original_final_points')
    geom={'cube':'Cube','rect':'Wide slab','gap':'Gap, wall A','wall2':'Gap, wall B','neck':'Constriction'}
    for key,label in [('r2',r'$\kappa_2/\kappa_1$'),('r3',r'$\kappa_3/\kappa_1$'),('r4',r'$\kappa_4/\kappa_1$')]:
        fig,axs=plt.subplots(2,3,figsize=(10.5,5.8))
        for ax,(g,title) in zip(axs.flat,geom.items()):
            test=next(q for q in o['endpoints'] if q['geom']==g and q['key']==key)
            for rule in COL:
                pts=[p for p in (second if key=='r2' else final) if p['geom']==g and p['rule']==rule]
                x=np.array([1/p['L'] for p in pts]);ax.errorbar(x,[p['estimate'][key] for p in pts],yerr=[p['se'][key] for p in pts],fmt='o' if rule=='standard' else 's',color=COL[rule],capsize=2,ms=3)
                xx=np.linspace(0,max(x),100)
                for power,f in enumerate(test['fits'][rule].values()):ax.plot(xx,curve(f,xx),'-' if power==0 else '--',color=COL[rule],lw=1)
            ax.axhline(test['target'],color='#555',ls=':');ax.set(xlabel=r'$1/L$',ylabel=label,title=title)
        axs.flat[-1].axis('off');axs.flat[-1].text(.05,.6,'Teal: standard; rust: orthogonal\nSolid: linear; dashed: quadratic\nDotted: prescribed target\nAll retained sizes',transform=axs.flat[-1].transAxes)
        fig.tight_layout();save(fig,f'original_{key}')
    for g,title in [('gap','Wall A'),('wall2','Wall B')]:
        fig,axs=plt.subplots(2,3,figsize=(10.5,5.8))
        for ax,key in zip(axs.flat,['idA','idB','idC','equal12_13','equal12_23','equal13_23']):
            test=next(q for q in o['endpoints'] if q['geom']==g and q['key']==key)
            for r in COL:
                pts=[p for p in second if p['geom']==g and p['rule']==r];x=np.array([1/p['L'] for p in pts])
                ax.errorbar(x,[p['estimate'][key] for p in pts],yerr=[p['se'][key] for p in pts],fmt='o' if r=='standard' else 's',color=COL[r],capsize=2,ms=3);xx=np.linspace(0,max(x),100)
                for power,f in enumerate(test['fits'][r].values()):ax.plot(xx,curve(f,xx),'-' if power==0 else '--',color=COL[r],lw=1)
            ax.axhline(0,color='#555',ls=':');ax.set(xlabel=r'$1/L$',ylabel='Normalized residual',title=key.replace('id','d').replace('equal','e'))
        fig.suptitle(title+' covariance identities');fig.tight_layout();save(fig,'identities_'+g)
    s=read('spectrum');fig,axs=plt.subplots(1,4,figsize=(11,3))
    for idx,(ax,n,target) in enumerate(zip(axs,s['modes'],s['targets'])):
        for r in COL:
            pts=[p for p in s['rows'] if p['rule']==r];ax.errorbar([1/p['L'] for p in pts],[p['estimate'][idx] for p in pts],yerr=[p['se'][idx] for p in pts],fmt='o' if r=='standard' else 's',color=COL[r],capsize=2,ms=3)
            xx=np.linspace(0,1/32,100)
            for degree,f in s['fits'][r][str(n)].items():ax.plot(xx,curve(f,xx,True),'-' if degree=='1' else '--',color=COL[r],lw=1)
        ax.axhline(target,color='#555',ls=':');ax.set(xlabel=r'$1/L$',title=f'Mode {n}',ylabel=r'$S_n$')
    fig.tight_layout();save(fig,'spectrum')
    e=read('exploratory');h=read('higher');fit=next(v for v in e['cohort_fits'] if v['cohort']=='pooled_old_diagnostics' and v['rule']=='joint' and v['observable']=='h_half')
    fig,ax=plt.subplots(figsize=(7,3.1))
    for i,(label,fs) in enumerate([('Fresh half-open',[h['fits']['joint']['h1'][k] for k in ['1','2']]),('Diagnostic',[fit['linear'],fit['quadratic']])]):
        for j,v in enumerate(fs):ax.errorbar(i+(-.09 if j==0 else .09),v['intercept'],yerr=v['se'],fmt='o' if j==0 else 's',color=['#1f657a','#b44e31'][j],capsize=4,label=['Linear','Quadratic'][j] if i==0 else None)
    target=next(x['target'] for x in e['legacy_sixth_fits'] if x['observable']=='h1');ax.axhline(target,color='#555',ls=':',label='Saddle target')
    ax.set(xticks=[0,1],xticklabels=['Fresh half-open (L = 32–256)','Diagnostic (L = 16–256)'],ylabel=r'$\kappa_3/\kappa_1$',xlim=(-.45,1.45),title='Auxiliary third cumulant: independent batches')
    ax.legend(fontsize=8);fig.tight_layout();save(fig,'third_batches')
if __name__=='__main__':build()
