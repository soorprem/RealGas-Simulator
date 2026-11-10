"""Presentation helpers; thermodynamic calculations remain in the existing modules."""
from html import escape
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from eos_model import solve_state

CSS = '''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--ink:#172e2a;--green:#12694f;--muted:#72817b;--line:#e0e7e1}
html,body,.stApp{font-family:'DM Sans',sans-serif}
.stApp{background:#f5f7f3;color:var(--ink)}
.block-container{padding:2.8rem 3rem 3rem;max-width:1500px}
h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;color:var(--ink);letter-spacing:-.04em}
h1{font-weight:800!important}h2{font-size:1.5rem!important}h3{font-size:1.13rem!important}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
[data-testid="stSidebar"]>div:first-child{padding-top:2rem}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:.55rem .7rem;border-radius:9px;margin:2px 0;width:100%;transition:background .15s}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:#edf4ec}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){background:#e4f1e7;color:#12694f;font-weight:700}
[data-testid="stSidebar"] [data-testid="stRadio"] label p{font-size:.86rem}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.2rem;box-shadow:0 3px 12px #173c2604}
[data-testid="stMetricLabel"]{color:#6b7f74;font-size:.78rem}
[data-testid="stMetricValue"]{font-family:'Manrope',sans-serif;font-size:1.9rem;font-weight:700;letter-spacing:-.04em;color:#163e30}
[data-testid="stForm"]{background:white;border:1px solid var(--line);border-radius:16px;padding:1.3rem}
[data-testid="stExpander"]{background:white;border-color:var(--line);border-radius:12px}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden}
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"] button{border-radius:9px;font-weight:600;min-height:2.8rem}
button[kind="primary"],button[kind="primaryFormSubmit"]{background:#12694f;border-color:#12694f}
[data-baseweb="input"],[data-baseweb="select"]>div{border-radius:9px;background:#f8faf7}
[data-testid="stAlert"]{border-radius:12px;font-size:.88rem}
.rg-brand{display:flex;align-items:center;gap:11px;margin:0 0 2rem}.rg-mark{display:grid;place-items:center;width:39px;height:43px;background:#173f30;color:#cef4b4;border-radius:10px;font:700 20px 'Manrope',sans-serif}.rg-brand strong{display:block;font:800 20px 'Manrope',sans-serif;letter-spacing:-.8px}.rg-brand small{font-size:10px;color:#87948a;letter-spacing:1.6px}
.rg-label{font-size:10px;font-weight:700;letter-spacing:1.7px;color:#839087;margin:22px 0 10px}
.rg-navfoot{margin-top:36px;border-top:1px solid #e5ebe4;padding-top:22px;font-size:12px;line-height:1.8;color:#839087}.rg-navfoot b{color:#315743}
.rg-topline{display:flex;align-items:center;justify-content:space-between;margin:0 0 24px;color:#819084;font-size:12px}.rg-topline b{color:#355944;font-weight:500}.rg-pill{border:1px solid #d8e5d6;background:#f0f6ed;color:#46713d;padding:6px 11px;border-radius:25px;font-size:11px}
.rg-hero{position:relative;overflow:hidden;border-radius:20px;background:#173f30;color:#e9f3e6;padding:34px 38px;margin-bottom:25px;min-height:170px}.rg-hero:after{content:'Z = PV / RT';position:absolute;right:38px;top:52px;font:500 40px 'Manrope',sans-serif;color:#99bd8840;letter-spacing:-2px;transform:rotate(-6deg)}
.rg-hero .rg-eyebrow{font-size:10px;letter-spacing:2px;color:#b0d39a;font-weight:700}.rg-hero h1{color:#f3faee!important;margin:10px 0 9px;font-size:2.65rem!important;line-height:1.2;max-width:75%}.rg-hero p{font-size:13px;line-height:1.7;color:#c3d7bf;max-width:560px;margin:0}.rg-hero .rg-dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:#b9e99b;margin-right:7px}
.rg-pageintro{margin:0 0 22px}.rg-pageintro h1{font-size:2.2rem;margin:6px 0}.rg-pageintro p{color:#728276;margin:0;font-size:14px}
.rg-section{display:flex;align-items:center;justify-content:space-between;margin:15px 0 15px}.rg-section strong{font:800 16px 'Manrope',sans-serif;letter-spacing:-.5px}.rg-section small{color:#839184;font-size:11px}
.rg-state{display:flex;gap:10px;flex-wrap:wrap;align-items:center;background:#edf3e9;border:1px solid #dce8d7;padding:12px 17px;border-radius:10px;font-size:12px;margin:14px 0 22px}.rg-state b{color:#275c3e}.rg-state span{color:#6e836d}.rg-state .rg-live{margin-left:auto;font-size:10px;color:#568149}
.rg-card{background:#fff;border:1px solid #e0e7e1;border-radius:15px;padding:22px;margin:6px 0 9px;min-height:154px}.rg-card .rg-no{font-size:11px;color:#85a676;letter-spacing:1px}.rg-card h3{margin:11px 0 8px!important;font-size:17px!important}.rg-card p{font-size:12px;line-height:1.7;color:#7a887c;margin:0}
.rg-tip{padding:17px 20px;border-left:3px solid #8ebc6a;background:#eaf2e4;color:#476342;border-radius:0 10px 10px 0;font-size:12px;line-height:1.8;margin:16px 0}
.rg-footer{font-size:11px;color:#8a958a;display:flex;justify-content:space-between;padding:25px 0 0;border-top:1px solid #e0e7e1;margin-top:22px}
[data-testid="stPlotlyChart"]{border:1px solid #e0e7e1;border-radius:15px;overflow:hidden;background:white}
@media(max-width:900px){.block-container{padding:2.8rem 1.1rem}.rg-hero{padding:26px 24px}.rg-hero h1{font-size:2rem!important;max-width:100%}.rg-hero:after{display:none}.rg-topline{font-size:10px}.rg-state .rg-live{margin-left:0}[data-testid="stMetricValue"]{font-size:1.5rem}}
</style>'''

