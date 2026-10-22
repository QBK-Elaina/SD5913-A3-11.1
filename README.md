# Cozy Desk Companion

A self-contained Pygame desktop-pet prototype for PolyU SD5913 Assignment 3, managed with [uv](https://docs.astral.sh/uv/). It is intended as a light, playful companion for students taking a short study break. The scene is a cozy study desk with a procedural cat-eared chibi companion and a live analog wall clock.

## Features

- **Autonomous behavior:** when left alone, the pet cycles through idle, walking, resting, napping, grooming, and looking around. It chooses actions on its own, and low energy makes naps more likely; naps restore energy.
- **Tap to cheer:** click the pet for a happy bounce, floating hearts, and a short message. A brief cooldown prevents rapid repeat taps from spamming the response; the pet explains when it is still cooling down.
- **Interactive physics:** drag and throw the pet with the mouse. It follows the cursor while grabbed, inherits mouse velocity on release, falls under gravity, bounces softly on the desk, and stays inside the window.
- **Procedural animation and art:** all scene and character shapes are drawn by Pygame, so no external image assets are needed. Expressions and poses vary by action.
- **Live wall clock:** a hanging analog clock in the background shows the computer's local time, including seconds.

## Requirements

- Python 3.10 or newer
- `uv`

## Run

From the project directory:

```powershell
uv sync
uv run python main.py
```

If your environment cannot access uv's default cache directory, use a project-local cache:

```powershell
$env:UV_CACHE_DIR = ".uv-cache"
uv sync
uv run python main.py
```

## Controls

- **Click the pet** to make it cheer. Wait for the brief cooldown before tapping again.
- **Click and drag the pet** to pick it up and move it; release to throw it.
- **R** resets the pet to the desk and clears its current interaction feedback.
- **Esc** or closing the window quits the program.

## Headless verification

Run the smoke test without opening the interactive window:

```powershell
uv run python main.py --headless-check
```

The check exercises imports, drag-and-throw physics, bounds, autonomous pose drawing, the wall-clock/background rendering, and reset behavior.
