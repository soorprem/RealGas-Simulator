"""Build the four-page report from executed samples, validation and screenshots."""
from pathlib import Path
import json,math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib import font_manager
for nm, family, weight in [("RGSans","DejaVu Sans","normal"),("RGSansBold","DejaVu Sans","bold"),("RGMono","DejaVu Sans Mono","normal")]:
    pdfmetrics.registerFont(TTFont(nm,font_manager.findfont(font_manager.FontProperties(family=family,weight=weight))))
pdfmetrics.registerFontFamily("RGSans",normal="RGSans",bold="RGSansBold",italic="RGSans",boldItalic="RGSansBold")
from component_data import COMPONENTS
from eos_model import solve_state
from pvt_calculations import calculate
from export_report import calculation_pdf

ROOT=Path(__file__).resolve().parent
assets=ROOT/'report_assets';assets.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(7.2,2.1),layout='constrained')
ps=np.linspace(.001,150,120)
for name,color in [('Methane','#087f8c'),('Carbon dioxide','#cc7431'),('Propane','#415c92')]:
    ss=[solve_state(COMPONENTS[name],400,float(p)) for p in ps]
    axs[0].plot(ps,[s['Z'] for s in ss],label=name,color=color)
    axs[1].plot(ps,[s['H_res_J_mol']/1000 for s in ss],label=name,color=color)
for ax in axs:ax.set_xlabel('Pressure (bar)');ax.grid(alpha=.2);ax.legend(fontsize=7,frameon=False)
axs[0].set_ylabel('Z (-)');axs[1].set_ylabel('Residual enthalpy (kJ/mol)')
axs[0].set_title('Compressibility at 400 K');axs[1].set_title('Enthalpy departure at 400 K')
fig.savefig(assets/'results.png',dpi=200);plt.close(fig)

fig,ax=plt.subplots(figsize=(8,2.8));ax.set_xlim(-1,10);ax.set_ylim(0,4);ax.axis('off')
boxes={'input':(1,3.3,'Component / T / P\nReference and Cp data'), 'check':(5,3.3,'Validate inputs\nCheck Cp interval'), 'eos':(5,2.2,'PR parameters and roots\nSelect stable branch'), 'ideal':(1,1.1,'Analytical ideal-gas\nintegrals'), 'dep':(8,1.1,'PR departures\nand fugacity'), 'out':(5,0.05,'Combine and display\nPlot / export')}
for k,(x,y,label) in boxes.items():
    ax.add_patch(FancyBboxPatch((x-1.5,y),3,.55,boxstyle='round,pad=.06',edgecolor='#087f8c',facecolor='#eff6f7'))
    ax.text(x,y+.275,label,ha='center',va='center',fontsize=8)
def arrow(a,b):
    x,y,_=boxes[a]; xx,yy,_=boxes[b]
    if abs(y-yy)<.01: start=(x+1.55,y+.275);end=(xx-1.55,yy+.275)
    else:start=(x,y-.03);end=(xx,yy+.61)
    ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=12,color='#52677b'))
for a,b in [('input','check'),('check','eos'),('eos','ideal'),('eos','dep'),('ideal','out'),('dep','out')]:arrow(a,b)
fig.savefig(ROOT/'flowchart.png',dpi=200,bbox_inches='tight',pad_inches=.1)
fig.savefig(ROOT/'flowchart.svg',bbox_inches='tight',pad_inches=.1);plt.close(fig)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyRG',fontName='RGSans',fontSize=9.4,leading=13,spaceAfter=7,textColor=colors.HexColor('#24384a')))
styles.add(ParagraphStyle(name='SmallRG',fontName='RGSans',fontSize=8,leading=10.4,spaceAfter=5,textColor=colors.HexColor('#35495a')))
styles.add(ParagraphStyle(name='EquationRG',fontName='RGMono',fontSize=8.5,leading=12.5,spaceBefore=2,spaceAfter=6,textColor=colors.HexColor('#124d58'),backColor=colors.HexColor('#eef5f6'),borderPadding=5))
styles['Title'].fontName='RGSansBold';styles['Title'].fontSize=22;styles['Title'].leading=27;styles['Title'].textColor=colors.HexColor('#173047');styles['Title'].alignment=TA_LEFT
for k in ['Heading1','Heading2','Heading3']:styles[k].textColor=colors.HexColor('#087f8c');styles[k].fontName='RGSansBold'
styles['Heading2'].fontSize=13;styles['Heading2'].leading=16;styles['Heading2'].spaceBefore=10;styles['Heading2'].spaceAfter=7
story=[]
def p(t,small=False):story.append(Paragraph(t,styles['SmallRG' if small else 'BodyRG']))
def h(t):story.append(Paragraph(t,styles['Heading2']))
def eq(t):story.append(Paragraph(t,styles['EquationRG']))
def table(data,widths=None,small=False):
    ts=styles['SmallRG' if small else 'BodyRG']
    rows=[[Paragraph(str(x),ts) for x in row] for row in data]
    tt=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
    tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2eef0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.8,colors.HexColor('#087f8c')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    story.append(tt);story.append(Spacer(1,7))

