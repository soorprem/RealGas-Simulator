"""Ideal comparisons and two-state changes; reuse the same PR solver and datum."""
import math
import pandas as pd
from eos_model import R
from pvt_calculations import calculate
from ideal_gas import ideal_contributions


def ideal_comparison(state):
    """Signed differences at identical T,P. No percent of datum-dependent H or S."""
    v_ideal=R*state['T_K']/(state['P_bar']*1e5)
    rows=[('Compressibility factor','-',1.,state['Z']),
          ('Molar volume','L/mol',1000*v_ideal,1000*state['volume_m3_mol']),
          ('Fugacity coefficient','-',1.,state['phi']),
          ('Fugacity','bar',state['P_bar'],state['fugacity_bar'])]
    if not state['thermal_error']:
        rows += [('Enthalpy','kJ/mol',state['H_ideal_J_mol']/1000,state['H_kJ_mol']),
                 ('Entropy','J/(mol K)',state['S_ideal_J_molK'],state['S_J_molK'])]
    return pd.DataFrame([{'Property':name,'Unit':unit,'Ideal gas':ig,'Peng–Robinson':real,
                          'PR minus ideal':real-ig,
                          'Deviation (%)':100*(real/ig-1) if name not in ('Enthalpy','Entropy') else None}
                         for name,unit,ig,real in rows])


def two_state(c,T1,P1,T2,P2,tref=298.15,pref=1.,phase1='Stable',phase2='Stable'):
    initial=calculate(c,T1,P1,tref,pref,phase1)
    final=calculate(c,T2,P2,tref,pref,phase2)
    for label,s in [('Initial',initial),('Final',final)]:
        if s['thermal_error']:
            raise ValueError(f"{label} state: {s['thermal_error']}")
    # Direct integration between endpoints cancels the arbitrary reference datum.
    ig=ideal_contributions(c,T2,P2,T1,P1)
    dh_ig=ig['H_ideal_J_mol']/1000
    ds_ig=ig['S_ideal_J_molK']
    dh_res=(final['H_res_J_mol']-initial['H_res_J_mol'])/1000
    ds_res=final['S_res_J_molK']-initial['S_res_J_molK']
    return dict(component=c.name,initial=initial,final=final,
                delta_H_ideal_kJ_mol=dh_ig,delta_H_residual_kJ_mol=dh_res,
                delta_H_kJ_mol=dh_ig+dh_res,
                delta_S_ideal_J_molK=ds_ig,delta_S_residual_J_molK=ds_res,
                delta_S_J_molK=ds_ig+ds_res,
                delta_volume_L_mol=1000*(final['volume_m3_mol']-initial['volume_m3_mol']),
                volume_ratio=final['volume_m3_mol']/initial['volume_m3_mol'])


def process_table(result):
    one,two=result['initial'],result['final']
    specs=[('Enthalpy','kJ/mol',one['H_ideal_J_mol']/1000,two['H_ideal_J_mol']/1000,one['H_kJ_mol'],two['H_kJ_mol']),
           ('Entropy','J/(mol K)',one['S_ideal_J_molK'],two['S_ideal_J_molK'],one['S_J_molK'],two['S_J_molK']),
           ('Molar volume','L/mol',R*one['T_K']/one['P_bar']/100,R*two['T_K']/two['P_bar']/100,one['volume_m3_mol']*1000,two['volume_m3_mol']*1000)]
    return pd.DataFrame([dict(Property=prop,Unit=unit,Ideal_initial=i1,Ideal_final=i2,Ideal_change=i2-i1,
                              PR_initial=r1,PR_final=r2,PR_change=r2-r1,
                              Component=result['component'],T1_K=one['T_K'],P1_bar=one['P_bar'],
                              T2_K=two['T_K'],P2_bar=two['P_bar'],
                              Initial_root=one['phase_rule'],Final_root=two['phase_rule'])
                         for prop,unit,i1,i2,r1,r2 in specs])
