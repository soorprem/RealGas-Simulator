"""Enthalpy uses the same PR state and alpha derivative as fugacity/entropy."""
def enthalpy(state, ideal):
    return (ideal['H_ideal_J_mol']+state['H_res_J_mol'])/1000  # kJ/mol
