"""Build the concise TRACE technical report using the supplied Word skill.

Run with a Python containing python-docx, lxml, NumPy and Matplotlib; Pandoc
converts the LaTeX formula source to native editable Word equations.
"""
from copy import deepcopy
import csv
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from space_debris_detection.plotting import publication_style,plt
import numpy as np
from matplotlib.patches import Arc,Circle,Rectangle
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm,Pt,RGBColor
from lxml import etree

REPORT=ROOT/'docs/reports/poblacion-validacion-trace'
ASSETS=REPORT/'assets'
TEMPLATE=ROOT/'.agents/skills/documentos-tecnicos-word/assets/articulo-referencia.docx'
EQUATIONS=[
 ('density',r'p(h\mid g)=\frac{4\pi(R_\oplus+h)^2 n_g(h)}{\int_{200}^{2000}4\pi(R_\oplus+\xi)^2 n_g(\xi)\,\mathrm d\xi}', '1.1'),
 ('sizecdf',r'F_{d\mid g}(x)=\frac{N(>d_{g,\min})-N(>x)}{N(>d_{g,\min})-N(>d_{g,\max})}', '1.2'),
 ('apsides',r'a=R_\oplus+h,\qquad h_p=a(1-e)-R_\oplus,\qquad h_a=a(1+e)-R_\oplus', '2.1'),
 ('bound',r'0\leq e\leq e_{\max}=\frac{\min(h-200,\,2000-h)}{a},\qquad M\sim\mathcal U(0,2\pi)', '2.2'),
 ('focal',r'f=\frac{W_{\mathrm{corto}}}{2\tan(\Theta/2)},\qquad\delta=\frac{p_{\mathrm{px}}}{f},\qquad\boldsymbol\rho=\mathbf r_d-\mathbf r_o', '3.1'),
 ('velocity',r'v_\perp=\left\|\mathbf v_{\mathrm{rel}}-(\mathbf v_{\mathrm{rel}}\cdot\hat{\boldsymbol{\rho}})\hat{\boldsymbol{\rho}}\right\|,\qquad\mathbf v_{\mathrm{rel}}=\mathbf v_d-\mathbf v_o', '3.2'),
 ('overlap',r't_s=\max\!\left(0,\,\min\!\left(t_{\mathrm{out}},t_c+\frac{t_e}{2}\right)-\max\!\left(t_{\mathrm{in}},t_c-\frac{t_e}{2}\right)\right)', '3.3'),
 ('photons',r'F_{\gamma,\odot}=\int_{\lambda_1}^{\lambda_2}E_{\odot,\lambda}\frac{\lambda}{h_{\mathrm P}c}\,\mathrm d\lambda,\qquad F_\gamma=F_{\gamma,\odot}\,p\left(\frac{d}{2r}\right)^2\Phi(\alpha)', '4.1'),
 ('phase',r'\Phi(\alpha)=\frac{\sin\alpha+(\pi-\alpha)\cos\alpha}{\pi},\qquad 0\leq\alpha\leq\pi', '4.2'),
 ('signal',r'A_{\mathrm{ef}}=\frac{\pi D^2}{4}\,T\,QE,\qquad N_{\mathrm{obj}}=F_\gamma A_{\mathrm{ef}}t_s,\qquad S=f_{\mathrm{ext}}N_{\mathrm{obj}}', '4.3'),
 ('pixels',r'L_{\mathrm{px}}=\frac{\omega_{\mathrm{cam}}t_s}{\delta},\qquad\sigma_{\mathrm{px}}=\frac{\mathrm{FWHM}_{\mathrm{px}}}{2\sqrt{2\ln2}}', '4.4'),
 ('npixels',r'n_{\mathrm{px}}=\mathrm{ceil}(\min(L_{\mathrm{px}}+6\sigma_{\mathrm{px}},N_{\mathrm{campo}}))\,\mathrm{ceil}(6\sigma_{\mathrm{px}})', '4.5'),
 ('snr',r'\mathrm{SNR}=\frac{S}{\sqrt{S+n_{\mathrm{px}}\left((B_{\mathrm{px}}+I_{\mathrm{dark}})t_e+\sigma_{\mathrm{read}}^2\right)}}', '4.6'),
 ('saturation',r'Q_{\mathrm{pico}}=N_{\mathrm{obj}}f_{\mathrm{pico}}+(B_{\mathrm{px}}+I_{\mathrm{dark}})t_e<15000\ \mathrm{e^-\,px^{-1}}', '4.7'),
 ('point',r'\frac{d}{r}\leq\mathrm{FWHM}_{\mathrm{px}}\,\delta=1.13165\times10^{-4}\ \mathrm{rad}\;(23.34\ \mathrm{arcsec})', '4.8'),
 ('magnitude',r'm_{\mathrm{AB}}=-2.5\log_{10}\!\left(\frac{F_\gamma}{F_{\gamma,0}}\right),\qquad F_{\nu,0}=3631\ \mathrm{Jy}', '5.1'),
 ('threshold',r'S_5=\frac{25+\sqrt{625+100V}}{2},\qquad m_5=-2.5\log_{10}\!\left(\frac{S_5}{S_0}\right)', '5.2'),
 ('j2',r'\dot\Omega=-\frac{3}{2}J_2\sqrt{\frac{\mu}{a^3}}\left(\frac{R_{J2}}{a}\right)^2\cos i\simeq\frac{2\pi}{365.2422\times86400}', '6.1'),
 ('margin',r'\Delta m=m_{\mathrm{AB}}-m_5,\qquad\Delta m\leq0\ \Longleftrightarrow\ \mathrm{SNR}\geq5', '6.2'),
]


