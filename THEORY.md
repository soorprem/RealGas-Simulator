# RealGas Simulator: equations and reference convention

All properties are molar. Internal units are Pa, K, m³/mol, J/mol, J/(mol K).
Input pressure in bar is multiplied by 100000. R = 8.31446261815324 J/(mol K).
The application was built from scratch; no prior source program was supplied.

## Peng–Robinson model

P = RT/(v-b) - a(T)/(v²+2bv-b²).

Tr = T/Tc; Pr = P/Pc; kappa = 0.37464 + 1.54226 omega - 0.26992 omega².
Let g = 1 + kappa(1-sqrt(Tr)), alpha = g²,
a_c = Omega_A R² Tc²/Pc, a(T) = a_c alpha,
b = Omega_B R Tc/Pc, a_T = da/dT = -a_c kappa g/sqrt(T Tc).

Unrounded critical-constraint constants: Omega_A = 0.4572355289213822,
Omega_B = 0.07779607390388846. These are the NIST teqp canonical_PR constants,
which reduce to textbook 0.45724 and 0.07780 on rounding.
Original PR alpha is used for all preset fluids. No SRK expressions are used.
Manual omega is restricted to [-0.5, 0.5]; g must be positive.

A = aP/(RT)²; B = bP/(RT).
Solve Z³ + (B-1)Z² + (A-2B-3B²)Z - AB+B²+B³ = 0.
Admissible roots must be real and Z>B. v = ZRT/P.
The smallest and largest roots are liquid-like and vapour-like when three
admissible roots exist. The middle root has positive dP/dv and is unstable.
Stable selects minimum ln(phi) among roots with nonpositive dP/dv.
A single root does not by itself label a fluid liquid or vapour.
Forced branches may be metastable. Saturation requires equal outer fugacities;
T and P do not specify phase fraction. No two-phase mixture properties are calculated.

## Derivation of departure functions

Let L = ln[(v+(1+sqrt(2))b)/(v+(1-sqrt(2))b)], equivalently
ln[(Z+(1+sqrt(2))B)/(Z+(1-sqrt(2))B)].

Integrating the pressure EOS from the zero-density ideal-gas limit gives
residual Helmholtz energy at the SAME T and v:

A^R_(T,v) = -RT ln(1-b/v) - a L/(2 sqrt(2) b).

At fixed v, b and L are temperature independent. Therefore
S^R_(T,v) = -(dA^R/dT)_v = R ln(1-b/v) + a_T L/(2 sqrt(2)b),
U^R = A^R + T S^R_(T,v) = (T a_T-a)L/(2 sqrt(2)b).

Since H = U+Pv and H_ideal = U_ideal+RT,
H^R = RT(Z-1) + (T a_T-a)L/(2 sqrt(2)b).

The ideal entropy at the same T and P is the ideal entropy at the same
T and v MINUS R ln Z. Thus convert the above same-density departure by
ADDING R ln Z:
S^R_(T,P) = R ln(Z-B) + a_T L/(2 sqrt(2)b).

G^R_(T,P) = H^R-T S^R = RT ln(phi), giving
ln(phi) = Z-1-ln(Z-B)-a L/(2 sqrt(2)bRT).
Pure-component fugacity f = phi P; use the same pressure units for f and P.
Fugacity defines chemical potential: mu = mu°(T)+RT ln(f/P°).

At low P on the gas branch, Z and phi approach 1, f/P approaches 1,
and H^R and S^R approach 0. These limits need not apply to a forced liquid branch.
The implementation evaluates L with log1p to retain low-pressure precision.

## Ideal-gas heat capacities and reference

Cp_ideal/R = A_c+B_c T+C_c T²+D_c/T² (T in kelvin).
Suffix c distinguishes Cp coefficients from dimensionless EOS A and B.
Heat-capacity coefficients are unscaled in component_data.py.
Dimensions: A_c [-], B_c [K^-1], C_c [K^-2], D_c [K²].

H_ideal = R[A_c(T-T0)+B_c(T²-T0²)/2+C_c(T³-T0³)/3+D_c(1/T0-1/T)].
S_ideal = R[A_c ln(T/T0)+B_c(T-T0)+C_c(T²-T0²)/2
          +D_c(1/T0²-1/T²)/2-ln(P/P0)].

