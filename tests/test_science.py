"""Meaningful checks: independent backend, numerical derivatives/integrals, roots."""
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.optimize import brentq
from component_data import COMPONENTS, Component
from eos_model import R,parameters,solve_state,pressure
from ideal_gas import heat_capacity,ideal_contributions
from pvt_calculations import calculate

@pytest.mark.parametrize('c',COMPONENTS.values(),ids=COMPONENTS.keys())
def test_low_pressure(c):
    s=solve_state(c,400,1e-6,'Vapour')
    assert abs(s['Z']-1)<2e-8
    assert abs(s['phi']-1)<2e-8
    assert abs(s['fugacity_bar']/1e-6-1)<2e-8
    assert abs(s['H_res_J_mol'])<1e-4
    assert abs(s['S_res_J_molK'])<1e-6

@pytest.mark.parametrize('c',COMPONENTS.values(),ids=COMPONENTS.keys())
def test_alpha_derivative_and_ideal_integrals(c):
    T=500; e=parameters(c,T,30); dt=0.001
    fd=(parameters(c,T+dt,30).a-parameters(c,T-dt,30).a)/(2*dt)
    assert e.da_dt==pytest.approx(fd,rel=2e-8)
    i=ideal_contributions(c,T,30)
    assert i['H_ideal_J_mol']==pytest.approx(quad(lambda t:heat_capacity(c,t),298.15,T)[0],rel=1e-11)
    assert i['S_ideal_J_molK']==pytest.approx(quad(lambda t:heat_capacity(c,t)/t,298.15,T)[0]-R*math.log(30),abs=1e-10)
    zero=ideal_contributions(c,298.15,1)
    assert zero['H_ideal_J_mol']==0 and zero['S_ideal_J_molK']==0

@pytest.mark.parametrize('c',COMPONENTS.values(),ids=COMPONENTS.keys())
def test_departures_from_numerical_fugacity_derivative(c):
    T=450; P=40; dt=0.002; dp=0.001
    s=solve_state(c,T,P)
    dln=(solve_state(c,T+dt,P)['ln_phi']-solve_state(c,T-dt,P)['ln_phi'])/(2*dt)
    assert s['H_res_J_mol']==pytest.approx(-R*T*T*dln,rel=2e-7,abs=1e-5)
    assert s['S_res_J_molK']==pytest.approx((s['H_res_J_mol']-R*T*s['ln_phi'])/T,abs=1e-10)
    dlnp=(solve_state(c,T,P+dp)['ln_phi']-solve_state(c,T,P-dp)['ln_phi'])/(2*dp)
    assert dlnp==pytest.approx((s['Z']-1)/P,rel=2e-7,abs=1e-10)

@pytest.mark.parametrize('c',COMPONENTS.values(),ids=COMPONENTS.keys())
def test_numerical_pressure_integrals(c):
    # Independent bracketing solver and numerical thermodynamic pressure integrals.
    T=450.; P=40.; tiny=1e-7
    def z_bracket(t,pbar):
        e=parameters(c,t,pbar); p=pbar*1e5
        v=brentq(lambda v:pressure(c,t,v)-p,e.b*(1+1e-9),10*R*t/p,xtol=1e-16,rtol=1e-13)
        return p*v/(R*t)
    def z_and_derivative(p):
        z=z_bracket(T,p); dt=.005
        dz=(z_bracket(T+dt,p)-z_bracket(T-dt,p))/(2*dt)
        return z,dz
    lnphi=quad(lambda p:(z_bracket(T,p)-1)/p,tiny,P,epsabs=1e-9)[0]
    hr=quad(lambda p:-R*T*T*z_and_derivative(p)[1]/p,tiny,P,epsabs=1e-5)[0]
    sr=quad(lambda p:-R*(z_and_derivative(p)[0]-1+T*z_and_derivative(p)[1])/p,tiny,P,epsabs=1e-7)[0]
    s=solve_state(c,T,P)
    assert s['ln_phi']==pytest.approx(lnphi,abs=2e-8)
    assert s['H_res_J_mol']==pytest.approx(hr,abs=3e-4)
    assert s['S_res_J_molK']==pytest.approx(sr,abs=2e-6)

@pytest.mark.parametrize('c',COMPONENTS.values(),ids=COMPONENTS.keys())
def test_coolprop_pr(c):
    CP=pytest.importorskip('CoolProp.CoolProp')
    name='RG_'+c.name.replace(' ','')
    fluid=dict(name=name,CAS=name,Tc=c.tc,Tc_units='K',pc=c.pc_bar*1e5,pc_units='Pa',acentric=c.omega,molemass=.04,molemass_units='kg/mol',aliases=[])
    CP.add_fluids_as_JSON('PR',json.dumps([fluid]))
    AS=CP.AbstractState('PR',name)
    AS.specify_phase(CP.iphase_gas)
    for T,P in [(400,1),(450,40),(600,150)]:
        AS.update(CP.PT_INPUTS,P*1e5,T)
        s=solve_state(c,T,P)
        assert s['Z']==pytest.approx(AS.compressibility_factor(),rel=1e-10)
        assert s['phi']==pytest.approx(AS.fugacity_coefficient(0),rel=1e-10)
        assert s['H_res_J_mol']==pytest.approx(AS.hmolar_residual(),abs=1e-7)
        # CoolProp residual entropy uses the same T and density.
        # S_ideal(T,P) = S_ideal(T,rho) - R ln Z, so ADD R ln Z.
        sr=AS.smolar_residual()+R*math.log(AS.compressibility_factor())
        assert s['S_res_J_molK']==pytest.approx(sr,abs=1e-8)


def test_three_roots_and_coexistence():
    c=COMPONENTS['Propane']
    s=solve_state(c,300,10)
    assert len(s['roots'])==3
    assert s['roots'][0]['mechanically_stable']
    assert not s['roots'][1]['mechanically_stable']
    assert s['roots'][-1]['mechanically_stable']
    assert s['ln_phi']==min(r['ln_phi'] for r in s['roots'] if r['mechanically_stable'])
    psat=brentq(lambda p:solve_state(c,300,p,'Liquid')['ln_phi']-solve_state(c,300,p,'Vapour')['ln_phi'],8,12)
    l=solve_state(c,300,psat,'Liquid');v=solve_state(c,300,psat,'Vapour')
    assert l['Z']<v['Z'] and abs(l['ln_phi']-v['ln_phi'])<1e-10


def test_domain_and_heat_capacity_errors():
    c=COMPONENTS['Methane']
    for t,p in [(0,1),(300,0),(float('nan'),10),(300,float('inf'))]:
        with pytest.raises(ValueError):solve_state(c,t,p)
    s=calculate(c,200,10)
    assert s['H_kJ_mol'] is None and s['thermal_error'] and s['phi']>0
    bad=Component('bad',190,46,.01,-1,0,0,0)
    with pytest.raises(ValueError):ideal_contributions(bad,400,1)


def test_grid_stability_and_pressure_reconstruction():
    for c in COMPONENTS.values():
        for tr in [.65,.9,.99,1,1.01,1.5,3]:
            for pr in [1e-6,.01,.1,.5,.99,1,1.01,2,5,10]:
                T=c.tc*tr;P=c.pc_bar*pr
                s=solve_state(c,T,P)
                assert all(math.isfinite(s[k]) for k in ('Z','phi','H_res_J_mol','S_res_J_molK'))
                assert pressure(c,T,s['volume_m3_mol'])==pytest.approx(P*1e5,rel=2e-6,abs=.01)
                assert s['Z']>s['parameters']['B']
