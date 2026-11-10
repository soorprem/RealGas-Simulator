"""Set up RealGas locally and keep a troubleshooting log."""
from pathlib import Path
import hashlib
import subprocess
import sys
import traceback
import venv

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "setup_log.txt"

def say(message):
    print(message, flush=True)
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(message + "\n")

def execute(command):
    with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True,
                          encoding="utf-8", errors="replace", bufsize=1) as process:
        try:
            for line in process.stdout:
                print(line, end="", flush=True)
                with LOG.open("a", encoding="utf-8") as stream:
                    stream.write(line)
            result = process.wait()
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
            raise
    if result:
        raise subprocess.CalledProcessError(result, command)

def main():
    LOG.write_text("RealGas Simulator launcher\n", encoding="utf-8")
    say("Python: " + sys.version.split()[0])
    say("Project folder: " + str(ROOT))
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11 or newer is required. Python 3.12 is recommended.")
    for filename in ("app.py", "ui.py", "requirements.txt", "eos_model.py", "report.pdf"):
        if not (ROOT / filename).is_file():
            raise FileNotFoundError("Extract ALL files first. Missing: " + filename)
    if "--check" in sys.argv:
        say("Launcher check passed: Python and project files are available.")
        return 0
    environment = ROOT / ".venv"
    interpreter = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not interpreter.is_file():
        say("Step 1/3: creating a private Python environment...")
        venv.EnvBuilder(with_pip=True).create(environment)
    requirements = ROOT / "requirements.txt"
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = environment / ".realgas-requirements"
    probe = subprocess.run([str(interpreter), "-c",
        "import streamlit, numpy, pandas, scipy, plotly, reportlab"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if probe.returncode or not marker.exists() or marker.read_text().strip() != fingerprint:
        say("Step 2/3: installing packages. Keep this window open; Internet is required.")
        execute([str(interpreter), "-u", "-m", "pip", "install", "-r", str(requirements)])
        marker.write_text(fingerprint)
    else:
        say("Step 2/3: packages are already installed.")
    say("Step 3/3: starting the website. Keep this terminal open.")
    say("Open the Local URL printed below if the browser does not open automatically.")
    execute([str(interpreter), "-u", "-m", "streamlit", "run", str(ROOT / "app.py"),
             "--server.headless=false", "--browser.gatherUsageStats=false"])
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nRealGas stopped.", flush=True)
    except Exception as exc:
        try:
            say("\nSETUP ERROR: " + str(exc))
            with LOG.open("a", encoding="utf-8") as stream:
                traceback.print_exc(file=stream)
        except OSError:
            print("Could not write the setup log. Extract to a writable folder.")
        print("\nRead setup_log.txt in this folder for the exact error.")
        print("For immediate use without installing Python, open OPEN_WEBSITE.html.")
        raise SystemExit(1)