def load_csv(path):
 with path.open() as f:return list(csv.DictReader(f))


def create_figures(population):
 publication_style()
 plt.rcParams.update({'font.size':9,'axes.labelsize':9,'axes.titlesize':10,'legend.fontsize':8})
 diameter=np.array([float(r['diameter_m'])*100 for r in population])
 altitude=np.array([float(r['altitude_km']) for r in population])
 fig,axes=plt.subplots(1,2,figsize=(6.3,2.55),layout='constrained')
 axes[0].hist(altitude,bins=np.arange(200,2001,50),color='#0072B2',edgecolor='black',lw=.3)
 axes[1].hist(diameter,bins=np.geomspace(1,np.nextafter(diameter.max(),np.inf),41),color='#0072B2',edgecolor='black',lw=.3)
 axes[0].set(xlabel='Altitud media orbital [km]',ylabel='Objetos por intervalo de 50 km',xlim=(200,2000))
 axes[1].set(xscale='log',xlabel='Diámetro equivalente [cm]',ylabel='Objetos por intervalo logarítmico')
 for ax in axes:ax.grid(axis='y',alpha=.25,lw=.4);ax.set_axisbelow(True)
 fig.savefig(ASSETS/'poblacion.png',dpi=300,bbox_inches='tight');plt.close(fig)
 # Phase and partial-exposure schematic, built from explicit geometric coordinates.
 fig,axes=plt.subplots(1,2,figsize=(6.3,2.5),layout='constrained')
 ax=axes[0];target=np.array([0.,0.]);observer=np.array([2.2,1.]);sun=np.array([0.,2.1])
 ax.add_patch(Circle(target,.075,color='black'));ax.add_patch(Circle(sun,.16,color='#EDCB35'))
 ax.add_patch(Rectangle(observer-[.14,.11],.28,.22,facecolor='#969696',edgecolor='black'))
 for end in (sun-[0,.17],observer-[.14,.06]):
  ax.annotate('',xy=end,xytext=target,arrowprops={'arrowstyle':'->','color':'#E68619','lw':1.6})
 angle=np.degrees(np.arctan2(observer[1],observer[0]));ax.add_patch(Arc(target,1.05,1.05,theta1=angle,theta2=90,color='#60A34C',lw=1.7))
 ax.text(.27,.48,r'$\alpha$',color='#478438',fontsize=12)
 ax.text(-.03,2.35,'Sol',ha='center');ax.text(2.2,1.3,'Observador',ha='center');ax.text(0.,-.28,'Objeto',ha='center')
 ax.text(.12,1.22,r'$\hat{\mathbf{s}}$',color='#E68619');ax.text(1.15,.23,r'$-\hat{\boldsymbol{\rho}}$',color='#E68619')
 ax.set(xlim=(-.35,2.75),ylim=(-.42,2.58),aspect='equal');ax.axis('off')
 ax=axes[1]
 ax.hlines([2,1],[-5,-5],[115,115],color='#999999',lw=.6)
 ax.plot([0,77],[2,2],lw=8,color='#969696',solid_capstyle='butt')
 ax.plot([25,110],[1,1],lw=8,color='#E68619',solid_capstyle='butt')
 ax.plot([25,77],[.2,.2],lw=8,color='#60A34C',solid_capstyle='butt')
 for value in (0,25,77,110):ax.axvline(value,color='#AAAAAA',ls='--',lw=.5)
 ax.text(38.5,2.27,'Exposición: 77 ms',ha='center',fontsize=8)
 ax.text(67.5,1.27,'Objeto dentro del FoV',ha='center',fontsize=8)
 ax.text(51,.46,r'Señal: $t_s=52$ ms',ha='center',fontsize=8)
 ax.set(xlim=(-7,116),ylim=(-.15,2.65),yticks=[],xticks=[0,25,77,110],xlabel='Tiempo [ms]')
 for spine in ('left','right','top'):ax.spines[spine].set_visible(False)
 fig.savefig(ASSETS/'geometria_transito.png',dpi=300,bbox_inches='tight')
 fig.savefig(ASSETS/'geometria_transito.svg',bbox_inches='tight');plt.close(fig)
 svg=ASSETS/'geometria_transito.svg'
 svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
 # Compact report editions reuse archived exact instrument/population results.
 ranges=[r for r in json.loads((ROOT/'data/generated/optical/range_vs_size_nominal.json').read_text()) if r['diameter_m']<=1.0]
 fig,ax=plt.subplots(figsize=(6.3,2.8),layout='constrained')
 ds=np.array([r['diameter_m']*100 for r in ranges]);lo=np.array([r['intervals'][0]['lower_m']/1000 for r in ranges]);hi=np.array([r['intervals'][-1]['upper_m']/1000 for r in ranges])
 ax.fill_between(ds,lo,hi,color='#C9DDEB',alpha=.65,label='Ventana elegible')
 ax.loglog(ds,hi,color='#0072B2',label='Máximo');ax.loglog(ds,lo,color='#D55E00',label='Mínimo')
 ax.set(xlabel='Diámetro equivalente [cm]',ylabel='Distancia al instrumento [km]',xlim=(1,100))
 ax.grid(which='both',lw=.35,alpha=.3);ax.legend(loc='upper left',ncol=3,fontsize=8)
 fig.savefig(ASSETS/'ventana_optica.png',dpi=300,bbox_inches='tight');plt.close(fig)
 encounters=load_csv(ROOT/'data/generated/encounters/sso450km_24h_encounters.csv')
 valid=[r for r in encounters if r['valid']=='True'];fig,ax=plt.subplots(figsize=(6.3,2.8),layout='constrained')
 for group,color in [('1_to_5cm','#0072B2'),('5_to_10cm','#009E73'),('10cm_up','#B57EDC')]:
  for marker in ('o','x','^'):
   records=[r for r in valid if r['size_group']==group and r['marker']==marker]
   ax.scatter([float(r['range_km']) for r in records],[float(r['magnitude_margin']) for r in records],s=4,c=color,marker=marker,alpha=.5,linewidths=.3)
 ax.axhline(0,color='red',ls='--',lw=1);ax.axhspan(0,14,color='red',alpha=.09)
 ax.set(xscale='log',ylim=(-10,14),xlabel='Distancia observador–objeto [km]',ylabel=r'$m_{\mathrm{AB}}-m_5$ [mag]')
 ax.grid(which='both',lw=.35,alpha=.25)
 from matplotlib.lines import Line2D
 ax.legend(handles=[Line2D([0],[0],marker='o',ls='none',color=c,label=l,ms=4) for c,l in
  [('#0072B2','1–5 cm'),('#009E73','5–10 cm'),('#B57EDC','≥10 cm')]],loc='lower left',ncol=3,fontsize=8)
 fig.savefig(ASSETS/'cruces_24h.png',dpi=300,bbox_inches='tight');plt.close(fig)


