"""Pure-component Peng-Robinson EOS, all internal quantities in molar SI.
No ideal heat-capacity model is needed to evaluate EOS departure functions.
"""
import math
from dataclasses import asdict, dataclass
import numpy as np
from component_data import Component

R = 8.31446261815324
# Unrounded critical constraints, NIST teqp canonical_PR metadata.
OMEGA_A = 0.4572355289213822
OMEGA_B = 0.07779607390388846
SQRT2 = math.sqrt(2)

@dataclass(frozen=True)
class Parameters:
    tr: float
    pr: float
    kappa: float
    alpha: float
    ac: float
    a: float
    da_dt: float
    b: float
    A: float
    B: float


def validate_component(c):
    values = [c.tc,c.pc_bar,c.omega,c.cp_a,c.cp_b,c.cp_c,c.cp_d,c.tmin,c.tmax]
    if not all(math.isfinite(x) for x in values):
        raise ValueError('All component parameters must be finite.')
    if not c.name.strip() or c.tc <= 0 or c.pc_bar <= 0:
        raise ValueError('Enter a component name and positive critical constants.')
    if not -0.5 <= c.omega <= 0.5:
        raise ValueError('This implementation supports acentric factors from -0.5 to 0.5 (original PR alpha).')
    if not 0 < c.tmin < c.tmax:
        raise ValueError('Heat-capacity validity limits must satisfy 0 < Tmin < Tmax.')


def parameters(c: Component, T: float, p_bar: float) -> Parameters:
    validate_component(c)
    if not math.isfinite(T) or not math.isfinite(p_bar) or not 50 <= T <= 2500 or not 1e-6 <= p_bar <= 2000:
        raise ValueError('Numerical domain: 50 ≤ T ≤ 2500 K and 0.000001 ≤ P ≤ 2000 bar. This is not a model accuracy guarantee.')
    pc, p = c.pc_bar*1e5, p_bar*1e5
    tr = T/c.tc
    k = 0.37464+1.54226*c.omega-0.26992*c.omega**2
    g = 1+k*(1-math.sqrt(tr))
    if g <= 0:
        raise ValueError('Temperature exceeds the supported PR alpha branch.')
    ac = OMEGA_A*R*R*c.tc*c.tc/pc
    a = ac*g*g
    da = -ac*k*g/math.sqrt(T*c.tc)
    b = OMEGA_B*R*c.tc/pc
    return Parameters(tr,p/pc,k,g*g,ac,a,da,b,a*p/(R*T)**2,b*p/(R*T))


def pressure(c, T, volume):
    """Return pressure in Pa for molar volume in m³/mol (V>b)."""
    e = parameters(c,T,1)
    if not math.isfinite(volume) or volume <= e.b:
        raise ValueError('Molar volume must exceed b.')
    return R*T/(volume-e.b)-e.a/(volume**2+2*e.b*volume-e.b**2)


def root_properties(T, p_bar, z, e):
    v = z*R*T/(p_bar*1e5)
    # log1p retains precision in the ideal-gas limit.
    L = math.log1p(2*SQRT2*e.B/(z+(1-SQRT2)*e.B))
    log_zb = math.log1p((z-1)-e.B)
    q = e.a/(2*SQRT2*e.b*R*T)
    lnphi = (z-1)-log_zb-q*L
    hr = R*T*(z-1)+(T*e.da_dt-e.a)/(2*SQRT2*e.b)*L
    sr = R*log_zb+e.da_dt/(2*SQRT2*e.b)*L
    denom = v*v+2*e.b*v-e.b**2
    slope = -R*T/(v-e.b)**2+e.a*(2*v+2*e.b)/denom**2
    # Scaled derivative is negative for mechanically stable homogeneous roots.
    scaled_slope = slope*v/(p_bar*1e5)
    return dict(Z=float(z),volume_m3_mol=v,L=L,ln_phi=lnphi,phi=math.exp(lnphi),
                fugacity_bar=math.exp(lnphi)*p_bar,H_res_J_mol=hr,S_res_J_molK=sr,
                dP_dV=slope,scaled_slope=scaled_slope,mechanically_stable=scaled_slope <= 1e-7)


def solve_state(c, T, p_bar, phase='Stable'):
    if phase not in ('Stable','Vapour','Liquid'):
        raise ValueError('Unknown root-selection rule.')
    e = parameters(c,T,p_bar)
    A,B = e.A,e.B
    coef = [1, B-1, A-2*B-3*B*B, -A*B+B*B+B**3]
    raw = np.roots(coef)
    real = sorted(float(z.real) for z in raw if abs(z.imag)<1e-7 and z.real>B)
    roots=[]
    for z in real:
        if not roots or abs(z-roots[-1]['Z'])>1e-8:
            roots.append(root_properties(T,p_bar,z,e))
    if not roots:
        raise ValueError('No admissible real root Z>B was resolved. Move away from the critical point.')
    candidates = [r for r in roots if r['mechanically_stable']]
    if not candidates:
        raise ValueError('No mechanically stable root was resolved.')
    stable = min(candidates,key=lambda r:r['ln_phi'])
    chosen = stable if phase=='Stable' else (max(candidates,key=lambda r:r['Z']) if phase=='Vapour' else min(candidates,key=lambda r:r['Z']))
    notes=[]
    if len(roots)>1:
        notes.append('Smallest admissible root is liquid-like; largest is vapour-like. The middle root is mechanically unstable. Stable selects the lowest ln(phi) among mechanically stable roots.')
        if abs(candidates[0]['ln_phi']-candidates[-1]['ln_phi'])<1e-6:
            notes.append('Outer roots have nearly equal fugacity: possible saturation. Phase fraction is not determined by T and P.')
    else:
        notes.append('Only one admissible root exists. A single root alone does not identify a liquid or vapour phase.')
    if chosen is not stable:
        notes.append('The requested branch is metastable relative to the lower-fugacity root.')
    if len(candidates)==1 and phase!='Stable':
        notes.append('Requested branch is unavailable as a distinct root; the sole stable root is returned.')
    if abs(chosen['scaled_slope'])<0.02:
        notes.append('Near a spinodal or critical point: root sensitivity is high.')
    return dict(component=c.name,T_K=T,P_bar=p_bar,phase_rule=phase,parameters=asdict(e),
                coefficients=coef,roots=roots,notes=notes,**chosen)
