"""Portable calculation PDF, generated from the exact displayed state."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from pvt_calculations import flat_result


def calculation_pdf(s):
    b=BytesIO(); styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(b,rightMargin=40,leftMargin=40,topMargin=36,bottomMargin=36)
    story=[Paragraph('RealGas Simulator | Calculation record',styles['Title']),Paragraph('Pure-component Peng-Robinson equation of state',styles['Normal']),Spacer(1,12)]
    rows=[['Property (units in key)','Value']]
    for k,v in flat_result(s).items():
        rows.append([Paragraph(escape(k),styles['BodyText']),Paragraph(escape(f'{v:.10g}' if isinstance(v,float) else str(v)),styles['BodyText'])])
    table=Table(rows,colWidths=[260,235],repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173047')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#eef4f7'),colors.white]),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.extend([table,Spacer(1,10),Paragraph('Reference: H_ideal(Tref) = 0; S_ideal(Tref, Pref) = 0. Totals include departures at the calculated state and are not absolute properties or zeroed real-fluid differences.',styles['BodyText'])])
    for note in s['notes']:
        story.append(Paragraph(escape(note),styles['BodyText']))
    story.extend([Spacer(1,8),Paragraph('Data: '+escape(s['component_data']['source']),styles['BodyText']),Paragraph('See THEORY.md and the application calculation details for equations, derivative, units and derivation.',styles['BodyText'])])
    doc.build(story)
    return b.getvalue()