def math_objects():
 source='\n\n'.join('$$\n'+latex+'\n$$' for key,latex,number in EQUATIONS)+'\n'
 (REPORT/'ecuaciones.md').write_text(source)
 target=Path('/tmp/trace-report-equations.docx')
 subprocess.run(['pandoc',str(REPORT/'ecuaciones.md'),'-o',str(target),'--reference-doc',str(TEMPLATE)],check=True)
 with ZipFile(target) as z:xml=etree.fromstring(z.read('word/document.xml'))
 math=xml.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMathPara')
 assert len(math)==len(EQUATIONS),(len(math),len(EQUATIONS))
 for expression in math:
  for parent in expression.iter():
   j=1
   while j<len(parent):
    left,right=parent[j-1],parent[j]
    def roman_word(node):
     style=node.find('./'+qn('m:rPr')+'/'+qn('m:sty'))
     text=node.find(qn('m:t'))
     return (node.tag==qn('m:r') and style is not None and style.get(qn('m:val'))=='p'
             and text is not None and text.text and text.text.isalpha())
    if roman_word(left) and roman_word(right):
     left.find(qn('m:t')).text+=right.find(qn('m:t')).text;parent.remove(right)
    else:j+=1
 return {key:(deepcopy(obj),number) for (key,latex,number),obj in zip(EQUATIONS,math)}


