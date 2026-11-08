"""Physical invariants and independent reconstructions for the new features."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from eos_model import R,pressure
from component_data import COMPONENTS
from process_calculations import two_state,ideal_comparison,process_table
from pvt_calculations import calculate
from plotting import isotherms,comparison_figures,sweep

@pytest.mark.parametrize('component',COMPONENTS.values(),ids=COMPONENTS.keys())
def test_process_endpoint_differences_reference_and_reversal(component):
    r=two_state(component,400,50,500,20)
    a,b=r['initial'],r['final']
    assert r['delta_H_kJ_mol']==pytest.approx(b['H_kJ_mol']-a['H_kJ_mol'],abs=1e-12)
    assert r['delta_S_J_molK']==pytest.approx(b['S_J_molK']-a['S_J_molK'],abs=1e-12)
    changed=two_state(component,400,50,500,20,tref=350,pref=2)
    rev=two_state(component,500,20,400,50)
    for key in ['delta_H_kJ_mol','delta_S_J_molK','delta_volume_L_mol']:
        assert changed[key]==pytest.approx(r[key],abs=1e-10)
        assert rev[key]==pytest.approx(-r[key],abs=1e-10)
    assert rev['volume_ratio']*r['volume_ratio']==pytest.approx(1)
    assert process_table(r).iloc[2].Ideal_initial==pytest.approx(R*400/(50*1e5)*1000)


def test_process_zero_and_isothermal_limits():
    c=COMPONENTS['Methane']
    r=two_state(c,400,50,400,50)
    assert r['delta_H_kJ_mol']==0 and r['delta_S_J_molK']==0 and r['delta_volume_L_mol']==0
    r=two_state(c,400,1e-6,400,1e-5)
    assert r['delta_H_ideal_kJ_mol']==0
    assert r['delta_S_ideal_J_molK']==pytest.approx(-R*math.log(10))
    assert abs(r['delta_H_kJ_mol'])<1e-7
    with pytest.raises(ValueError):two_state(c,200,50,500,20)


def test_ideal_comparison_low_pressure_and_residuals():
    c=COMPONENTS['Methane']
    state=calculate(c,400,50)
    table=ideal_comparison(state).set_index('Property')
    assert table.loc['Molar volume','Deviation (%)']==pytest.approx(100*(state['Z']-1))
    assert table.loc['Enthalpy','PR minus ideal']==pytest.approx(state['H_res_J_mol']/1000)
    assert table.loc['Entropy','PR minus ideal']==pytest.approx(state['S_res_J_molK'])
    assert np.isnan(table.loc['Entropy','Deviation (%)'])
    dilute=ideal_comparison(calculate(c,400,1e-6)).set_index('Property')
    assert abs(dilute.loc['Molar volume','Deviation (%)'])<1e-6


def test_isotherms_pressure_and_stability():
    c=COMPONENTS['Propane']
    fig,df=isotherms(c,[300,369.8,450],.08,5,150,180)
    assert len(fig.data)==9 and len(df)==540
    for _,row in df.iloc[::17].iterrows():
        assert row.PR_pressure_bar==pytest.approx(pressure(c,row.T_K,row.volume_L_mol/1000)/1e5)
        assert row.Ideal_pressure_bar==pytest.approx(R*row.T_K/(row.volume_L_mol/1000)/1e5)
    assert not df.mechanically_stable.all()
    with pytest.raises(ValueError):isotherms(c,[300,369.8,450],.001,5)


def test_comparison_pressure_plots():
    c=COMPONENTS['Methane']
    df=sweep(c,400,50,298.15,1,'Stable',.1,150,300,700,30)
    f,g,data=comparison_figures(df)
    assert len(f.data)==2 and len(g.data)==1
    assert np.allclose(data.Volume_deviation_percent,100*(data.PR_volume_L_mol/data.Ideal_volume_L_mol-1))
