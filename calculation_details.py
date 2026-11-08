"""Equations and numeric substitutions displayed for the computed snapshot."""
import pandas as pd
import streamlit as st
from eos_model import R,OMEGA_A,OMEGA_B


def details(s):
    e=s['parameters']; c=s['component_data']; T=s['T_K']; P=s['P_bar']
    with st.expander('Calculation details · equations, substitutions and units'):
        st.caption('All EOS arithmetic uses Pa, K, m³/mol and J/mol. Display pressure is bar (1 bar = 100000 Pa).')
        st.latex(r'P=\frac{RT}{v-b}-\frac{a(T)}{v^2+2bv-b^2},\quad T_r=T/T_c,\quad P_r=P/P_c')
        st.write(f"Tᵣ = {T:g}/{c['tc']:g} = {e['tr']:.9g}; Pᵣ = {P:g}/{c['pc_bar']:g} = {e['pr']:.9g}. R = {R:.12g} J/(mol K).")
        st.latex(r'\kappa=0.37464+1.54226\omega-0.26992\omega^2,\quad\alpha=[1+\kappa(1-\sqrt{T_r})]^2')
        st.latex(r'a_c=\Omega_A R^2 T_c^2/P_c,\quad a=a_c\alpha,\quad b=\Omega_B RT_c/P_c,\quad a_T=-\frac{a_c\kappa[1+\kappa(1-\sqrt{T_r})]}{\sqrt{TT_c}}')
        st.write(f"ω = {c['omega']:g}; ΩA = {OMEGA_A:.16g}; ΩB = {OMEGA_B:.16g}. Unrounded PR constants are from NIST teqp canonical_PR metadata.")
        units={'tr':'-','pr':'-','kappa':'-','alpha':'-','ac':'Pa m⁶/mol²','a':'Pa m⁶/mol²','da_dt':'Pa m⁶/(mol² K)','b':'m³/mol','A':'-','B':'-'}
        st.dataframe(pd.DataFrame([{'Variable':k,'Value':v,'Unit':units[k]} for k,v in e.items()]),hide_index=True,width='stretch')
        st.latex(r'A=\frac{aP}{R^2T^2},\ B=\frac{bP}{RT},\quad Z^3+(B-1)Z^2+(A-2B-3B^2)Z-AB+B^2+B^3=0')
        st.write('Substituted polynomial coefficients [Z³, Z², Z, 1]: '+', '.join(f'{v:.12g}' for v in s['coefficients']))
        st.latex(r'v=ZRT/P')
        st.write(f"v = {s['Z']:.10g} × {R:.10g} × {T:g} / {P*1e5:.10g} = {s['volume_m3_mol']:.10g} m³/mol.")
        st.latex(r'L=\ln\frac{Z+(1+\sqrt{2})B}{Z+(1-\sqrt{2})B},\quad H^R=RT(Z-1)+\frac{Ta_T-a}{2\sqrt{2}b}L')
        st.write(f"L = {s['L']:.12g}; Hᴿ = {R*T*(s['Z']-1):.10g} + ({T:g} × {e['da_dt']:.10g} − {e['a']:.10g}) / (2√2 × {e['b']:.10g}) × {s['L']:.10g} = {s['H_res_J_mol']:.10g} J/mol.")
        st.latex(r'S^R=R\ln(Z-B)+\frac{a_T}{2\sqrt{2}b}L')
        st.write(f"Sᴿ = {R:.10g} ln({s['Z']:.10g} − {e['B']:.10g}) + {e['da_dt']:.10g}/(2√2 × {e['b']:.10g}) × {s['L']:.10g} = {s['S_res_J_molK']:.10g} J/(mol K).")
        st.latex(r'\ln\phi=Z-1-\ln(Z-B)-\frac{a}{2\sqrt{2}bRT}L,\quad f=\phi P')
        st.write(f"ln φ = ({s['Z']:.10g} − 1) − ln({s['Z']:.10g} − {e['B']:.10g}) − {e['a']:.10g}/(2√2 × {e['b']:.10g} × {R:.10g} × {T:g}) × {s['L']:.10g} = {s['ln_phi']:.10g}.")
        st.write(f"φ = exp({s['ln_phi']:.10g}) = {s['phi']:.10g}; f = {s['phi']:.10g} × {P:g} = {s['fugacity_bar']:.10g} bar.")
        st.latex(r'\frac{C_P^{ig}}R=A_c+B_cT+C_cT^2+D_c/T^2')
        st.write(f"Cp/R = {c['cp_a']:g} + ({c['cp_b']:g}) T + ({c['cp_c']:g}) T² + ({c['cp_d']:g})/T²; validity {c['tmin']:g}–{c['tmax']:g} K.")
        st.latex(r'H^{ig}=R[A_c(T-T_0)+\tfrac{B_c}{2}(T^2-T_0^2)+\tfrac{C_c}{3}(T^3-T_0^3)+D_c(T_0^{-1}-T^{-1})]')
        st.latex(r'S^{ig}=R[A_c\ln(T/T_0)+B_c(T-T_0)+\tfrac{C_c}{2}(T^2-T_0^2)+\tfrac{D_c}{2}(T_0^{-2}-T^{-2})-\ln(P/P_0)]')
        st.write(f"T₀ = {s['T_ref_K']:g} K; P₀ = {s['P_ref_bar']:g} bar. Cp coefficients carry powers of kelvin so Cp/R is dimensionless.")
        if not s['thermal_error']:
            st.write('H ideal integral terms (A, B, C, D), J/mol: '+', '.join(f'{x:.10g}' for x in s['H_integral_terms']))
            st.write('S ideal terms (A, B, C, D, pressure), J/(mol K): '+', '.join(f'{x:.10g}' for x in s['S_integral_terms']))
            st.write(f"H = ({s['H_ideal_J_mol']:.10g} + {s['H_res_J_mol']:.10g})/1000 = {s['H_kJ_mol']:.10g} kJ/mol.")
            st.write(f"S = {s['S_ideal_J_molK']:.10g} + {s['S_res_J_molK']:.10g} = {s['S_J_molK']:.10g} J/(mol K).")
        else:
            st.warning(s['thermal_error'])
        st.markdown('**Derivation.** Integrate the EOS in density to obtain residual Helmholtz energy. At fixed T and v:')
        st.latex(r'A^R_{T,v}=-RT\ln(1-b/v)-\frac{a}{2\sqrt2 b}\ln\frac{v+(1+\sqrt2)b}{v+(1-\sqrt2)b}')
        st.markdown('Here the Helmholtz departure uses an ideal gas at the same T and v. Use Uᴿ = Aᴿ − T(∂Aᴿ/∂T)ᵥ and Hᴿ = Uᴿ + RT(Z−1). For entropy at the same T and P, add R ln Z to the same-density entropy departure. This gives the expressions above; Gᴿ = Hᴿ − TSᴿ = RT ln φ. No equations from SRK are used.')