H = H_ideal+H^R; S = S_ideal+S^R.
H_ideal(T0)=0 and S_ideal(T0,P0)=0. There is no heat of formation and
no absolute third-law entropy. Real-fluid H and S need NOT be zero at T0,P0.
To obtain changes between two real states on a common datum, subtract their totals.
Changing P0 shifts entropy by a constant and does not change enthalpy.
Total thermal properties are blocked unless the entire integration path lies
inside the declared Cp validity range and Cp is positive along that path.
EOS departures remain available outside the Cp interval.

## Data provenance

Smith, Van Ness, Abbott and Swihart, Introduction to Chemical Engineering
Thermodynamics, 8th edition, McGraw-Hill, 2018 (uploaded Book.pdf):
critical constants and omega, Appendix B, Table B.1; ideal Cp, Appendix C,
Table C.1, printed page 656. EOS and residual-property discussion: Chapters 3 and 13.

| Fluid | Tc (K) | Pc (bar) | omega | A_c | B_c (1/K) | C_c (1/K²) | D_c (K²) | Cp interval (K) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Methane |190.6|45.99|0.012|1.702|0.009081|-0.000002164|0|298–1500|
| Nitrogen |126.2|34.00|0.038|3.280|0.000593|0|4000|298–2000|
| Carbon dioxide |304.2|73.83|0.224|5.457|0.001045|0|-115700|298–2000|
| Propane |369.8|42.48|0.152|1.213|0.028785|-0.000008824|0|298–1500|
| Ethane |305.3|48.72|0.100|1.131|0.019225|-0.000005561|0|298–1500|

NIST teqp constants and cubic Helmholtz form:
https://pages.nist.gov/teqp-docs/en/main/models/cubics.html

Independent implementation: CoolProp 8.0.0 PR backend:
https://coolprop.org/coolprop/Cubics.html
Custom fluids register the SAME textbook Tc/Pc/omega to isolate implementation
error. CoolProp smolar_residual is a same-T,density residual; the comparison
adds R ln Z to obtain same-T,P entropy departure. The required mass entry for
these custom fluids is a placeholder and is never used: comparisons are molar.
Additional HEOS comparisons quantify model discrepancy, not implementation error.
No computed value is labelled experimental data.

## Model limits

Pure homogeneous fluids only, with conventional PR alpha. No mixtures, solids,
association models, reactions, transport properties or phase quality. Liquid
densities and near-critical results require care; root conditioning deteriorates
near critical/spinodal states. Numerical input domain 50–2500 K, 10^-6–2000 bar
is a software guard, not an experimentally validated operating envelope. The
preset Cp correlations have their own, narrower validity intervals.

## Two-state extension and ideal-gas comparisons

For the same component on a common ideal-gas datum:
Delta H = integral(T1,T2) Cp_ideal dT + H2^R-H1^R.
Delta S = integral(T1,T2) Cp_ideal/T dT - R ln(P2/P1) + S2^R-S1^R.
Delta v = R(Z2 T2/P2 - Z1 T1/P1).
The arbitrary reference constants cancel in these changes. Initial and final
roots can be chosen independently; the endpoints specify no process path and
no phase fraction. The module therefore reports no heat, work or entropy generation.

At equal T and P, v_ideal=RT/P, Z_ideal=phi_ideal=1 and f_ideal=P.
The signed percent volume deviation is 100(vPR/videal-1)=100(Z-1).
Relative percentage errors in H/S are omitted because they depend on the datum.

Three new graphs supplement the original seven: (1) ideal/PR volume versus P,
(2) signed percent volume deviation versus P, and (3) P–V isotherms at three
editable temperatures (default 0.85 Tc, Tc and 1.2 Tc). Isotherms directly evaluate
the same pressure EOS. Dotted PR segments have positive dP/dv and are unstable;
solid segments satisfy dP/dv<=0 but need not be globally stable. A subcritical
homogeneous EOS loop is not an equilibrium two-phase plateau. Negative raw
pressures remain in CSV data but the graph displays nonnegative pressure.
