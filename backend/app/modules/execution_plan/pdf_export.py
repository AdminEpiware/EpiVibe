"""Generate a complete, print-friendly Stage 4 execution plan from saved data.
Requires: reportlab (pip install reportlab).
"""
from io import BytesIO
from html import escape
from pathlib import Path
from decimal import Decimal
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PURPLE=colors.HexColor('#6520AD')
DARK=colors.HexColor('#251339')
LIGHT=colors.HexColor('#F4EFFA')
GRAY=colors.HexColor('#5D5666')


def _fonts():
    locations=[
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('C:/Windows/Fonts/arial.ttf','C:/Windows/Fonts/arialbd.ttf'),
    ]
    for regular,bold in locations:
        if Path(regular).exists() and Path(bold).exists():
            if 'EpiRegular' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('EpiRegular',regular))
                pdfmetrics.registerFont(TTFont('EpiBold',bold))
            return 'EpiRegular','EpiBold'
    return 'Helvetica','Helvetica-Bold'


def build_execution_pdf(plan):
    if not isinstance(plan,dict):
        raise ValueError('Saved execution plan is missing')
    regular,bold=_fonts()
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='EpiTitle',fontName=bold,fontSize=22,leading=29,textColor=DARK,spaceAfter=13))
    styles.add(ParagraphStyle(name='EpiSection',fontName=bold,fontSize=15,leading=20,textColor=PURPLE,spaceBefore=17,spaceAfter=10,keepWithNext=True))
    styles.add(ParagraphStyle(name='EpiSub',fontName=bold,fontSize=10.5,leading=15,textColor=DARK,spaceBefore=10,spaceAfter=6,keepWithNext=True))
    styles.add(ParagraphStyle(name='EpiBody',fontName=regular,fontSize=9,leading=14,textColor=DARK,spaceAfter=7,wordWrap='CJK'))
    styles.add(ParagraphStyle(name='EpiSmall',fontName=regular,fontSize=8,leading=12,textColor=DARK,wordWrap='CJK'))
    styles.add(ParagraphStyle(name='EpiHeader',fontName=bold,fontSize=8,leading=12,textColor=colors.white))
    styles.add(ParagraphStyle(name='EpiMuted',fontName=regular,fontSize=8,leading=12,textColor=GRAY))
    buff=BytesIO()
    doc=SimpleDocTemplate(buff,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=53,bottomMargin=50,title='EpiVibe Complete Execution Plan',author='EpiVibe')
    story=[]
    def p(value,style='EpiBody'):
        return Paragraph(escape(str(value if value is not None else '—')).replace('\n','<br/>'),styles[style])
    def section(title):story.append(p(title,'EpiSection'))
    def sub(title):story.append(p(title,'EpiSub'))
    def para(value):story.append(p(value))
    def value(v):
        if v is None or v=='':return '—'
        if isinstance(v,list):return '; '.join(value(x) for x in v) or '—'
        if isinstance(v,dict):return '; '.join(f'{nice(k)}: {value(x)}' for k,x in v.items()) or '—'
        return str(v)
    def nice(k):return str(k).replace('_',' ').title()
    def currency(n):
        try:return 'INR {:,.0f}'.format(Decimal(str(n)))
        except Exception:return value(n)
    def table(rows,headers=None,widths=None):
        data=[]
        if headers:data.append([p(h,'EpiHeader') for h in headers])
        data += [[p(value(cell),'EpiSmall') for cell in row] for row in rows]
        if not data:return
        t=Table(data,colWidths=widths,repeatRows=1 if headers else 0,hAlign='LEFT')
        rules=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#E5DDED'))]
        if headers:rules += [('BACKGROUND',(0,0),(-1,0),PURPLE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT])]
        else:rules += [('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white,LIGHT])]
        t.setStyle(TableStyle(rules));story.append(t);story.append(Spacer(1,9))
    def entries(rows,heading):
        for i,r in enumerate(rows or []):
            if not isinstance(r,dict):continue
            title=r.get(heading) or f'Item {i+1}'
            content=[p(title,'EpiSub')]
            for k,v in r.items():
                if k==heading or v is None or v=='':continue
                content.append(p(f'{nice(k)}: {value(v)}','EpiSmall'))
                content.append(Spacer(1,4))
            story.append(KeepTogether(content[:2]) if len(content)>1 else content[0])
            story.extend(content[2:])
            story.append(Spacer(1,5))
    def page(canvas,doc):
        canvas.saveState();w,h=A4
        canvas.setStrokeColor(colors.HexColor('#D9C6E8'));canvas.line(42,40,w-42,40)
        canvas.setFont(bold,8);canvas.setFillColor(PURPLE);canvas.drawString(42,h-30,'EpiVibe  |  AI Event Strategist')
        canvas.setFont(regular,8);canvas.setFillColor(GRAY);canvas.drawRightString(w-42,27,f'Execution Plan  •  Page {doc.page}')
        canvas.restoreState()
    story.append(p('COMPLETE EXECUTION PLAN','EpiMuted'))
    story.append(p(plan.get('event_name') or 'Event Execution Plan','EpiTitle'))
    table([
        ['Venue',value(plan.get('venue'))],['Event dates',value(plan.get('event_dates'))],
        ['Approved working budget',currency(plan.get('budget_total'))],
        ['Activity count',str(len(plan.get('activities') or []))]
    ],['Event Detail','Approved Plan'],[155,355])
    section('1. Overview')
    sub('Executive Summary');para(plan.get('executive_summary'))
    sub('Objectives');para(plan.get('objectives'))
    sub('Key Milestones')
    table([[r.get('date'),r.get('milestone'),r.get('description')] for r in (plan.get('timeline') or []) if isinstance(r,dict)],['Date','Milestone','Description'],[85,135,290])
    sub('Budget Summary')
    table([[r.get('category'),currency(r.get('amount'))] for r in (plan.get('budget_breakdown') or []) if isinstance(r,dict)],['Category','Approved Amount'],[340,170])
    sub('Priority Tasks')
    table([[r.get('task'),r.get('owner_role'),r.get('due_date'),r.get('priority')] for r in (plan.get('tasks') or [])[:6] if isinstance(r,dict)],['Task','Owner','Due','Priority'],[205,125,95,85])
    section('2. Timeline & Tasks')
    sub('Preparation & Delivery Milestones');entries(plan.get('timeline'),'milestone')
    sub('All Execution Tasks');entries(plan.get('tasks'),'task')
    section('3. Activities & Resources')
    sub('Activity Execution Plans');entries(plan.get('activities'),'name')
    sub('Resources, Vendors & Equipment');entries(plan.get('resources'),'resource')
    section('4. Budget & Marketing')
    sub('Approved Budget & Procurement')
    table([[r.get('category'),currency(r.get('amount')),r.get('procurement_notes')] for r in (plan.get('budget_breakdown') or []) if isinstance(r,dict)],['Category','Amount','Procurement Notes'],[160,95,255])
    para('Total approved budget: '+currency(plan.get('budget_total')))
    sub('Marketing & Promotion');entries(plan.get('marketing'),'action')
    section('5. Operations & Risks')
    sub('Operations & Logistics');entries(plan.get('operations'),'area')
    sub('Risks & Mitigation');entries(plan.get('risks'),'risk')
    sub('Event-Day Runbook')
    table([[r.get('date'),r.get('time'),r.get('action'),r.get('owner_role')] for r in (plan.get('event_day_runbook') or []) if isinstance(r,dict)],['Date','Time','Action','Owner'],[82,65,238,125])
    sub('Post-Event Closure');entries(plan.get('post_event'),'action')
    doc.build(story,onFirstPage=page,onLaterPages=page)
    return buff.getvalue()