PAGE_COPY = {
    'PVT Calculator': ('Pressure, volume & temperature.', 'Find compressibility, molar volume and the physically admissible roots.'),
    'Enthalpy Calculator': ('Understand the energy.', 'Separate ideal-gas enthalpy from the Peng–Robinson departure.'),
    'Entropy Calculator': ('Track the entropy.', 'Explore temperature, pressure and real-gas entropy contributions.'),
    'Fugacity Calculator': ('Beyond ideal pressure.', 'Calculate fugacity and inspect the escaping tendency of a real fluid.'),
    'Ideal-gas comparison': ('How ideal is your gas?', 'Compare real and ideal properties at exactly the same conditions.'),
    'Two-state process': ('From one state to another.', 'Calculate enthalpy, entropy and volume changes on a common datum.'),
    'Graphical Analysis': ('See the thermodynamics.', 'Explore ten interactive plots with your own pressure and temperature ranges.'),
    'About the Project': ('The science behind the screen.', 'Model assumptions, data sources, validation and the technical report.')
}

def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)

def brand():
    st.markdown('<div class="rg-brand"><div class="rg-mark">Rg</div><div><strong>RealGas</strong><small>SIMULATION STUDIO</small></div></div><div class="rg-label">YOUR WORKSPACE</div>',unsafe_allow_html=True)

def page_header(page):
    st.markdown(f'<div class="rg-topline"><span>WORKSPACE &nbsp; / &nbsp; <b>{escape(page)}</b></span><span class="rg-pill">Peng–Robinson EOS</span></div>',unsafe_allow_html=True)
    if page == 'Dashboard':
        st.markdown('<div class="rg-hero"><div class="rg-eyebrow"><span class="rg-dot"></span>REAL-GAS THERMODYNAMICS, MADE CLEAR</div><h1>A little beyond ideal.</h1><p>Explore how real gases behave. Calculate properties, compare states, and see the science behind every result.</p></div>',unsafe_allow_html=True)
    else:
        title,desc=PAGE_COPY[page]
        st.markdown(f'<div class="rg-pageintro"><div class="rg-label">REALGAS / {escape(page.upper())}</div><h1>{title}</h1><p>{desc}</p></div>',unsafe_allow_html=True)

def section(title, subtitle=''):
    st.markdown(f'<div class="rg-section"><strong>{escape(title)}</strong><small>{escape(subtitle)}</small></div>',unsafe_allow_html=True)