class Writer:
 def __init__(self,math):
  self.doc=Document(TEMPLATE);self.math=math;self.bookmarks=100
  self.doc.core_properties.title='TRACE — Población sintética y validación óptica y radiométrica'
  self.doc.core_properties.subject='Metodología, hipótesis y resultados preliminares'
  self.doc.core_properties.author='';self.doc.core_properties.language='es-ES'
  for style in self.doc.styles:
   if style.type in (1,2):
    style.font.name='Times New Roman'
    for fonts in style.element.findall('.//'+qn('w:rFonts')):
     for attr in ('asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme'):
      fonts.attrib.pop(qn('w:'+attr),None)
  self.doc.styles['Subtitle'].font.name='Times New Roman'
  self.doc.styles['Subtitle'].font.size=Pt(15)
  normal=self.doc.styles['Normal'];normal.paragraph_format.space_after=Pt(4)
  normal.paragraph_format.line_spacing=1.05
  for style in ('Heading 1','Heading 2'):
   self.doc.styles[style].paragraph_format.space_before=Pt(10)
   self.doc.styles[style].paragraph_format.space_after=Pt(5)
  self.doc.settings.odd_and_even_pages_header_footer=False
  for section in self.doc.sections:section.different_first_page_header_footer=False
  language=OxmlElement('w:lang');language.set(qn('w:val'),'es-ES')
  self.doc.styles['Normal'].element.get_or_add_rPr().append(language)
 def p(self,text='',bold=False,size=None):
  p=self.doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
  tokens=('t_FoV','W_corto','n_g','t_c','t_out','t_in','t_s','t_e','f_ext','f_pico','F_γ','F_ν','h_P','B_px','I_dark','σ_read','ω_cam','L_px','N_campo','n_px','σ_px','S_0','m_AB')
  for part in re.split('('+'|'.join(map(re.escape,tokens))+')',text):
   if part in tokens:
    base,sub=part.split('_',1)
    run=p.add_run(base);run.italic=True;run.bold=bold
    if size:run.font.size=Pt(size)
    run=p.add_run(sub);run.font.subscript=True;run.bold=bold
    if size:run.font.size=Pt(size)
   else:
    run=p.add_run(part);run.bold=bold
    if size:run.font.size=Pt(size)
  return p
 def heading(self,text,page=False):
  p=self.doc.add_paragraph(text,'Heading 1');p.paragraph_format.page_break_before=page
  return p
 def sub(self,text):return self.doc.add_paragraph(text,'Heading 2')
 def equation(self,key):
  math,number=self.math[key];table=self.doc.add_table(rows=1,cols=2);table.autofit=False
  table.columns[0].width=Cm(14.05);table.columns[1].width=Cm(1.35)
  for i,cell in enumerate(table.rows[0].cells):
   cell.width=Cm(14.05 if i==0 else 1.35)
   p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
   if i==0:
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p._p.append(deepcopy(math))
    for run in p._p.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}r'):
     props=OxmlElement('w:rPr');fonts=OxmlElement('w:rFonts');fonts.set(qn('w:ascii'),'Cambria Math');fonts.set(qn('w:hAnsi'),'Cambria Math');props.append(fonts)
     size=OxmlElement('w:sz');size.set(qn('w:val'),'20');props.append(size)
     run.insert(1 if len(run) and run[0].tag==qn('m:rPr') else 0,props)
   else:
    p.alignment=WD_ALIGN_PARAGRAPH.RIGHT;r=p.add_run('('+number+')');r.font.size=Pt(10)
   cell.vertical_alignment=1
  # Equations must not split across pages; rows have no visible borders.
  props=table._tbl.tblPr;border=OxmlElement('w:tblBorders')
  for side in ('top','left','bottom','right','insideH','insideV'):
   node=OxmlElement('w:'+side);node.set(qn('w:val'),'nil');border.append(node)
  props.append(border);table.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
 def caption(self,kind,section,number,text,bookmark=None,above=False):
  p=self.doc.add_paragraph(style='Caption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(5);p.paragraph_format.keep_with_next=above
  p.add_run(kind+' ')
  if bookmark:
   begin=OxmlElement('w:bookmarkStart');begin.set(qn('w:id'),str(self.bookmarks));begin.set(qn('w:name'),bookmark);p._p.append(begin)
  p.add_run(str(section)+'.')
  field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),f'SEQ {kind}_{section} \\* ARABIC')
  r=OxmlElement('w:r');t=OxmlElement('w:t');t.text=str(number);r.append(t);field.append(r);p._p.append(field)
  if bookmark:
   end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(self.bookmarks));p._p.append(end);self.bookmarks+=1
  p.add_run('. '+text)
  return p
 def table(self,headers,rows,widths,param=False):
  table=self.doc.add_table(rows=1,cols=len(headers));table.autofit=False
  for col,width in zip(table.columns,widths):col.width=Cm(width)
  for cell,text,width in zip(table.rows[0].cells,headers,widths):cell.width=Cm(width);cell.text=text
  for values in rows:
   cells=table.add_row().cells
   for cell,text,width in zip(cells,values,widths):cell.width=Cm(width);cell.text=str(text)
  table.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
  for ri,row in enumerate(table.rows):
   row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
   for ci,cell in enumerate(row.cells):
    if ri==0 or (param and ci==0):
     shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'9CC4EE' if ri==0 else 'E6F0F9');cell._tc.get_or_add_tcPr().append(shade)
    for p in cell.paragraphs:
     p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
     for r in p.runs:r.font.size=Pt(9);r.bold=ri==0 or (param and ci==0)
  border=OxmlElement('w:tblBorders')
  for side in ('top','left','bottom','right','insideH','insideV'):
   line=OxmlElement('w:'+side);line.set(qn('w:val'),'single');line.set(qn('w:sz'),'3');line.set(qn('w:color'),'AAAAAA');border.append(line)
  table._tbl.tblPr.append(border)
  return table
 def figure(self,name,width=15.2):
  p=self.doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(0)
  p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(ASSETS/name),width=Cm(width))
 def ref(self,before,bookmark,number,after):
  p=self.p(before);field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'REF '+bookmark+' \\h')
  r=OxmlElement('w:r');t=OxmlElement('w:t');t.text=number;r.append(t);field.append(r);p._p.append(field);p.add_run(after)


