"""Molar entropy, J/(mol K), ideal reference plus PR departure."""
def entropy(state, ideal):
    return ideal['S_ideal_J_molK']+state['S_res_J_molK']