def state_bar(s):
    st.markdown(f'<div class="rg-state"><b>{escape(s["component"])}</b><span>·</span><b>{s["T_K"]:g} K</b><span>·</span><b>{s["P_bar"]:g} bar</b><span>·</span><span>{escape(s["phase_rule"])} root</span><span class="rg-live">● LAST CALCULATED STATE</span></div>',unsafe_allow_html=True)

def navigate(page):
    st.session_state.page=page

def dashboard(s, comp):
    section('Explore your next calculation', 'ONE COMPONENT. ONE CONSISTENT MODEL.')
    cards=[('01 / STATE','PVT & fugacity','Inspect compressibility, molar volume and real-gas fugacity.','PVT Calculator','Explore PVT'),('02 / ENERGY','Enthalpy & entropy','See ideal and residual contributions, with every equation explained.','Enthalpy Calculator','Explore properties'),('03 / PROCESS','Compare two states','Find ΔH, ΔS and Δv between your initial and final conditions.','Two-state process','Calculate a process')]
    for col,(num,title,description,page,label) in zip(st.columns(3),cards):
        with col:
            st.markdown(f'<div class="rg-card"><div class="rg-no">{num}</div><h3>{title}</h3><p>{description}</p></div>',unsafe_allow_html=True)
            st.button(label+' →',key='jump_'+page,on_click=navigate,args=(page,),width='stretch')
    section('A closer look at your gas', 'LIVE PRESSURE RESPONSE')
    left,right=st.columns([1.7,1])
    with left:
        pressure=np.linspace(max(1e-6,s['P_bar']/100),min(2000,max(100,s['P_bar']*2)),45)
        values=[]
        for p in pressure:
            try:values.append(solve_state(comp,s['T_K'],float(p),s['phase_rule'])['Z'])
            except (ValueError,OverflowError,ArithmeticError):values.append(None)
        fig=go.Figure()
        fig.add_scatter(x=pressure,y=values,name='Peng–Robinson',mode='lines',line=dict(color='#267b51',width=3),fill='tozeroy',fillcolor='rgba(114,166,90,0.10)',connectgaps=False)
        fig.add_hline(y=1,line_dash='dot',line_color='#abb4a1',annotation_text='Ideal gas · Z = 1',annotation_position='top left')
        fig.add_scatter(x=[s['P_bar']],y=[s['Z']],name='Your state',mode='markers',marker=dict(color='#173f30',size=9,line=dict(color='white',width=2)))
        valid=[v for v in values if v is not None]
        if valid:
            lo,hi=min(min(valid),1),max(max(valid),1);pad=max(.025,(hi-lo)*.2)
            fig.update_yaxes(range=[lo-pad,hi+pad])
        fig.update_layout(title=dict(text=f'Compressibility at {s["T_K"]:g} K',font=dict(size=15)),xaxis_title='Pressure (bar)',yaxis_title='Compressibility factor Z',height=310,margin=dict(l=30,r=25,t=55,b=45),paper_bgcolor='white',plot_bgcolor='white',font=dict(family='DM Sans',color='#536b58',size=11),legend=dict(orientation='h',y=-.25),xaxis=dict(gridcolor='#edf0e9'),yaxis=dict(gridcolor='#edf0e9'))
        st.plotly_chart(fig,width='stretch')
    with right:
        st.markdown(f'<div class="rg-card"><div class="rg-no">YOUR GAS AT A GLANCE</div><h3>{escape(s["component"])}</h3><p>Volume differs from ideal gas by <b>{100*(s["Z"]-1):+.2f}%</b> at this state.<br><br>Reference: {s["T_ref_K"]:g} K · {s["P_ref_bar"]:g} bar<br>Cp validity: {comp.tmin:g}–{comp.tmax:g} K</p></div>',unsafe_allow_html=True)
        st.button('Open all 10 plots →',key='jump_graphs',on_click=navigate,args=('Graphical Analysis',),width='stretch')
        st.button('Compare with ideal gas →',key='jump_ideal',on_click=navigate,args=('Ideal-gas comparison',),width='stretch')
    st.markdown('<div class="rg-tip"><b>Try this:</b> start with methane at 400 K and 50 bar. Reduce pressure to 0.000001 bar to explore the ideal-gas limit. For multiple cubic roots, try propane at 300 K and 10 bar.</div>',unsafe_allow_html=True)
