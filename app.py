"""Run from this directory with: streamlit run app.py"""
from pathlib import Path
import json
import pandas as pd
import streamlit as st
from component_data import COMPONENTS,Component
from pvt_calculations import calculate,flat_result
from calculation_details import details
from plotting import sweep,figure,PLOTS,comparison_figures,isotherms
from extra_pages import show_comparison,show_process
from export_report import calculation_pdf
from downloads import download_button

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='RealGas Simulator',page_icon='🧪',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container{padding-top:4rem;max-width:1450px} h1{letter-spacing:-.035em;color:#173047} h2,h3{color:#173047}
[data-testid="stMetric"]{background:white;border:1px solid #dde6ee;border-top:3px solid #087f8c;border-radius:8px;padding:16px}
[data-testid="stSidebar"]{border-right:1px solid #d7e2ea} .rg-kicker{font-size:12px;font-weight:700;letter-spacing:.16em;color:#087f8c;margin-bottom:8px}
</style>''',unsafe_allow_html=True)
PAGES=['Dashboard','PVT Calculator','Enthalpy Calculator','Entropy Calculator','Fugacity Calculator','Ideal-gas comparison','Two-state process','Graphical Analysis','About the Project']
with st.sidebar:
    st.markdown('## RealGas Simulator')
    st.caption('PURE COMPONENT · PENG–ROBINSON')
    page=st.radio('Workspace',PAGES,label_visibility='collapsed',key='page')
    st.divider()
    name=st.selectbox('Component',list(COMPONENTS)+['Custom component'],key='component_choice')
    base=COMPONENTS.get(name,COMPONENTS['Methane'])
    with st.form('state_inputs'):
        st.markdown('#### Common inputs')
        cname=st.text_input('Component name',value=base.name if name!='Custom component' else 'Custom gas',key=f'name_{name}')
        c1,c2=st.columns(2)
        T=c1.number_input('Temperature (K)',50.0,2500.0,400.0,10.0,format='%.4f')
        P=c2.number_input('Pressure (bar)',0.000001,2000.0,50.0,1.0,format='%.6f')
        phase=st.selectbox('Root selection',['Stable','Vapour','Liquid'])
        with st.expander('Critical constants & Cp data',expanded=name=='Custom component'):
            tc=st.number_input('Critical temperature (K)',min_value=0.1,value=float(base.tc),key=f'tc_{name}',format='%.5f')
            pc=st.number_input('Critical pressure (bar)',min_value=0.000001,value=float(base.pc_bar),key=f'pc_{name}',format='%.6f')
            om=st.number_input('Acentric factor',min_value=-0.5,max_value=0.5,value=float(base.omega),key=f'om_{name}',format='%.6f')
            st.caption('Cp/R = A + B T + C T² + D/T². Enter unscaled coefficients; T in K.')
            ca=st.number_input('Cp A (dimensionless)',value=float(base.cp_a),key=f'a_{name}',format='%.8g')
            cb=st.number_input('Cp B (1/K)',value=float(base.cp_b),key=f'b_{name}',format='%.8g')
            cc=st.number_input('Cp C (1/K²)',value=float(base.cp_c),key=f'c_{name}',format='%.8g')
            cd=st.number_input('Cp D (K²)',value=float(base.cp_d),key=f'd_{name}',format='%.8g')
            mn=st.number_input('Cp minimum T (K)',min_value=1.0,value=float(base.tmin),key=f'mn_{name}')
            mx=st.number_input('Cp maximum T (K)',min_value=1.0,value=float(base.tmax),key=f'mx_{name}')
        with st.expander('Reference state'):
            tref=st.number_input('Reference temperature (K)',min_value=1.0,value=298.15,format='%.4f')
            pref=st.number_input('Reference pressure (bar)',min_value=0.000001,value=1.0,format='%.6f')
        submitted=st.form_submit_button('Calculate state',type='primary',width='stretch')
    st.caption('Edit inputs, then calculate to update the displayed state. Tables and downloads use that same snapshot.')

if 'history' not in st.session_state: st.session_state.history=[]
if submitted or 'result' not in st.session_state:
    original=(name in COMPONENTS and (cname,tc,pc,om,ca,cb,cc,cd,mn,mx)==(base.name,base.tc,base.pc_bar,base.omega,base.cp_a,base.cp_b,base.cp_c,base.cp_d,base.tmin,base.tmax))
    component=Component(cname,tc,pc,om,ca,cb,cc,cd,mn,mx,base.source if original else 'User-supplied parameters; verify sources and validity before use')
    try:
        result=calculate(component,T,P,tref,pref,phase)
        st.session_state.result=result
        st.session_state.history.append(flat_result(result))
    except (ValueError,OverflowError,ArithmeticError) as exc:
        st.error(str(exc))
        if 'result' not in st.session_state: st.stop()
        st.warning('Calculation failed. The previous successful state remains below.')
s=st.session_state.result
comp=Component(**s['component_data'])
st.markdown('<div class="rg-kicker">CHEMICAL ENGINEERING / THERMODYNAMIC WORKSPACE</div>',unsafe_allow_html=True)
st.title('RealGas Simulator')
st.caption('PVT Behaviour and Thermodynamic Property Prediction Using Cubic Equations of State.')
st.markdown(f"**{page}**  ·  {s['component']}  ·  {s['T_K']:g} K  ·  {s['P_bar']:g} bar  ·  {s['phase_rule']} root")
st.caption(f"Data: {comp.source}. Heat-capacity range: {comp.tmin:g}–{comp.tmax:g} K. Displayed values correspond to the last successful calculation.")

def metrics():
    cols=st.columns(4)
    for col,label,value in zip(cols,['Compressibility Z','Molar volume (L/mol)','Fugacity coefficient φ','Fugacity (bar)'],[s['Z'],s['volume_m3_mol']*1000,s['phi'],s['fugacity_bar']]):
        col.metric(label,f'{value:.6g}')


def roots_table():
    rows=[]
    for i,r in enumerate(s['roots']):
        label='Single admissible root' if len(s['roots'])==1 else ('Liquid-like' if i==0 else ('Vapour-like' if i==len(s['roots'])-1 else 'Unstable'))
        rows.append({'Root':label,'Z':r['Z'],'Volume (L/mol)':r['volume_m3_mol']*1000,'ln φ':r['ln_phi'],'dP/dV (Pa mol/m³)':r['dP_dV'],'Selected':abs(r['Z']-s['Z'])<1e-10})
    st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
    for note in s['notes']: st.info(note)

if page=='Dashboard':
    metrics()
    st.subheader('One state. Four connected calculations.')
    left,right=st.columns([1.1,1])
    with left:
        st.markdown('Calculate real-gas volume, enthalpy, entropy and fugacity using a shared Peng–Robinson state. Inspect the equations on each page, compare roots, then explore pressure and temperature sweeps.')
        st.markdown('**Suggested demonstration:** methane at 400 K and 50 bar; then reduce pressure to 0.000001 bar to inspect the ideal-gas limit. Use propane at 300 K and 10 bar to demonstrate three roots.')
        st.info('Hᶦᵍ(T₀) = 0 and Sᶦᵍ(T₀, P₀) = 0. H and S totals include state departures; they are relative to this ideal-gas datum, not absolute values. Real-gas totals need not vanish at T₀, P₀.')
    with right:
        data=[['EOS','Peng–Robinson, original alpha'],['Scope','Pure homogeneous fluid; no mixtures'],['Internal units','Pa, K, m³/mol, J/mol'],['Reference',f"{s['T_ref_K']:g} K / {s['P_ref_bar']:g} bar"],['Heat capacity',f'Cp/R polynomial, {comp.tmin:g}–{comp.tmax:g} K']]
        st.dataframe(pd.DataFrame(data,columns=['Setting','Value']),hide_index=True,width='stretch')
    if s['thermal_error']: st.warning(s['thermal_error'])
    elif s['H_kJ_mol'] is not None:
        a,b=st.columns(2);a.metric('Enthalpy (kJ/mol)',f"{s['H_kJ_mol']:.6g}");b.metric('Entropy (J/mol K)',f"{s['S_J_molK']:.6g}")
    details(s)
elif page=='PVT Calculator':
    metrics();st.subheader('Cubic roots and phase selection');roots_table()
    e=s['parameters'];a,b=st.columns(2);a.metric('Reduced temperature',f"{e['tr']:.6g}");b.metric('Reduced pressure',f"{e['pr']:.6g}")
    st.caption('Mechanical stability requires (∂P/∂v)T ≤ 0. Among stable outer roots, minimum fugacity gives minimum molar Gibbs energy. A forced outer branch can be metastable.')
    details(s)
elif page in ('Enthalpy Calculator','Entropy Calculator'):
    is_h=page.startswith('Enthalpy'); st.subheader('Ideal-gas contribution + EOS departure')
    st.info(f"Ideal-gas zero: T₀ = {s['T_ref_K']:g} K, P₀ = {s['P_ref_bar']:g} bar. Departures compare real and ideal gases at the same T and P.")
    if s['thermal_error']:
        st.error(s['thermal_error']);st.write('PVT, fugacity and residual properties remain available. Change the state/reference to the Cp validity interval for total properties.')
    else:
        a,b,c=st.columns(3)
        if is_h:
            a.metric('Ideal enthalpy (kJ/mol)',f"{s['H_ideal_J_mol']/1000:.7g}");b.metric('Residual enthalpy (kJ/mol)',f"{s['H_res_J_mol']/1000:.7g}");c.metric('Total enthalpy (kJ/mol)',f"{s['H_kJ_mol']:.7g}")
        else:
            a.metric('Ideal entropy (J/mol K)',f"{s['S_ideal_J_molK']:.7g}");b.metric('Residual entropy (J/mol K)',f"{s['S_res_J_molK']:.7g}");c.metric('Total entropy (J/mol K)',f"{s['S_J_molK']:.7g}")
        st.write(f"Ideal-gas Cp at this state: {s['Cp_J_molK']:.7g} J/(mol K).")
    details(s)
elif page=='Fugacity Calculator':
    metrics()
    st.subheader('Effective pressure for chemical potential')
    st.markdown('Fugacity measures the escaping tendency of a fluid. For a pure gas, chemical potential is μ = μ°(T) + RT ln(f/P°). The coefficient φ = f/P accounts for molecular interactions; equal fugacity identifies phase equilibrium. At low pressure on the gas branch, φ and Z approach 1 and f/P approaches 1.')
    st.latex(r'f=\phi P')
    st.write(f"f = {s['phi']:.9g} × {s['P_bar']:g} = {s['fugacity_bar']:.9g} bar.")
    roots_table();details(s)
elif page=='Ideal-gas comparison':
    show_comparison(s)
elif page=='Two-state process':
    show_process(comp,s)
elif page=='Graphical Analysis':
    st.subheader('Pressure and temperature sweeps')
    st.caption('Plots and downloads use the last successful Generate graphs calculation; edit bounds and submit the form to refresh them.')
    st.caption('Pressure sweeps hold the calculated T fixed; temperature sweeps hold the calculated P fixed. Each point independently applies the selected root rule. Branch jumps can occur at phase transitions; these are not two-phase mixture properties.')
    with st.form('graph_controls'):
        a,b,c,d=st.columns(4)
        pmin=a.number_input('Minimum pressure (bar)',0.000001,2000.0,0.1,format='%.6f')
        pmax=b.number_input('Maximum pressure (bar)',0.000001,2000.0,150.0)
        tmin=c.number_input('Minimum temperature (K)',50.0,2500.0,300.0)
        tmax=d.number_input('Maximum temperature (K)',50.0,2500.0,700.0)
        n=st.slider('Points per sweep',30,200,90)
        st.markdown('**P–V isotherm controls**')
        a,b,c=st.columns(3)
        iso1=a.number_input('Isotherm 1 temperature (K)',50.,2500.,float(min(2500,max(50,.85*comp.tc))))
        iso2=b.number_input('Isotherm 2 temperature (K)',50.,2500.,float(min(2500,max(50,comp.tc))))
        iso3=c.number_input('Isotherm 3 temperature (K)',50.,2500.,float(min(2500,max(50,1.2*comp.tc))))
        a,b=st.columns(2)
        vmin=a.number_input('Minimum isotherm volume (L/mol)',min_value=.000001,value=float(s['parameters']['b']*1100),format='%.7f')
        vmax=b.number_input('Maximum isotherm volume (L/mol)',min_value=.000001,value=float(max(s['parameters']['b']*100000,s['volume_m3_mol']*3000)),format='%.7f')
        draw=st.form_submit_button('Generate graphs',type='primary')
    signature=json.dumps(s,sort_keys=True)
    if draw or 'graphs' not in st.session_state or st.session_state.get('graph_signature')!=signature:
        if pmin>=pmax or tmin>=tmax:
            st.error('Each minimum must be less than its maximum.')
        else:
            try:
                iso_fig,iso_data=isotherms(comp,[iso1,iso2,iso3],vmin,vmax,pmax,max(180,n))
                new_sweep=sweep(comp,s['T_K'],s['P_bar'],s['T_ref_K'],s['P_ref_bar'],s['phase_rule'],pmin,pmax,tmin,tmax,n)
                st.session_state.graphs=new_sweep
                st.session_state.isotherm_plot=iso_fig
                st.session_state.isotherm_data=iso_data
                st.session_state.graph_signature=signature
            except (ValueError,OverflowError) as exc:
                st.error(str(exc))
    if 'graphs' in st.session_state:
        df=st.session_state.graphs
        bad=df['thermal_error'].notna().sum()
        if bad: st.warning(f'{bad} sweep points have unavailable properties. See the downloaded error column. EOS results are retained when only Cp is outside its range.')
        left,right=st.columns(2)
        for i,(y,title,unit) in enumerate(PLOTS):
            with (left if i%2==0 else right):st.plotly_chart(figure(df[df.sweep=='P'],'P_bar',y,title,unit,s['phase_rule']),width='stretch')
        for col,y,title,unit in [(right,'H_kJ_mol','Enthalpy','kJ/mol'),(left,'S_J_molK','Entropy','J/(mol K)')]:
            with col:st.plotly_chart(figure(df[df.sweep=='T'],'T_K',y,title,unit,s['phase_rule']),width='stretch')
        st.subheader('Ideal-gas comparisons and P–V isotherms')
        volume_fig,deviation_fig,comparison_data=comparison_figures(df)
        a,b=st.columns(2)
        a.plotly_chart(volume_fig,width='stretch')
        b.plotly_chart(deviation_fig,width='stretch')
        if 'isotherm_plot' in st.session_state:
            st.plotly_chart(st.session_state.isotherm_plot,width='stretch')
            st.caption('Solid PR segments have dP/dv ≤ 0; dotted segments are mechanically unstable. These raw homogeneous EOS curves do not represent an equilibrium two-phase plateau. Ideal curves can be enabled from the legend. Logarithmic volume axis; displayed pressure is 0 to the chosen maximum.')
            download_button(st,'Download isotherm CSV',st.session_state.isotherm_data.to_csv(index=False).encode(),'pv_isotherms.csv','text/csv')
        download_button(st,'Download ideal-volume comparison CSV',comparison_data.to_csv(index=False).encode(),'ideal_volume_sweep.csv','text/csv')
        download_button(st,'Download sweep CSV',df.to_csv(index=False).encode(),'realgas_sweeps.csv','text/csv')
elif page=='About the Project':
    st.subheader('Development of software for real-gas thermodynamics')
    st.write('Built from scratch because no previous PVT program was available. This implementation retains PVT as the core calculation and adds consistent PR enthalpy, entropy and pure-component fugacity. Includes ideal-gas comparison, a two-state calculator and ten interactive plots. Intended for undergraduate demonstration and analysis.')
    st.markdown('**Architecture:** inputs → validation → PR parameters and alpha derivative → cubic roots and stability → ideal-gas integrals + departures → tables, graphs and downloads.')
    st.markdown('**Limitations:** pure components; original PR alpha for −0.5 ≤ ω ≤ 0.5; no mixtures, solids, association, reactions or two-phase quality. PR liquid densities and near-critical predictions can be inaccurate. The numerical input domain is not an accuracy guarantee. Total H and S are blocked outside the full Cp validity path. Manual data must be checked by the user.')
    st.markdown('**Data and theory:** Smith, Van Ness, Abbott & Swihart, *Introduction to Chemical Engineering Thermodynamics*, 8e, Chapters 3 and 13, Appendix B and Table C.1. Unrounded PR constants: [NIST teqp](https://pages.nist.gov/teqp-docs/en/main/models/cubics.html). Independent software checks: [CoolProp cubic backend](https://coolprop.org/coolprop/Cubics.html).')
    vf=ROOT/'validation'/'summary.csv'
    if vf.exists():
        st.subheader('Executed validation');st.dataframe(pd.read_csv(vf),hide_index=True,width='stretch')
        download_button(st,'Download validation table',vf.read_bytes(),'validation_summary.csv','text/csv')
    pdf=ROOT/'report.pdf'
    if pdf.exists():download_button(st,'Download project report',pdf.read_bytes(),'RealGas_Technical_Report.pdf','application/pdf')
    details(s)

st.divider()
st.subheader('Results & session history')
st.caption('History lasts for this browser session. Download records before closing it. SI units are included in CSV column names; H_kJ_mol is in kJ/mol.')
with st.expander('Current result table'):
    st.dataframe(pd.DataFrame([flat_result(s)]),hide_index=True,width='stretch')
a,b,c=st.columns(3)
download_button(a,'Download state CSV',pd.DataFrame([flat_result(s)]).to_csv(index=False).encode(),'realgas_state.csv','text/csv',width='stretch')
download_button(b,'Download calculation JSON',json.dumps(s,indent=2).encode(),'realgas_calculation.json','application/json',width='stretch')
download_button(c,'Download calculation PDF',calculation_pdf(s),'realgas_calculation.pdf','application/pdf',width='stretch')
with st.expander(f"Calculation history ({len(st.session_state.history)} states)"):
    history=pd.DataFrame(st.session_state.history)
    st.dataframe(history,hide_index=True,width='stretch')
    download_button(st,'Download history CSV',history.to_csv(index=False).encode(),'realgas_history.csv','text/csv')
    if st.button('Clear history'):
        st.session_state.history=[];st.rerun()
