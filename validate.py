"""Regenerate reproducible sample/validation tables; requires requirements-dev.txt."""
from pathlib import Path
import json,math,platform
import numpy as np
import pandas as pd
import CoolProp
import CoolProp.CoolProp as CP
from scipy.optimize import brentq
from component_data import COMPONENTS
from eos_model import R,pressure,solve_state
from pvt_calculations import calculate,flat_result

ROOT=Path(__file__).resolve().parent;out=ROOT/'validation';out.mkdir(exist_ok=True)
rows=[];low=[];grid=[];heos=[]
for key,c in COMPONENTS.items():
    name='Validation_'+key.replace(' ','')
    fluid=dict(name=name,CAS=name,Tc=c.tc,Tc_units='K',pc=c.pc_bar*1e5,pc_units='Pa',acentric=c.omega,molemass=.04,molemass_units='kg/mol',aliases=[])
    # Molar mass is a required placeholder for custom registration only. All comparisons are MOLAR.
    CP.add_fluids_as_JSON('PR',json.dumps([fluid]))
    AS=CP.AbstractState('PR',name)
    for T,P,phase in [(400,1,'Vapour'),(450,40,'Vapour'),(600,150,'Vapour'),(max(80,c.tc*.85),c.pc_bar*2,'Liquid')]:
        AS.specify_phase(CP.iphase_liquid if phase=='Liquid' else CP.iphase_gas)
        AS.update(CP.PT_INPUTS,P*1e5,T)
        s=solve_state(c,T,P,phase)
        ref={'Z':AS.compressibility_factor(),'phi':AS.fugacity_coefficient(0),'H_res_J_mol':AS.hmolar_residual(),'S_res_J_molK':AS.smolar_residual()+R*math.log(AS.compressibility_factor())}
        for prop,val in ref.items():
            actual=s[prop];error=abs(actual-val)
            tol=1e-7 if prop=='H_res_J_mol' else 1e-8
            rows.append(dict(component=key,T_K=T,P_bar=P,branch=phase,property=prop,app_value=actual,CoolProp_PR=val,absolute_error=error,tolerance=tol,passed=error<tol))
    s=solve_state(c,400,1e-6,'Vapour')
    low.append(dict(component=key,T_K=400,P_bar=1e-6,Z=s['Z'],phi=s['phi'],f_over_P=s['fugacity_bar']/1e-6,H_res_J_mol=s['H_res_J_mol'],S_res_J_molK=s['S_res_J_molK']))
    for tr in [.65,.9,.99,1,1.01,1.5,3]:
        for pr in [1e-6,.01,.1,.5,.99,1,1.01,2,5,10]:
            t=c.tc*tr;p=c.pc_bar*pr;ss=solve_state(c,t,p)
            err=abs(pressure(c,t,ss['volume_m3_mol'])-p*1e5)
            grid.append(dict(component=key,T_K=t,P_bar=p,Z=ss['Z'],relative_pressure_error=err/(p*1e5),absolute_pressure_error_Pa=err))
    fluid_name={'Carbon dioxide':'CarbonDioxide'}.get(key,key)
    hs=CP.AbstractState('HEOS',fluid_name);hs.update(CP.PT_INPUTS,50e5,400)
    ours=solve_state(c,400,50)
    heos.append(dict(component=key,T_K=400,P_bar=50,PR_Z=ours['Z'],HEOS_Z=hs.compressibility_factor(),Z_error_percent=100*(ours['Z']/hs.compressibility_factor()-1)))
pd.DataFrame(rows).to_csv(out/'coolprop_comparison.csv',index=False)
pd.DataFrame(low).to_csv(out/'low_pressure.csv',index=False)
pd.DataFrame(grid).to_csv(out/'grid_stability.csv',index=False)
pd.DataFrame(heos).to_csv(out/'heos_model_comparison.csv',index=False)
summary=[]
for key,c in COMPONENTS.items():
    rr=[r for r in rows if r['component']==key]
    ll=next(r for r in low if r['component']==key)
    summary.append(dict(Component=key,PR_checks=len(rr),Max_abs_Z_error=max(r['absolute_error'] for r in rr if r['property']=='Z'),Max_abs_HR_error_J_mol=max(r['absolute_error'] for r in rr if r['property']=='H_res_J_mol'),LowP_abs_Z_minus_1=abs(ll['Z']-1),Passed=all(r['passed'] for r in rr)))
pd.DataFrame(summary).to_csv(out/'summary.csv',index=False)
sample=calculate(COMPONENTS['Methane'],400,50)
(ROOT/'sample_output.json').write_text(json.dumps(sample,indent=2))
pd.DataFrame([flat_result(sample)]).to_csv(ROOT/'sample_output.csv',index=False)
(ROOT/'sample_input.json').write_text(json.dumps(dict(component='Methane',T_K=400,P_bar=50,T_ref_K=298.15,P_ref_bar=1,root_rule='Stable'),indent=2))
meta=dict(Python=platform.python_version(),CoolProp=CoolProp.__version__,numpy=np.__version__,states_grid=len(grid),reference_scalar_checks=len(rows),all_reference_checks_passed=all(r['passed'] for r in rows),note='Independent implementation verification is not experimental validation. HEOS comparison uses built-in high-accuracy fluids and may use different critical constants.')
(out/'environment.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta));print(pd.DataFrame(summary).to_string(index=False));print(pd.DataFrame(heos).to_string(index=False))
assert meta['all_reference_checks_passed']