def footer(canv,doc):
    canv.setStrokeColor(colors.HexColor('#cedce4'));canv.line(42,40,A4[0]-42,40)
    canv.setFont('Helvetica',8);canv.setFillColor(colors.HexColor('#52677b'))
    canv.drawString(42,27,'REALGAS SIMULATOR | Chemical Engineering software project')
    canv.drawRightString(A4[0]-42,27,f'{doc.page} / 4')

# PAGE 1
p('TECHNICAL REPORT  |  8 NOVEMBER 2026',True)
story.append(Paragraph('Development of Software for Predicting PVT Behaviour and Thermodynamic Properties of Real Gases',styles['Title']))
p('<b>RealGas Simulator</b> - a Python and Streamlit implementation using the Peng-Robinson equation of state.')
info_path=ROOT/'student_details.json'
info=json.loads(info_path.read_text()) if info_path.exists() else {}
from xml.sax.saxutils import escape
p('Name: '+escape(info.get('student_name') or '________________')+' | Entry no.: '+escape(info.get('entry_number') or '________________')+' | Course: '+escape(info.get('course_code') or '________________'),True)
h('Abstract')
p('A browser application was developed to calculate molar volume, compressibility, enthalpy, entropy and pure-component fugacity. A common Peng-Robinson (PR) state solver supplies all departure functions, while temperature-dependent ideal-gas heat capacities supply the ideal contributions. The software displays cubic roots, stability criteria, equations and numerical substitutions. Five preset gases and manual component data are supported, with ideal-gas comparison and a two-state process calculator. Independent PR-backend checks, thermodynamic identities, numerical integration and interface tests were executed. The deliverables include executable source, validation data, interactive graphs and this four-page report.')
h('Introduction and objectives')
p('The ideal-gas law neglects molecular size and attraction. These effects become relevant as density increases, changing both volumetric and caloric properties. A cubic EOS offers a compact model requiring critical temperature, critical pressure and acentric factor. The project connects PVT prediction to enthalpy, entropy and fugacity within one consistent EOS.')
p('The objectives are to solve the PR cubic with transparent root selection; calculate ideal and residual thermal contributions on a stated reference datum; verify low-pressure behaviour; and provide a usable website with graphs, session history and downloadable records. No existing program was available, so this implementation was developed from scratch.')
h('Background and scope')
p('PR combines an excluded-volume term with a temperature-dependent attraction term. It can generate liquid-like and vapour-like roots below the critical temperature. Admissible roots satisfy Z &gt; B. Mechanical stability and minimum Gibbs energy determine the selected homogeneous state; the application also permits explicit branch selection. It does not calculate mixture properties or two-phase quality.')
table([['Preset fluid','Tc (K)','Pc (bar)','Acentric factor'],*[[c.name,f'{c.tc:.1f}',f'{c.pc_bar:.2f}',f'{c.omega:.3f}'] for c in COMPONENTS.values()]],[205,95,100,111],True)
p('Critical constants and heat-capacity coefficients come from the supplied Smith et al. textbook [1]. Preset Cp correlations are valid from 298 K to 1500 K for hydrocarbons and to 2000 K for nitrogen and carbon dioxide. These limits are enforced for total enthalpy and entropy.',True)
story.append(PageBreak())
# PAGE 2
h('Theoretical formulation and derivation')
p('All quantities are molar; R = 8.31446261815324 J/(mol K). Pressure is converted from bar to Pa. Let a<sub>T</sub> denote da/dT, and use subscripts c for critical properties and 0 for the ideal-gas reference datum.',True)
eq('P = RT/(v-b) - a(T)/(v^2 + 2bv - b^2)<br/>Tr = T/Tc; Pr = P/Pc; k = 0.37464 + 1.54226w - 0.26992w^2<br/>g = 1 + k(1-sqrt(Tr)); alpha = g^2<br/>ac = OmegaA R^2 Tc^2/Pc; a = ac alpha; b = OmegaB R Tc/Pc<br/>aT = -ac k g/sqrt(T Tc)')
p('OmegaA = 0.4572355289213822 and OmegaB = 0.07779607390388846 are the unrounded PR critical-constraint constants reported by NIST teqp [2]. Their rounded forms are 0.45724 and 0.07780. The same attraction function and derivative are used throughout.',True)
eq('A = aP/(RT)^2; B = bP/(RT)<br/>Z^3+(B-1)Z^2+(A-2B-3B^2)Z-AB+B^2+B^3 = 0; v = ZRT/P<br/>L = ln{[Z+(1+sqrt(2))B]/[Z+(1-sqrt(2))B]}')
p('<b>Departure derivation.</b> Integrating the EOS from zero density gives the residual Helmholtz energy relative to an ideal gas at the same T and v. At fixed v, the logarithm L is independent of temperature:',True)
eq('Ar(T,v) = -RT ln(1-b/v) - a L/[2 sqrt(2)b]<br/>Ur = Ar - T(dAr/dT)v = (T aT-a)L/[2 sqrt(2)b]<br/>Hr = RT(Z-1) + (T aT-a)L/[2 sqrt(2)b]')
p('For entropy, - (dAr/dT)<sub>v</sub> gives the same-density departure. Add R ln Z to convert to a departure relative to the ideal gas at the same T and P. Then G<sup>R</sup> = H<sup>R</sup> - TS<sup>R</sup> gives fugacity:',True)
eq('Sr(T,P) = R ln(Z-B) + aT L/[2 sqrt(2)b]<br/>ln(phi) = Z-1-ln(Z-B)-a L/[2 sqrt(2)bRT]; f = phi P')
p('<b>Ideal terms and totals.</b> With Cp/R = A<sub>c</sub> + B<sub>c</sub>T + C<sub>c</sub>T<super>2</super> + D<sub>c</sub>/T<super>2</super>, analytic integration gives:',True)
eq('Hig/R = Ac(T-T0) + Bc(T^2-T0^2)/2 + Cc(T^3-T0^3)/3<br/>        + Dc(1/T0-1/T)<br/>Sig/R = Ac ln(T/T0)+Bc(T-T0)+Cc(T^2-T0^2)/2<br/>        + Dc(1/T0^2-1/T^2)/2 - ln(P/P0)<br/>H = Hig + Hr; S = Sig + Sr')
eq('Delta H = H2-H1; Delta S = S2-S1; Delta v = v2-v1<br/>vig = RT/P; volume deviation (%) = 100(Z-1)')
p('Hig(T0) = 0 and Sig(T0,P0) = 0. Total real-gas values need not vanish at the reference state. No formation enthalpy or third-law entropy is implied. H is displayed in kJ/mol and S in J/(mol K). Full derivations, units and coefficient tables are supplied in THEORY.md.',True)
story.append(PageBreak())
# PAGE 3
h('Software methodology and architecture')
p('app.py manages the nine-section Streamlit interface. eos_model.py solves PR states and selects roots; ideal_gas.py integrates Cp; pvt_calculations.py combines the shared state with enthalpy, entropy and fugacity modules. process_calculations.py computes endpoint changes; plotting.py builds ten interactive plots, including P-V isotherms and ideal-volume comparisons. The browser-hosted build mounts the same Python files in Stlite [4]; the standard project runs with streamlit run app.py.')
story.append(Image(str(ROOT/'flowchart.png'),width=500,height=166))
p('<b>Figure 1.</b> Data flow. EOS departures remain available if the Cp integration interval is invalid; total H and S are then withheld with an explanation.',True)
p('Inputs comprise component name, T, P, Tc, Pc, acentric factor, Cp coefficients and validity limits, reference T and P, and root rule. Validation rejects nonfinite values, invalid domains and nonpositive heat capacities. A successful calculation stores one consistent snapshot for all pages and exports; failed calculations preserve the previous valid state. Graph sweeps report unavailable points as gaps with error messages.')
shot=ROOT/'screenshots'/'process_calculation.jpg'
story.append(Image(str(shot if shot.exists() else ROOT/'screenshots'/'dashboard.jpg'),width=450,height=309))
p('<b>Figure 2.</b> Actual browser screenshot of the two-state calculator, using methane. Additional comparison and graphical-analysis screenshots are included in the project.',True)
story.append(PageBreak())
# PAGE 4
h('Results, validation and discussion')
s=json.loads((ROOT/'sample_output.json').read_text())
p(f"For methane at 400 K and 50 bar, with ideal-gas zero at 298.15 K and 1 bar, Z = {s['Z']:.6f}, v = {s['volume_m3_mol']*1000:.6f} L/mol, phi = {s['phi']:.6f} and f = {s['fugacity_bar']:.4f} bar. H = {s['H_ideal_J_mol']/1000:.6f} + ({s['H_res_J_mol']/1000:.6f}) = {s['H_kJ_mol']:.6f} kJ/mol; S = {s['S_ideal_J_molK']:.6f} + ({s['S_res_J_molK']:.6f}) = {s['S_J_molK']:.6f} J/(mol K). Negative S reflects the chosen datum and pressure contribution.",True)
summ=pd.read_csv(ROOT/'validation/summary.csv')
data=[['Fluid','Max |Z - Zref|','Max |Hr - Hrref|<br/>(J/mol)','Low-P |Z - 1|']]
for _,r in summ.iterrows():data.append([r['Component'],f"{r['Max_abs_Z_error']:.2e}",f"{r['Max_abs_HR_error_J_mol']:.2e}",f"{r['LowP_abs_Z_minus_1']:.2e}"])
table(data,[145,117,130,119],True)
p('<b>Table 1.</b> Executed CoolProp 8.0.0 PR comparisons with identical Tc, Pc and omega: 80 scalar checks across 20 fluid states, including liquid states. Low-pressure tests use 400 K and 10<super>-6</super> bar. The maximum |phi-1| is below 8 x 10<super>-9</super>; departures approach zero. CoolProp entropy is converted from the same-density convention by adding R ln Z.',True)
p('All 41 automated tests passed, covering scientific identities, independent numerical integration, alpha derivatives, three-root/saturation behaviour, bad inputs, custom data, all nine navigation sections, ten plots, reference invariance and two-state reversibility. A 350-state grid checked pressure reconstruction. These are implementation checks, not experimental measurements.',True)
story.append(Image(str(assets/'results.png'),width=500,height=146))
p('<b>Figure 3.</b> Stable-root PR predictions. Additional comparisons against CoolProp HEOS at 400 K and 50 bar show Z deviations from -0.63% to -2.97% for these gases. Those discrepancies reflect model and parameter differences; a matching PR backend does not establish experimental accuracy.',True)
p('<b>Conclusion and limits.</b> The program provides consistent PVT, H, S and fugacity calculations with inspectable equations and exports. PR remains an approximate pure-fluid model, especially for liquid density and near-critical states. The software excludes solids, mixtures and two-phase quality; Cp extrapolation is blocked.',True)
proc=json.loads((ROOT/'sample_process.json').read_text())
p(f"<b>Two-state example.</b> Methane, 400 K/50 bar to 500 K/20 bar: delta H = {proc['delta_H_kJ_mol']:.6f} kJ/mol, delta S = {proc['delta_S_J_molK']:.6f} J/(mol K), delta v = {proc['delta_volume_L_mol']:.6f} L/mol. Heat and work are not determined by endpoints alone.",True)
h('References')
p('[1] Smith, J.M., Van Ness, H.C., Abbott, M.M. &amp; Swihart, M.T. Introduction to Chemical Engineering Thermodynamics, 8e. McGraw-Hill, 2018. Ch. 3, 13; App. B; Table C.1, p. 656 (supplied Book.pdf).<br/>[2] NIST teqp, General cubics: pages.nist.gov/teqp-docs/en/main/models/cubics.html.<br/>[3] CoolProp 8.0.0, Cubic equations of state: coolprop.org/coolprop/Cubics.html.<br/>[4] Stlite, Browser runtime: stlite.net/browser/. Web references accessed 6 November 2026; software extended 8 November 2026.',True)

doc=SimpleDocTemplate(str(ROOT/'report.pdf'),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=50,title='RealGas Simulator - Technical Report',author='Chemical Engineering software project')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(ROOT/'sample_calculation.pdf').write_bytes(calculation_pdf(s))
from pypdf import PdfReader
n=len(PdfReader(str(ROOT/'report.pdf')).pages)
print('Report pages:',n)
assert n==4,f'Report has {n} pages; reduce content.'
