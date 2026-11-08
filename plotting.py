"""Sweep calculations include gaps instead of silently hiding failures."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pvt_calculations import calculate,flat_result

PLOTS=[('Z','Compressibility factor','-'),('phi','Fugacity coefficient','-'),('fugacity_bar','Fugacity','bar'),('H_res_J_mol','Residual enthalpy','J/mol'),('S_res_J_molK','Residual entropy','J/(mol K)')]


def sweep(c,T,P,tref,pref,phase,pmin,pmax,tmin,tmax,n=90):
    rows=[]
    for variable,grid in [('P',np.geomspace(pmin,pmax,n)),('T',np.linspace(tmin,tmax,n))]:
        for x in grid:
            tt,pp=(T,float(x)) if variable=='P' else (float(x),P)
            try:
                s=calculate(c,tt,pp,tref,pref,phase)
                rows.append(dict(sweep=variable,**flat_result(s)))
            except (ValueError,OverflowError,FloatingPointError) as exc:
                rows.append(dict(sweep=variable,T_K=tt,P_bar=pp,thermal_error=str(exc)))
    return pd.DataFrame(rows)


def figure(df,x,y,title,unit,branch):
    f=go.Figure(go.Scatter(x=df[x],y=df[y],mode='lines',name=f'PR · {branch}',connectgaps=False,line=dict(color='#087f8c',width=3)))
    f.update_layout(title=title,xaxis_title='Pressure (bar)' if x=='P_bar' else 'Temperature (K)',yaxis_title=f'{title} ({unit})',template='plotly_white',height=340,margin=dict(l=25,r=25,t=55,b=45),legend=dict(orientation='h',y=1.12),showlegend=True)
    f.update_xaxes(showgrid=True);f.update_yaxes(showgrid=True)
    return f


def comparison_figures(df):
    """Two added pressure plots on the exact same sampled state rows."""
    from eos_model import R
    data=df[df.sweep=='P'].copy()
    data['Ideal_volume_L_mol']=R*data.T_K/data.P_bar/100
    data['PR_volume_L_mol']=1000*data.volume_m3_mol
    data['Volume_deviation_percent']=100*(data.Z-1)
    f=go.Figure()
    for y,label,color,dash in [('Ideal_volume_L_mol','Ideal gas','#788b9b','dash'),('PR_volume_L_mol','Peng–Robinson','#087f8c','solid')]:
        f.add_scatter(x=data.P_bar,y=data[y],mode='lines',name=label,connectgaps=False,line=dict(color=color,dash=dash))
    f.update_layout(title='Ideal and PR molar volume',xaxis_title='Pressure (bar)',yaxis_title='Molar volume (L/mol)',template='plotly_white',height=360,legend=dict(orientation='h',y=1.15))
    f.update_yaxes(type='log')
    g=go.Figure(go.Scatter(x=data.P_bar,y=data.Volume_deviation_percent,mode='lines',name='100(Z − 1)',connectgaps=False,line=dict(color='#087f8c')))
    g.add_hline(y=0,line_dash='dash',line_color='#788b9b')
    g.update_layout(title='Signed molar-volume deviation from ideal',xaxis_title='Pressure (bar)',yaxis_title='100(vPR − vig)/vig (%)',template='plotly_white',height=360,showlegend=True)
    return f,g,data


def isotherms(c,temperatures,vmin_L,vmax_L,pmax_bar=150,n=180):
    """Raw homogeneous PR P(v,T) curves, NOT an equilibrium two-phase plateau."""
    from eos_model import R,parameters
    import math
    if not all(math.isfinite(x) for x in (*temperatures,vmin_L,vmax_L,pmax_bar)):
        raise ValueError('Isotherm controls must be finite.')
    b=parameters(c,float(temperatures[0]),1).b
    if not b*1000<vmin_L<vmax_L or pmax_bar<=0:
        raise ValueError(f'Isotherm volumes must satisfy b = {b*1000:.6g} L/mol < minimum < maximum.')
    volume=np.geomspace(vmin_L/1000,vmax_L/1000,n)
    rows=[];f=go.Figure()
    for T,color in zip(temperatures,['#087f8c','#c77931','#6558a6']):
        e=parameters(c,float(T),1)
        denominator=volume**2+2*e.b*volume-e.b**2
        p=(R*T/(volume-e.b)-e.a/denominator)/1e5
        ideal=R*T/volume/1e5
        slope=-R*T/(volume-e.b)**2+e.a*(2*volume+2*e.b)/denominator**2
        stable=slope<=0
        for arr,name,dash,visible in [(np.where(stable,p,np.nan),'PR','solid',True),
                                      (np.where(~stable,p,np.nan),'PR unstable','dot',True),
                                      (ideal,'Ideal','dash','legendonly')]:
            f.add_scatter(x=volume*1000,y=arr,mode='lines',name=f'{T:g} K · {name}',connectgaps=False,visible=visible,line=dict(color=color,dash=dash))
        rows.extend(dict(T_K=float(T),volume_L_mol=float(v*1000),PR_pressure_bar=float(pp),Ideal_pressure_bar=float(ii),mechanically_stable=bool(ok))
                    for v,pp,ii,ok in zip(volume,p,ideal,stable))
    f.update_layout(title=f'P–V isotherms · {c.name}',xaxis_title='Molar volume (L/mol)',yaxis_title='Pressure (bar)',template='plotly_white',height=540,legend=dict(orientation='h',y=-.28,yanchor='top',font=dict(size=10)),margin=dict(t=60,b=130))
    f.update_xaxes(type='log',showgrid=True)
    f.update_yaxes(range=[0,pmax_bar],showgrid=True)
    return f,pd.DataFrame(rows)
