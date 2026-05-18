# Complete Explanation: What Was Built, What Was Used, and Why

This document explains the full system in plain language: what was implemented, how it works, why each part exists, and what decisions were made.

## 1. Project objective

The system is a local File Integrity Monitoring (FIM) tool designed to:

- monitor file activity in real time
- detect suspicious behavior using anomaly detection
- quarantine risky files quickly
- provide visibility and recovery options to users

The goal is practical early detection and containment, especially for behavior that looks ransomware-like.

## 2. What was built in this project

Implemented features include:

- Real-time monitoring of selected folders
- Detection for create/modify/delete/move events
- Machine-learning anomaly scoring (Isolation Forest)
- Severity levels (`Normal`, `Low`, `Medium`, `Critical`)
- Quarantine and restore workflow
- Alerts in the UI
- Debounce/filtering to reduce noisy temporary file events
- Whitelist support (paths/extensions)
- Activity chart on dashboard
- Model training workflow (Training Mode and manual training)
- Scan Existing Files Now (one-click initial scan)
- Export report files (events CSV, quarantine CSV, summary TXT)
- Reset functionality for clean restarts

## 3. Technology stack used

- Python: core language
- Watchdog: file system event monitoring
- scikit-learn: Isolation Forest model
- SQLite: local persistent event/anomaly storage
- Tkinter + ttk: desktop GUI
- joblib: model persistence (`model.joblib`)

Why this stack:

- lightweight and local-first
- easy to deploy for a student/client demo
- enough capability for real-time monitoring and explainable workflow

## 4. Architecture overview

High-level pipeline:

1. Monitor receives file event from OS.
2. Feature extractor builds numeric feature vector from file behavior.
3. Model predicts normal vs anomaly.
4. Heuristic safety rules run as fallback for obvious risky patterns.
5. Event and decision are logged in database.
6. If risky, responder quarantines file and queues alert.
7. GUI reads DB and displays live status.

## 5. Core modules and why they exist

## 5.1 Monitor

What it does:

- watches configured folders recursively
- handles event types (`created`, `modified`, `deleted`, `moved`)

Why:

- event-driven design is efficient and near real-time
- avoids expensive full-disk rescans by default

## 5.2 Feature extractor

What it does:

- computes behavior features from file and context

Current features include:

- `size_log`
- `entropy`
- `ext_hash`
- `hour_of_day`
- `is_executable`
- `size_change_ratio`
- `mod_frequency`

Why:

- these features capture suspicious patterns common in file attacks
- they are lightweight and work without labeled malware datasets

## 5.3 ML engine (Isolation Forest)

What it does:

- trains on normal baseline data
- predicts anomaly score and verdict during detection

Verdict meanings:

- `1`: normal
- `-1`: anomaly

Why Isolation Forest:

- unsupervised (no malware labels required)
- suitable for outlier detection in mixed behavioral features
- fast enough for local endpoint use

## 5.4 Heuristic fallback layer

What it does:

- catches obvious dangerous patterns (for example high-entropy executable-like files)

Why:

- small or low-variance training sets can weaken ML confidence
- fallback rules improve safety and practical detection reliability

## 5.5 Database layer

What it stores:

- raw events
- snapshots
- anomaly decisions
- quarantine history
- training-sample markers

Why:

- provides audit trail and reproducibility
- powers GUI, reporting, and retraining

## 5.6 Responder and quarantine

What it does:

- isolates suspicious files into quarantine folder
- logs action
- provides restore path in GUI

Why:

- containment reduces blast radius
- restore support handles false positives safely

## 5.7 GUI

Pages:

- Dashboard
- Live Events
- Quarantine
- Settings

Why:

- gives non-technical users operational control and visibility
- supports demonstration and client handover

## 6. Modes and decision logic

## 6.1 Training Mode

Purpose:

- collect clean baseline behavior

Behavior:

- events are captured
- feature snapshots are marked as training samples
- used later by manual training

Why:

- anomaly detection quality depends on what "normal" looks like

## 6.2 Detection Mode

Purpose:

- active protection

Behavior:

- each event gets scored
- severity assigned
- risky events may quarantine and alert

Why:

- separates learning phase from protection phase for better control

## 7. Severity model

Severity represents risk confidence:

- `Normal`: expected behavior
- `Low`: minor deviation
- `Medium`: clear deviation
- `Critical`: highly suspicious behavior

Important note:

- severity means potential threat behavior, not guaranteed malware identity.

## 8. Why "nothing happens" can occur

The monitor is event-driven.

If files do not change, there are no new events to process.

Solutions:

- create/edit/delete files in watched folder
- use `Scan Existing Files Now` for immediate one-time processing of existing files

## 9. What was improved during development and why

Key upgrades and rationale:

- added delete/move handling: full event coverage
- added whitelist: reduce false positives/noise
- added debounce/temp filters: reduce flood events
- added severity display: easier triage
- added chart improvements: clearer trend visibility
- added training sample separation: prevent accidental mixed training data
- added export/report tools: client/audit evidence
- added reset and restore UX: safer operational lifecycle

## 10. Limitations (honest scope)

Current system is:

- local host based
- behavior anomaly focused

Not included:

- malware family classification
- signature database scanning
- cloud/distributed management
- enterprise EDR orchestration

## 11. How to explain this to a client

Use this wording:

- "The system detects suspicious file behavior and assigns severity."
- "It can automatically isolate risky files and allows manual restore."
- "It is an anomaly-based FIM, not a signature antivirus."

Avoid this wording:

- "This confirms the exact malware type" (unless verified by external tools).

## 12. Final value delivered

This project delivers a complete, usable FIM prototype with:

- real-time monitoring
- anomaly detection
- severity-based response
- quarantine and recovery
- report export
- user-friendly operation for non-technical clients

It is suitable for demonstration, controlled endpoint use, and as a strong foundation for future hardening.
