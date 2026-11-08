# Submitting RealGas Simulator

## Recommended submission

Follow the course portal's prescribed file types and naming rules. The assignment
requires a complete program and a report of at most four pages, so submit BOTH:

1. `report.pdf`: the four-page technical report.
2. `RealGas_Simulator.zip`: the complete runnable project, including Python source,
   requirements, README, theory, sample inputs/outputs, tests and screenshots.

If only one upload is allowed, upload the ZIP, which already contains report.pdf.
Rename your final copy according to the course instructions, for example
`YourEntryNumber_RealGas_Simulator.zip`. Replace the example with your actual
entry number. Add your name, entry number, course code and partner details (if
applicable) to the report before submission; keep the final report within four pages.
Fill in `student_details.json`, then run `python build_report.py`. The editable report source is `build_report.py`.

Do not submit only a screenshot, only the app.py file, or only the hosted link.
The program uses supporting modules. The hosted site is currently owner-private,
so a professor cannot necessarily open it from your account's URL. The full local
project is self-contained after installing dependencies. No sharing permissions
have been changed. Do not include .venv, node_modules, .git or credentials.

## Before uploading

- Extract the final ZIP into a fresh folder and follow README.md.
- Install with `python -m pip install -r requirements.txt`.
- Run with `python -m streamlit run app.py` (or `streamlit run app.py`).
- Try the methane sample and compare with sample_output.csv.
- Check both new pages and all ten interactive plots.
- Confirm report.pdf still has at most four pages after adding your details.
- Follow the course's rules for collaboration, attribution and AI assistance.
  Acknowledge assistance where required and be prepared to explain the code.
- Upload before the stated deadline of 10 November 2026, using the portal's
  specified cutoff time. No exact cutoff time was supplied in this conversation.

## Five-minute demonstration

1. **Launch and scope (30 s):** explain pure-component Peng–Robinson, inputs and units.
2. **PVT (45 s):** methane at 400 K, 50 bar; show Z and volume. Explain root selection.
3. **Ideal comparison (45 s):** compare ideal and PR volumes; reduce pressure to
   0.000001 bar and show the ideal limit.
4. **Thermal properties and fugacity (60 s):** show ideal + residual H/S and f=phi P.
   Explain the ideal-gas reference convention and analytical attraction derivative.
5. **Two-state example (60 s):** methane 400 K/50 bar to 500 K/20 bar, both stable.
   Explain deltaH=H2-H1 and deltaS=S2-S1; heat/work need a specified process path.
6. **Plots and validation (60 s):** show P–V isotherms and signed volume deviation;
   distinguish an unstable EOS segment from an equilibrium two-phase plateau.
   Show the executed validation table and download a CSV.

If the course allows supplementary material, a short screen recording can make
review easier, but it is not a substitute for the required source and report.
Install dependencies and test the local version ahead of your demonstration.
