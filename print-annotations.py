#!/usr/bin/env python2.7
import popplerqt4
import PyQt4
import argparse
import tempfile
import shutil
import bisect
import jinja2
import json
import os
jinja_env=jinja2.Environment(extensions=['jinja2.ext.autoescape'])
          
def save_pdf(pdf_doc,filename):
    c = pdf_doc.pdfConverter()
    c.setOutputFileName(filename)
    c.setPDFOptions(c.WithChanges)
    c.convert()
    
def load_pdf(filename):
    return popplerqt4.Poppler.Document.load(filename)

def quad_to_rect(quad, scalex, scaley):
    left = min( [ q.x() for q in quad.points] )
    right = max( [ q.x() for q in quad.points] )
    top = min( [ q.y() for q in quad.points] )
    bottom = max( [ q.y() for q in quad.points] )
    return PyQt4.QtCore.QRectF(left*scalex,top*scaley,(right-left)*scalex,(bottom-top)*scaley)

def get_hilighted_text(page,annot):
    ret = u'';
    scalex = page.pageSizeF().width()
    scaley = page.pageSizeF().height()
    for quad in annot.highlightQuads():
        rect = quad_to_rect(quad,scalex,scaley)
        ret += unicode(page.text(rect));
    return ret

def get_lines(page):
    last_top,last_bottom=0,0
    lines = []
    for tbox in page.textList():
        top = tbox.boundingBox().top()
        bottom = tbox.boundingBox().bottom()
        if top > last_bottom:
            lines.append(int(top))
        last_bottom, last_top = bottom, top
    return lines

def find_line(top, lines):
    return bisect.bisect_left(lines,top)

def annot_to_line(page, annot, lines):
    top = annot.boundary().top()*page.pageSizeF().height()
    return find_line(top,lines)

    

def hType(annot):
    if annot.highlightType() == popplerqt4.Poppler.HighlightAnnotation.Highlight:
        return "Highlight"
    if annot.highlightType() == popplerqt4.Poppler.HighlightAnnotation.Squiggly:
        return "Squiggly"
    if annot.highlightType() == popplerqt4.Poppler.HighlightAnnotation.Underline:
        return "Underline"
    if annot.highlightType() == popplerqt4.Poppler.HighlightAnnotation.StrikeOut:
        return "StrikeOut"
    
def print_annotations(page):
    lines = get_lines(page)
    for annot in page.annotations():
        if annot.subType() == popplerqt4.Poppler.Annotation.AHighlight:
            print "Hilight:", get_hilighted_text(page,annot)
            print "Hilight Type:", hType(annot)
        print "Line:",annot_to_line(page,annot,lines)
        print "Author:", unicode(annot.author())
        print "Contents:", unicode(annot.contents())

def annot_to_dict(page,lines,annot):
    ret =  {
        'Line':annot_to_line(page,annot,lines),
        'Author':unicode(annot.author()),
        'Contents':unicode(annot.contents()),
        'Type':'Comment'
    }
    if annot.subType() == popplerqt4.Poppler.Annotation.AHighlight:
        ret['HighlightedText'] = get_hilighted_text(page,annot)
        ret['Type'] = hType(annot)
    return ret

def page_to_list(page):
    lines = get_lines(page)
    annots = []
    for annot in page.annotations():
        annots.append(annot_to_dict(page,lines,annot))
    return annots
        
def load_template(tpl):
  base_name = tpl or '.annotations-summary-template.tex'
  search_dirs = [ '.', os.environ['HOME'], os.path.dirname(os.path.realpath(__file__)) ]

  for dirname in search_dirs:
    try:
      fname = os.path.join(dirname,base_name)
      return unicode(file(fname,'r').read(),encoding='utf-8',errors='ignore')
    except:
      pass
  return ''
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple utility for summarizing pdf annotations')
    parser.add_argument('file', help='the files to summarize annotations from')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),help='output file')
    parser.add_argument('--template',help='template to use for output', default=None)
    parser.add_argument('--json', help='output as JSON',action='store_true')
    args = parser.parse_args()
    pdf = load_pdf(args.file)

    #print get_lines(pdf.page(0))
    pages = []
    for pg_index in range(pdf.numPages()):
        page = pdf.page(pg_index)
        pages.append({
            'number':pg_index+1,
            'annots':page_to_list(page)
        })
    
    if args.json:
        output=json.dumps(pages)
    else:
        dtpl = jinja_env.from_string(load_template(args.template))
        output = dtpl.render({'pages':pages})
        
    if args.output:
        args.output.write(output.encode('utf-8'))
    else:
        print output.encode('utf-8')
        
        
    
    


            
        
        
    