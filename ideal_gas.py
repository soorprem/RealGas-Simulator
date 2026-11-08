"""Analytical integrals of the textbook Cp/R correlation, no extrapolation."""
import math
from eos_model import R, validate_component


def heat_capacity(c,T):
    return R*(c.cp_a+c.cp_b*T+c.cp_c*T*T+c.cp_d/T**2)


def ideal_contributions(c,T,p_bar,tref=298.15,pref_bar=1.0):
    validate_component(c)
    if not all(math.isfinite(v) and v>0 for v in (T,p_bar,tref,pref_bar)):
        raise ValueError('State and reference temperatures and pressures must be finite and positive.')
    lo,hi = sorted((T,tref))
    if lo<c.tmin or hi>c.tmax:
        raise ValueError(f'Cp correlation for {c.name} is valid only from {c.tmin:g} to {c.tmax:g} K, including the full reference-to-state path.')
    # Check positivity at endpoints and all stationary points of Cp(T).
    import numpy as np
    stationary=np.roots([2*c.cp_c,c.cp_b,0,0,-2*c.cp_d]) if any((c.cp_c,c.cp_b,c.cp_d)) else []
    check=[lo,hi]+[float(x.real) for x in stationary if abs(x.imag)<1e-8 and lo<x.real<hi]
    if any(heat_capacity(c,x)<=0 for x in check):
        raise ValueError('Heat capacity is nonpositive on the integration path; correct the coefficients.')
    a,b,cc,d = c.cp_a,c.cp_b,c.cp_c,c.cp_d
    ht=[R*a*(T-tref),R*b/2*(T*T-tref*tref),R*cc/3*(T**3-tref**3),R*d*(1/tref-1/T)]
    st=[R*a*math.log(T/tref),R*b*(T-tref),R*cc/2*(T*T-tref*tref),R*d/2*(1/tref**2-1/T**2),-R*math.log(p_bar/pref_bar)]
    return dict(H_ideal_J_mol=sum(ht),S_ideal_J_molK=sum(st),H_integral_terms=ht,S_integral_terms=st,Cp_J_molK=heat_capacity(c,T))
