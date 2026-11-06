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
EQUATIONS=[]  # Populated by the current report entry point.


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



if __name__=='__main__':
 from build_trace_intro_report import main
 main()