def main():
 REPORT.mkdir(parents=True,exist_ok=True);ASSETS.mkdir(exist_ok=True)
 pop=load_csv(ROOT/'data/generated/trace_population_50000.csv')
 meta=json.loads((ROOT/'data/generated/trace_population_metadata.json').read_text())
 optical=json.loads((ROOT/'data/generated/optical/manifest.json').read_text())
 day=json.loads((ROOT/'data/generated/encounters/sso450km_24h_photometry.json').read_text())
 validation=json.loads((ROOT/'data/generated/encounters/sso450km_24h_validation.json').read_text())
 assert len(pop)==50000 and hashlib.sha256((ROOT/'data/generated/trace_population_50000.csv').read_bytes()).hexdigest()==day['propagation']['population_sha256']
 create_figures(pop);w=Writer(math_objects())
 # Page 1: scope and statistical population.
 title=w.doc.add_paragraph('TRACE','Title');title.alignment=WD_ALIGN_PARAGRAPH.CENTER
 p=w.doc.add_paragraph('Población sintética y validación\nóptica y radiométrica','Subtitle');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 p=w.doc.add_paragraph('Informe técnico breve · 6 de noviembre de 2026');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 w.p('Resumen',bold=True)
 w.p('Se describe la construcción reproducible de una población nominal de 50.000 objetos LEO y el modelo empleado para estimar su detectabilidad óptica desde TRACE. Se combinan estadísticas aproximadas de ESA y parámetros orbitales de tres familias de fragmentación de CelesTrak. El presupuesto radiométrico incluye fase, traza, ruido, saturación y tránsitos parciales. Se presentan ventanas instrumentales y una simulación de cruces de 24 horas. Los resultados verifican la consistencia del modelo bajo sus hipótesis; no demuestran por sí solos la viabilidad operacional de la misión.')
 w.heading('1. Propósito y población de partida')
 w.p('TRACE —Tracking and Reacquisition Architecture for Cooperative Estimation of Uncorrelated Space Objects— estudia la detección de basura espacial mediante un instrumento fijo al satélite. La población comprende órbitas residentes entre 200 y 2.000 km y diámetros d ≥ 1 cm. Se conserva un nominal inmutable para separar cambios del instrumento y sensibilidad orbital. El estudio usa modelos físicos y muestreo reproducible en Python, sin IA.')
 w.p('Las curvas de tamaños y densidad se digitalizaron de las Figuras 2.8–2.9 de ESA 2026 [1], con calibración logarítmica y trazabilidad de los vértices del PDF. Los perfiles de objetos no maniobrables se usan como aproximación al entorno de debris. Para g=1–10 cm se resta la densidad >10 cm de la >1 cm; el otro grupo es ≥10 cm. La altitud se muestrea ponderando por volumen de capa:')
 w.equation('density')
 w.p('Aquí h es la altitud media orbital en km, R⊕=6.371 km y n_g la densidad espacial del grupo. Dentro de cada grupo se invierte la distribución acumulativa de tamaño N(>d), con interpolación logarítmica y monotonía corregida:')
 w.equation('sizecdf')
 w.p('Se supone independencia entre tamaño y altitud dentro de cada uno de los dos grupos; no se reconstruye una distribución conjunta completa de ESA. La semilla 20260201 genera 47.400 objetos de 1–10 cm y 2.600 mayores. El corte de la curva es 38,29 m; el mayor diámetro realizado es 12,36 m.')
 # Page 2: orbital construction and limitations.
 w.heading('2. Asignación de los elementos orbitales',page=True)
 w.p('Los GP de FENGYUN 1C, COSMOS 2251 e IRIDIUM 33 se cruzan con SATCAT [2]. Se conservan 2.567 donantes DEB/RB no operativos ni decaídos, con GP a menos de siete días de la época común. Se propagan con SGP4 a 2026-11-05T00:00:00Z en TEME; de sus estados se obtienen elementos instantáneos de dos cuerpos. No se tratan los elementos medios GP originales como osculantes sincronizados.')
 w.equation('apsides')
 w.p('Para cada altitud se selecciona conjuntamente la terna (e, Ω, ω) de un donante compatible: se preserva la asociación entre excentricidad, RAAN y argumento del perigeo. Se exige perigeo h_p ≥200 km y apogeo h_a ≤2.000 km. Se priorizan donantes a ±100 km de altitud media; si faltan, se usan hasta los 50 compatibles más próximos.')
 w.equation('bound')
 w.p('La inclinación i se muestrea de los conteos aproximados de la Figura 3.3a de ESA, condicionada al perigeo, con celdas de 40 km ×3°. La anomalía media M es uniforme: representa fase temporal uniforme, no anomalía verdadera uniforme en una elipse. Se convierten después los elementos sintéticos a posición y velocidad en la época común. Las semillas orbital y de fase son 20260202 y 20260203.')
 w.figure('poblacion.png')
 w.caption('Figura',2,1,'Distribuciones realizadas de altitud media y diámetro de los 50.000 registros nominales. Son conteos por intervalo, sin pesos.',bookmark='fig_population')
 w.p('Límites de representatividad. El 20,996 % (10.498 objetos) requiere donantes fuera del vecindario de ±100 km; se marca donor_local_support=False y el desajuste máximo de altitud del donante llega a 1.576,51 km. Solo hay tres familias de fragmentación y la inclinación se asigna de manera independiente de la terna donante. Se combinan referencias estadísticas de fechas distintas; no es un censo contemporáneo global. Siete altitudes se ajustan menos de 0,987 km para admitir una excentricidad empírica sin recortarla.',size=10)
 w.p('La integral de densidad representa ≈354.821 objetos y asigna peso 7,096 por muestra. Los resultados de encuentros de este informe cuentan registros sin multiplicar por ese peso. Existen nueve poblaciones de sensibilidad, separadas del nominal: tres de e, y 12/8/4 posiciones equiespaciadas de Ω o ω, cambiando un parámetro cada vez.',size=10)
 # Page 3: baseline, conventions and corrected partial transit.
 w.heading('3. Instrumento, geometría y tránsito parcial',page=True)
 w.caption('Tabla',3,1,'Configuración nominal leída del Excel del detector y óptica [4].',above=True)
 w.table(['Parámetro','Valor nominal','Parámetro','Valor nominal'],[
  ('Apertura D','80 mm','FoV corto Θ','14°'),('Sensor','4500 × 4340 px','Paso de píxel','10 µm'),
  ('Banda','450–750 nm','Exposición','77 ms'),('Transmisión T','0,8','QE','0,9'),
  ('PSF FWHM','2 px','Lectura RMS','5 e⁻/px'),('Dark','0,01 e⁻/px/s','Full well High Gain','15000 e⁻/px'),
  ('Fondo supuesto','22 AB mag/arcsec²','Albedo geométrico p','0,2')],[4.1,3.6,4.1,3.6])
 w.p('El instrumento no sigue al debris. El satélite mantiene el zenit en el marco orbital local (LVLH), por lo que la cámara gira respecto a las estrellas. Con W_corto=43,4 mm, la focal nominal es 176,73 mm y la escala angular es δ=5,6583·10⁻⁵ rad/px. Los subíndices d y o denotan debris y observador.')
 w.equation('focal');w.equation('velocity')
 w.figure('geometria_transito.png')
 w.caption('Figura',3,1,'Fase α medida en el objeto entre las direcciones al Sol y al observador. Ejemplo temporal ilustrativo: el solapamiento de 25 a 77 ms aporta 52 ms de señal.',bookmark='fig_geometry')
 w.p('Se obtiene t_FoV=t_out−t_in de las entradas y salidas del campo rectangular. Para una exposición centrada en t_c, la señal se integra solo durante su intersección con ese tránsito:')
 w.equation('overlap')
 w.p('Un tránsito parcial no se rechaza por durar menos de 77 ms. El fondo y la corriente oscura siguen integrando durante toda t_e; un cruce parcial puede alcanzar SNR ≥5. En los barridos sin encuentro concreto se usa el máximo solapamiento central t_s=min(t_e,t_FoV).',size=10)
 # Page 4: radiometry.
 w.heading('4. Presupuesto de señal y ruido',page=True)
 w.p('La estructura de señal, ruido de Poisson, fondo, dark y lectura se apoya en el modelo del paper [3, §2.1]. TRACE lo adapta a esfera lambertiana, integración espectral, PSF/traza y tránsito parcial; no reproduce íntegramente sus figuras ni adopta su veto a tránsitos cortos. El objeto se considera iluminado salvo cuando la Tierra lo oculta al Sol.')
 w.sub('4.1. Fotones y electrones')
 w.p('Se integra un espectro solar de cuerpo negro a 5772 K, normalizado a 1361 W/m² a 1 UA. F_γ es el flujo recibido en fotones/m²/s, r la distancia, d el diámetro y h_P la constante de Planck:')
 w.equation('photons');w.equation('phase')
 w.ref('La fase α se define como en la Figura ','fig_geometry','3.1','. El área efectiva incluye transmisión y QE; la extracción conserva la fracción erf(3/√2)²≈0,9946 de la señal en el modelo:')
 w.equation('signal')
 w.sub('4.2. Traza, ruido y criterios de validez')
 w.equation('pixels');w.equation('npixels')
 w.p('La tasa angular ω_cam incluye el giro de cámara. La máscara usa margen de 3σ por lado, limitada al ancho corto N_campo. La función ceil redondea al entero superior. B_px es el fondo en e⁻/px/s, obtenido de 22 AB mag/arcsec² y del área angular del píxel; I_dark y σ_read proceden de la Tabla 3.1.',size=10)
 w.equation('snr')
 w.p('La carga pico usa la fracción f_pico de una PSF gaussiana convolucionada con traza uniforme, integrada en el píxel central de peor alineación:')
 w.equation('saturation');w.equation('point')
 w.p('La última desigualdad define el dominio puntual del modelo, no un criterio de Rayleigh. No se usa >140 ke⁻ de Low Gain como capacidad exacta ni se combina con su ruido desconocido. Se omite clipping del ADC; la PSF se mantiene en 2 px al variar la apertura.',size=10)
 # Page 5: magnitudes and range checks.
 w.heading('5. Magnitud aparente y alcance instrumental',page=True)
 w.p('La magnitud aparente AB equivalente expresa el flujo recibido en 450–750 nm. El cero se integra con F_ν constante de 3631 Jy. Una magnitud mayor indica menor brillo. Apertura y ruido no cambian esa magnitud: determinan el SNR con que se registra.')
 w.equation('magnitude')
 w.p('Para cada exposición se define V=n_px[(B_px+I_dark)t_e+σ_read²]. S_0 es la señal de una fuente de magnitud cero con la misma traza y tiempo visible; la señal y magnitud que dan SNR=5 son:')
 w.equation('threshold')
 w.p('No hay una magnitud límite única para todos los movimientos: V y t_s cambian entre cruces. Al fijar magnitud aparente ya se fija el flujo recibido; no se aplica otra pérdida 1/r². Para un objeto de tamaño fijo, esa pérdida sí entra mediante la ecuación (4.1).')
 w.figure('ventana_optica.png')
 w.caption('Figura',5,1,'Ventana óptica condicional nominal para diámetros de 1 a 100 cm. Fase 60°, albedo 0,2, v⊥=5 km/s y observador nominal a 450 km. Límites de SNR, saturación y fuente puntual; no incluyen accesibilidad de encuentros.')
 w.caption('Tabla',5,1,'Cortes exactos del barrido para cuatro diámetros; mismo caso que la Figura 5.1.',above=True)
 cases=load_csv(ROOT/'data/generated/optical/size_comparison_cases.csv');selected=[]
 for r in cases:
  if all(float(r[k])==v for k,v in [('Fase [deg]',60),('Albedo',.2),('FOV [deg]',14),('Apertura [mm]',80),('Velocidad transversal [km/s]',5)]):
   selected.append((r['Diámetro [cm]'],f"{float(r['Alcance óptico mínimo [km]']):.3f}".replace('.',','),f"{float(r['Alcance óptico máximo [km]']):.2f}".replace('.',',')))
 assert len(selected)==4
 w.table(['Diámetro [cm]','Alcance mínimo [km]','Alcance máximo [km]'],selected,[4.,5.7,5.7])
 w.p('Los alcances son distancias instrumento–objeto, no altitudes orbitales. Algunos máximos exceden las distancias disponibles para encuentros LEO; no deben interpretarse como cobertura real. Los barridos varían una entrada cada vez y conservan los intervalos separados cuando aparecen.',size=10)
 # Page 6: one-day result.
 w.heading('6. Aplicación a los cruces de 24 horas',page=True)
 w.p('Se eligió la SSO LTAN 06:00 por el mayor número de IDs detectables en un barrido exploratorio previo. Se fija RAAN inicial 130,1326° y argumento de latitud inicial 0°. La inclinación 97,1877° procede de igualar la precesión secular J2 al movimiento solar medio:')
 w.equation('j2')
 w.p('Se propagan los 50.000 estados y el observador durante 86400 s desde 2026-11-05 00:00 UTC, con RK4 y gravedad central+J2. La altitud de 450 km es la referencia circular osculante inicial: bajo J2 varía entre 442,46 y 450,00 km. El FoV es rectangular y el apuntamiento se mantiene al zenit; se aplican iluminación, ocultación y exclusión solar de 90°.')
 w.p('Entre pasos de 20 s se interpola la trayectoria con cúbicos Hermite. Cotas de Bernstein y raíces de las caras buscan cruces incluso cuando ambos extremos están fuera. Cada cruce aporta el mayor SNR válido encontrado con centros de exposición cada ≤0,25 s y refinamiento local; la sincronización del frame se supone ideal. Se acepta el solapamiento parcial de (3.3).')
 w.equation('margin')
 w.figure('cruces_24h.png')
 w.caption('Figura',6,1,'Cruces válidos de 24 h: rojo, SNR<5; debajo de cero, SNR≥5. Azul 1–5 cm, verde 5–10 cm, lila ≥10 cm; punto, primer cruce; cruz, segundo; triángulo, tercero y posteriores. Los excluidos no se dibujan.',bookmark='fig_day')
 w.caption('Tabla',6,1,'Conteos sin ponderación de la población sintética; no equivalen a tasas operacionales.',above=True)
 w.table(['Concepto','Cruces','Objetos distintos'],[
  ('Cruces geométricos por el FoV','16.578','13.304'),('Dentro del dominio óptico válido','8.312','7.344'),('SNR ≥5 y criterios válidos','271','251')],[7.8,3.8,3.8])
 # Page 7: verification, limitations, traceability.
 w.heading('7. Verificación, límites y conclusiones',page=True)
 w.p('La población supera controles de IDs, finitud, época/marco, límites de ápsides, asociación de donantes y conversión elemento–estado. El error relativo máximo de energía de la conversión nominal es 1,70·10⁻¹⁵. Esta comprobación verifica coherencia computacional, no representatividad global del debris.')
 w.p('En 5.000 objetos, reducir el paso dinámico de 20 a 10 s conserva los mismos 1.708 cruces. La diferencia máxima de entrada es 5,865 ms y la mediana del mayor error de borde por cruce es 0,429 ms; la diferencia máxima de posición del observador es 10,905 m. Reducir el muestreo fotométrico a 0,125 s conserva las clasificaciones de los 16.578 cruces y los 271 casos de SNR≥5. La suite del proyecto contiene 42 pruebas superadas en esta fase.')
 w.sub('7.1. Alcance de la interpretación')
 for text in [
  'Población: tres familias no describen todo LEO; el soporte por altitud es incompleto y el catálogo observable no caracteriza directamente todos los fragmentos de 1 cm.',
  'Óptica: esfera difusa, albedo fijo, PSF gaussiana de 2 px, fondo uniforme y extracción simplificada; no se modelan tumbling, reflejos especulares, luz terrestre ni respuesta fuera de eje.',
  'Geometría y dinámica: sombra cilíndrica y Sol aproximado; se omiten arrastre, armónicos superiores, terceros cuerpos y correcciones precisas de orientación terrestre.',
  'Operación: mejor instante de exposición encontrado, sin cadencia fija ni tiempos muertos. SNR≥5 no fija por sí solo la probabilidad de detección ni la tasa de falsas alarmas.'
 ]:
  p=w.p('• '+text,size=10)
 w.p('La fase proporciona una base reproducible para comparar diseños y geometrías. Antes de concluir viabilidad de misión deben ampliarse los donantes, ensayarse incertidumbres de albedo/PSF/fondo y simularse cadencia, procesamiento y precisión de medidas. Los 251 IDs son un resultado condicionado de esta realización, no una predicción garantizada del entorno real.')
 w.sub('7.2. Fuentes y reproducción')
 references=[
  '[1] ESA, ESA Space Environment Report 2026. Figuras 2.8–2.9 (PDF p. 31) y 3.3a (PDF p. 68). Copia y extracción archivadas en el proyecto.',
  '[2] CelesTrak, GP de FENGYUN 1C, COSMOS 2251 e IRIDIUM 33 y SATCAT aportados por el usuario. Ventana de GP ≤7 días respecto al 05/11/2026; 2.567 donantes retenidos.',
  '[3] D’Anniballe, A.; Felicetti, L.; Hobbs, S. Preliminary analysis and design of an optical space surveillance and tracking constellation for LEO coverage. Acta Astronautica 231 (2025), 47–63. DOI: 10.1016/j.actaastro.2025.02.019.',
  '[4] TRACE_Detector_Optical_Baseline (1).xlsx, archivo del proyecto. High Gain: 15 ke⁻/px; Low Gain: >140 ke⁻/px, solo cota inferior.',
  '[5] Nominal: data/generated/trace_population_50000.csv y metadatos; estudio diario: data/generated/encounters/. Hipótesis completas: Notas del Proyecto.md.'
 ]
 for text in references:w.p(text,size=9)
 w.p('Secuencia reproducible: scripts/reproduce_population.sh; generate_optical_validation.py; propagate_day_encounters.py; plot_day_encounters.py. El presente informe usa la población ya archivada, sin regenerar entradas ni modificar las simulaciones.',size=9)
 # Update dynamic Word fields when opening; footer/header inherited from template.
 update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');w.doc.settings.element.append(update)
 final=REPORT/'TRACE_Informe_Poblacion_Validacion_Optica.docx';w.doc.save(final)
 inputs=[ROOT/'data/generated/trace_population_50000.csv',ROOT/'data/generated/trace_population_metadata.json',
  ROOT/'data/generated/validation.json',ROOT/'data/generated/optical/manifest.json',
  ROOT/'data/generated/optical/range_vs_size_nominal.json',ROOT/'data/generated/optical/size_comparison_cases.csv',
  ROOT/'data/generated/encounters/sso450km_24h_encounters.csv',ROOT/'data/generated/encounters/sso450km_24h_photometry.json',
  ROOT/'data/generated/encounters/sso450km_24h_validation.json',ROOT/'docs/references/ESA_Space_Environment_Report_2026.pdf',
  ROOT/'docs/references/Space debris mission scientific paper.pdf',ROOT/'docs/references/TRACE_Detector_Optical_Baseline (1).xlsx',TEMPLATE]
 provenance={'language':'es-ES','document':final.name,'equations_editable_omml':len(EQUATIONS),
  'template':str(TEMPLATE.relative_to(ROOT)),'inputs':[{'path':str(p.relative_to(ROOT)),
  'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs],
  'figure_source':'redrawn compact report editions from frozen nominal CSV and archived optical/encounter results; geometry illustrative',
  'input_population_sha256':day['propagation']['population_sha256'],
  'scope':'no population or simulation regenerated; report data remain the archived nominal results',
  'runtime':{'python':sys.version.split()[0],'pandoc':subprocess.check_output(['pandoc','--version'],text=True).splitlines()[0]}}
 (REPORT/'fuentes.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n')
 print(final)


if __name__=='__main__':main()
