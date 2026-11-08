"""Smith et al., Introduction to Chemical Engineering Thermodynamics, 8e.
Critical constants: Appendix B, Table B.1; Cp: Table C.1 (p. 656).
Cp/R = A + B*T + C*T**2 + D/T**2, T in K. Coefficients below are UNSCALED.
"""
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Component:
    name: str
    tc: float
    pc_bar: float
    omega: float
    cp_a: float
    cp_b: float
    cp_c: float
    cp_d: float
    tmin: float = 298.0
    tmax: float = 1500.0
    source: str = 'Smith, Van Ness, Abbott & Swihart, 8e; App. B and Table C.1'

    def to_dict(self):
        return asdict(self)

COMPONENTS = {
    'Methane': Component('Methane',190.6,45.99,0.012,1.702,9.081e-3,-2.164e-6,0),
    'Nitrogen': Component('Nitrogen',126.2,34.00,0.038,3.280,0.593e-3,0,0.040e5,tmax=2000),
    'Carbon dioxide': Component('Carbon dioxide',304.2,73.83,0.224,5.457,1.045e-3,0,-1.157e5,tmax=2000),
    'Propane': Component('Propane',369.8,42.48,0.152,1.213,28.785e-3,-8.824e-6,0),
    'Ethane': Component('Ethane',305.3,48.72,0.100,1.131,19.225e-3,-5.561e-6,0),
}
