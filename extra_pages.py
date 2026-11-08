"""Comparison and process UI, with calculations kept in process_calculations.py."""
import json
import streamlit as st
from eos_model import R
from process_calculations import ideal_comparison,two_state,process_table
from downloads import download_button
from pvt_calculations import flat_result
import pandas as pd


def show_comparison(s):
    st.subheader('Ideal-gas comparison at the same temperature and pressure')
    v=R*s['T_K']/s['P_bar']/100
    a,b,c=st.columns(3)
    a.metric('Ideal molar volume (L/mol)',f'{v:.7g}')
    b.metric('PR molar volume (L/mol)',f"{s['volume_m3_mol']*1000:.7g}")
    c.metric('Volume deviation from ideal (%)',f"{100*(s['Z']-1):.7g}")
    table=ideal_comparison(s)
    st.dataframe(table,hide_index=True,width='stretch')
    st.caption('Signed deviation = 100(PR − ideal)/ideal. H and S differences are shown in physical units; their percentage deviations depend on the arbitrary reference datum and are intentionally omitted.')
    if s['thermal_error']:st.warning(s['thermal_error'])
    st.latex(r'v^{ig}=RT/P,\quad v^{PR}=ZRT/P,\quad\frac{v^{PR}-v^{ig}}{v^{ig}}100=100(Z-1)')
    st.write(f"vig = {R:.10g} × {s['T_K']:g} / ({s['P_bar']:g} × 100) = {v:.10g} L/mol; deviation = 100 × ({s['Z']:.10g} − 1) = {100*(s['Z']-1):.10g}%.")
    st.info('Comparisons use the same T, P and reference datum. HPR − Hig and SPR − Sig are exactly the PR residual contributions. Ideal-gas values use Z = φ = 1 and f = P.')
    export=table.assign(Component=s['component'],T_K=s['T_K'],P_bar=s['P_bar'],T_ref_K=s['T_ref_K'],P_ref_bar=s['P_ref_bar'])
    download_button(st,'Download ideal comparison CSV',export.to_csv(index=False).encode(),'ideal_gas_comparison.csv','text/csv')


def show_process(c,s):
    st.subheader('Two-state process calculator')
    st.caption('Choose initial and final homogeneous states of the same component. Component constants and the reference datum come from the last calculated common state.')
    st.info('These are endpoint property changes. Heat, shaft work, boundary work and entropy generation need additional process or equipment assumptions and are not inferred here.')
    with st.form('process_inputs'):
        one,two=st.columns(2)
        with one:
            st.markdown('#### Initial state')
            t1=st.number_input('Initial temperature (K)',50.,2500.,float(s['T_K']),key='process_t1')
            p1=st.number_input('Initial pressure (bar)',.000001,2000.,float(s['P_bar']),format='%.6f',key='process_p1')
            root1=st.selectbox('Initial root rule',['Stable','Vapour','Liquid'],key='process_root1')
        with two:
            st.markdown('#### Final state')
            t2=st.number_input('Final temperature (K)',50.,2500.,float(min(s['T_K']+100,c.tmax)),key='process_t2')
            p2=st.number_input('Final pressure (bar)',.000001,2000.,20.,format='%.6f',key='process_p2')
            root2=st.selectbox('Final root rule',['Stable','Vapour','Liquid'],key='process_root2')
        go=st.form_submit_button('Calculate process',type='primary')
    signature=json.dumps([c.to_dict(),s['T_ref_K'],s['P_ref_bar']],sort_keys=True)
    if go or 'process_result' not in st.session_state or st.session_state.get('process_signature')!=signature:
        try:
            result=two_state(c,t1,p1,t2,p2,s['T_ref_K'],s['P_ref_bar'],root1,root2)
            st.session_state.process_result=result
            st.session_state.process_signature=signature
        except (ValueError,OverflowError,ArithmeticError) as exc:
            st.error(str(exc));return
    r=st.session_state.process_result
    a,b,d=st.columns(3)
    a.metric('ΔH (kJ/mol)',f"{r['delta_H_kJ_mol']:.7g}")
    b.metric('ΔS (J/mol K)',f"{r['delta_S_J_molK']:.7g}")
    d.metric('Δv (L/mol)',f"{r['delta_volume_L_mol']:.7g}")
    x,y=r['initial'],r['final']
    st.write(f"Calculated snapshot: {r['component']}, {x['T_K']:g} K / {x['P_bar']:g} bar ({x['phase_rule']}) → {y['T_K']:g} K / {y['P_bar']:g} bar ({y['phase_rule']}). v₂/v₁ = {r['volume_ratio']:.7g}.")
    table=process_table(r)
    st.dataframe(table.iloc[:,:8],hide_index=True,width='stretch')
    with st.expander('Process equations and contributions'):
        st.latex(r'\Delta H=\int_{T_1}^{T_2}C_P^{ig}\,dT+H_2^R-H_1^R')
        st.write(f"ΔH = {r['delta_H_ideal_kJ_mol']:.10g} + ({r['delta_H_residual_kJ_mol']:.10g}) = {r['delta_H_kJ_mol']:.10g} kJ/mol.")
        st.latex(r'\Delta S=\int_{T_1}^{T_2}(C_P^{ig}/T)\,dT-R\ln(P_2/P_1)+S_2^R-S_1^R')
        st.write(f"ΔS = {r['delta_S_ideal_J_molK']:.10g} + ({r['delta_S_residual_J_molK']:.10g}) = {r['delta_S_J_molK']:.10g} J/(mol K).")
        st.latex(r'\Delta v=R(Z_2T_2/P_2-Z_1T_1/P_1)')
        st.write(f"Δv = {y['volume_m3_mol']*1000:.10g} − {x['volume_m3_mol']*1000:.10g} = {r['delta_volume_L_mol']:.10g} L/mol.")
        st.caption('Δ means final minus initial. The arbitrary ideal reference cancels; a common datum is retained in the endpoint tables. Endpoint specifications do not define an equilibrium trajectory or two-phase fraction.')
        st.dataframe(pd.DataFrame([flat_result(x),flat_result(y)]),hide_index=True,width='stretch')
    for label,state in [('Initial',x),('Final',y)]:
        for note in state['notes']:st.caption(f'{label}: {note}')
    a,b=st.columns(2)
    download_button(a,'Download process CSV',table.to_csv(index=False).encode(),'two_state_process.csv','text/csv')
    download_button(b,'Download process JSON',json.dumps(r,indent=2).encode(),'two_state_process.json','application/json')
