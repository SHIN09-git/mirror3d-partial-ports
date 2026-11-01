"""Compile both PDFs using a local LaTeX installation; no research computation."""
import argparse,os,pathlib,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tex-bin',type=pathlib.Path,help='Optional directory containing pdflatex and bibtex');args=ap.parse_args()
    env=os.environ.copy()
    if args.tex_bin:env['PATH']=str(args.tex_bin)+os.pathsep+env['PATH']
    env['SOURCE_DATE_EPOCH']='1793491200'
    with tempfile.TemporaryDirectory(prefix='partial_ports_paper_') as tmp:
        work=pathlib.Path(tmp)
        for p in (ROOT/'paper').iterdir():
            if p.is_dir():shutil.copytree(p,work/p.name)
            elif p.suffix in ['.tex','.bib']:shutil.copy2(p,work/p.name)
        for source,target in [('main','paper'),('sm','sm')]:
            sequence=[['pdflatex','-interaction=nonstopmode','-halt-on-error',source+'.tex'],['bibtex',source],['pdflatex','-interaction=nonstopmode','-halt-on-error',source+'.tex'],['pdflatex','-interaction=nonstopmode','-halt-on-error',source+'.tex']]
            for cmd in sequence:subprocess.run(cmd,cwd=work,env=env,check=True)
            log=(work/(source+'.log')).read_text(encoding='utf-8',errors='replace')
            assert 'There were undefined references' not in log
            shutil.copy2(work/(source+'.pdf'),ROOT/'paper'/(target+'.pdf'))
if __name__=='__main__':main()
