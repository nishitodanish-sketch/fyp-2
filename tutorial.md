# FIM System Full Tutorial (From Zero)

This is a complete beginner guide for your client.
Follow it in order from installation to testing.

## 1. What this system is

This application is an **Anomaly-Based File Integrity Monitoring (FIM)** system.

It does:

- monitor selected folders in real time
- detect suspicious file behavior
- show severity (`Normal`, `Low`, `Medium`, `Critical`)
- quarantine suspicious files
- allow restore from quarantine
- export CSV reports

It does **not** do signature-based antivirus identification.
It reports **potential threats** based on behavior.

## 2. Prerequisites

You need:

- terminal access (macOS or Windows)
- Python 3.13+ (recommended)
- project folder extracted locally

Example project path:

```bash
/Users/user/Downloads/FYP2
```

Windows example project path:

```text
C:\Users\YourName\Downloads\FYP2
```

## 3. First-time installation

Use the section that matches your operating system.

### 3.1 macOS setup

```bash
cd /Users/user/Downloads/FYP2
python3 -m venv .venv
source .venv/bin/activate
pip install watchdog scikit-learn joblib numpy scipy pandas
brew install python-tk@3.13
python3 -m venv .venv
source .venv/bin/activate
pip install watchdog scikit-learn joblib numpy scipy pandas
```

If Tkinter GUI fails on macOS, install Tk support:

```bash
brew install python-tk@3.13
```

### 3.2 Windows setup (PowerShell)

```powershell
cd C:\Users\YourName\Downloads\FYP2
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install watchdog scikit-learn joblib numpy scipy pandas
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3.3 Windows setup (Command Prompt / CMD)

```cmd
cd C:\Users\YourName\Downloads\FYP2
py -m venv .venv
.\.venv\Scripts\activate.bat
pip install watchdog scikit-learn joblib numpy scipy pandas
```

## 4. Run the application

### 4.1 macOS

```bash
cd /Users/user/Downloads/FYP2
.venv/bin/python3 -m fim_system.main
```

### 4.2 Windows (PowerShell or CMD)

```powershell
cd C:\Users\YourName\Downloads\FYP2
py -m fim_system.main
```

You should see the app window with pages:

- Dashboard
- Live Events
- Quarantine
- Settings

## 5. Full first-time setup (required)

## 5.1 Add monitored folder

1. Open `Settings`.
2. Click `Add Folder`.
3. Select folder(s) you want to protect.

For testing, use:

```bash
/Users/user/Downloads/FYP2/test_monitored
```

Windows equivalent example:

```text
C:\Users\YourName\Downloads\FYP2\test_monitored
```

## 5.2 Build baseline (Training Mode)

1. Open `Dashboard`.
2. Select `Training Mode (Collect Normal Data)`.
3. Click `Start Monitoring`.
4. Provide the system with normal files to learn from. You have two options:

**Option A: Train on data already on the computer (Recommended)**
Simply click the **`Scan Existing Files Now`** button. The system will safely crawl through all existing files in your monitored folders and extract their features to build its baseline.

**Option B: Create new test files manually**
```bash
cd /Users/user/Downloads/FYP2
echo "normal note 1" > test_monitored/normal1.txt
echo "normal note 2" > test_monitored/normal2.txt
echo "normal note 3" > test_monitored/normal3.txt
```

Windows PowerShell equivalent:

```powershell
cd C:\Users\YourName\Downloads\FYP2
Set-Content -Path .\test_monitored\normal1.txt -Value "normal note 1"
Set-Content -Path .\test_monitored\normal2.txt -Value "normal note 2"
Set-Content -Path .\test_monitored\normal3.txt -Value "normal note 3"
```

5. Click `Train Model (Current DB)`.
6. Wait for success popup/status.

Notes:

- `Training Samples` should increase.
- `Model: Trained (...)` should appear.

## 5.3 Switch to Detection Mode

1. Select `Detection Mode (Flag Anomalies)`.
2. Click `Stop Monitoring`.
3. Click `Start Monitoring` again.

Now active protection is ON.

## 6. How to test using attack simulation (the exact flow)

This is the same testing approach we used during development.

1. Keep app running in `Detection Mode`.
2. Ensure watched folder is `test_monitored`.
3. Run simulation script:

```bash
cd /Users/user/Downloads/FYP2
python3 test_attack_simulation.py
```

Windows equivalent:

```powershell
cd C:\Users\YourName\Downloads\FYP2
py test_attack_simulation.py
```

The script creates safe test files that mimic suspicious behavior.

Expected in app:

- `Total Events` increases
- `Anomalies Detected` increases
- Live Events shows severity (some `Critical`)
- Quarantine receives suspicious files

## 7. Test on a real client folder

If client wants to monitor a real folder (example: `work`):

1. Add `work` folder in `Settings`.
2. Go to `Dashboard` -> `Detection Mode` -> `Start Monitoring`.
3. Trigger events in that folder:
   - create/edit/delete files
4. Check `Live Events` and `Quarantine`.

Important:

- This system is event-based.
- If no file activity happens, no new detection appears.

If needed, click `Scan Existing Files Now` to analyze current files immediately.

## 8. Dashboard buttons explained

- `Start Monitoring`: start watchdog monitor on selected folders
- `Stop Monitoring`: stop monitor
- `Train Model (Current DB)`: train model using collected Training Mode samples
- `Scan Existing Files Now`: process all existing files in monitored folders now
- `Export Report CSV`: export events/quarantine/summary files for reporting

## 9. Live Events explained

Each row shows:

- ID
- Event type (`created`, `modified`, `moved`, `deleted`)
- File path
- Timestamp
- Severity

Color guidance:

- green: Normal
- yellow/orange: Low/Medium
- red/dark red: Critical

All actions are logged.

### 10.1 Manual Access to Quarantine Folder (Windows)
The quarantine folder is hidden and locked for safety. To see it manually in File Explorer:
1. Open PowerShell in the project root.
2. Run the command:
   ```powershell
   attrib -h -s fim_system/quarantine
   ```
3. The folder will now be visible. To hide it again, use `+h +s`.
**Note**: Files inside are encrypted (`.locked`) and cannot be executed even if the folder is visible.

## 11. Exporting client report files

From `Dashboard` click `Export Report CSV`.

Generated files:

- events CSV
- quarantine CSV
- summary TXT (anomaly rate, latency, totals)

Use these as evidence for FYP/client report.

## 12. Troubleshooting

### Problem: app does not open

Try:

```bash
cd /Users/user/Downloads/FYP2
.venv/bin/python3 -m fim_system.main
```

Windows equivalent:

```powershell
cd C:\Users\YourName\Downloads\FYP2
py -m fim_system.main
```

If Tkinter error appears, install:

```bash
brew install python-tk@3.13
```

### Problem: "Nothing happens"

Check:

- folder was added in `Settings`
- monitor is started
- file activity happens inside that same folder
- use `Scan Existing Files Now`

### Problem: all events are Normal

Check:

- collected baseline in `Training Mode`
- clicked `Train Model (Current DB)`
- switched to `Detection Mode`

### Problem: wrong file quarantined

Use `Quarantine` -> `Restore Selected`.

## 13. Suggested client workflow (daily)

1. Start app
2. Verify watched folder list
3. Start Monitoring in Detection Mode
4. Check Dashboard/Live Events periodically
5. Review Quarantine before restore
6. Export report weekly

## 14. Safety and communication note

Correct wording for client communication:

- "Potential threat detected"
- "Suspicious file behavior detected"

Avoid saying:

- "Confirmed virus" unless verified by external antivirus/forensics.
