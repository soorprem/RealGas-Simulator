"""One calculation pipeline shared by all pages, tables and downloads."""
from eos_model import solve_state
from ideal_gas import ideal_contributions
from enthalpy import enthalpy
from entropy import entropy
from fugacity import fugacity


def calculate(c,T,p_bar,tref=298.15,pref_bar=1.0,phase='Stable'):
    state=solve_state(c,T,p_bar,phase)
    state.update(component_data=c.to_dict(),T_ref_K=tref,P_ref_bar=pref_bar)
    state['fugacity_bar']=fugacity(state)
    try:
        ideal=ideal_contributions(c,T,p_bar,tref,pref_bar)
        state.update(ideal,H_kJ_mol=enthalpy(state,ideal),S_J_molK=entropy(state,ideal),thermal_error=None)
    except ValueError as exc:
        state.update(H_kJ_mol=None,S_J_molK=None,thermal_error=str(exc))
    return state


def flat_result(s):
    keys=['component','T_K','P_bar','T_ref_K','P_ref_bar','phase_rule','Z','volume_m3_mol','phi','fugacity_bar','H_ideal_J_mol','H_res_J_mol','H_kJ_mol','S_ideal_J_molK','S_res_J_molK','S_J_molK','thermal_error']
    return {k:s.get(k) for k in keys}
