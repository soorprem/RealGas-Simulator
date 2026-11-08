"""Exercise the actual Streamlit script with its supported AppTest runner."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from streamlit.testing.v1 import AppTest
APP=Path(__file__).resolve().parents[1]/'app.py'


def app():
    return AppTest.from_file(str(APP),default_timeout=45).run()


def test_all_navigation_and_plots():
    at=app()
    assert not at.exception
    pages=['PVT Calculator','Enthalpy Calculator','Entropy Calculator','Fugacity Calculator','Ideal-gas comparison','Two-state process','Graphical Analysis','About the Project','Dashboard']
    for page in pages:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, [e.message for e in at.exception]
        if page=='Graphical Analysis':
            assert len(at.get('plotly_chart'))==10
            at.button(key='FormSubmitter:graph_controls-Generate graphs').click().run()
            assert not at.exception


def test_components_custom_and_invalid_input():
    at=app()
    for name in ['Nitrogen','Carbon dioxide','Propane','Ethane','Custom component']:
        at.selectbox(key='component_choice').set_value(name).run()
        at.button(key='FormSubmitter:state_inputs-Calculate state').click().run()
        assert not at.exception
        assert at.session_state['result']['component']==('Custom gas' if name=='Custom component' else name)
    # Invalid validity limits are rejected while retaining the last successful state.
    before=at.session_state['result']['Z']
    at.number_input(key='mx_Custom component').set_value(100.0)
    at.button(key='FormSubmitter:state_inputs-Calculate state').click().run()
    assert not at.exception and len(at.error)>0
    assert at.session_state['result']['Z']==before


def test_history_and_temperature_range():
    at=app()
    at.number_input[0].set_value(200.0)
    at.button(key='FormSubmitter:state_inputs-Calculate state').click().run()
    assert not at.exception
    assert at.session_state['result']['H_kJ_mol'] is None
    at.sidebar.radio[0].set_value('Enthalpy Calculator').run()
    assert len(at.error)>0 and not at.exception
    assert len(at.session_state['history'])==2
    at.button[1].click().run() if False else None
    # Clear button is a functional session-state mutation.
    next(b for b in at.button if b.label=='Clear history').click().run()
    assert len(at.session_state['history'])==0


def test_process_and_comparison_pages():
    at=app()
    at.sidebar.radio[0].set_value('Ideal-gas comparison').run()
    assert not at.exception and len(at.metric)==3
    at.sidebar.radio[0].set_value('Two-state process').run()
    assert not at.exception
    assert at.session_state['process_result']['initial']['T_K']==400
    at.number_input(key='process_t2').set_value(600.0)
    at.button(key='FormSubmitter:process_inputs-Calculate process').click().run()
    assert not at.exception
    assert at.session_state['process_result']['final']['T_K']==600
    at.number_input(key='process_t2').set_value(200.0)
    at.button(key='FormSubmitter:process_inputs-Calculate process').click().run()
    assert not at.exception and len(at.error)>0
