# Cozy Desk Companion

A small, self-contained Pygame desktop pet prototype for PolyU SD5913 Assignment 3. The project is managed with [uv](https://docs.astral.sh/uv/).

This Stage 1 foundation focuses on the pet's physics and interaction state machine. Later stages can extend the experience.

## Run

```powershell
uv sync
uv run python main.py
```

To check the project without opening a display:

```powershell
uv run python main.py --headless-check
```

## Controls

- Drag the pet with the mouse; release to throw it.
- Press **R** to reset it to the desk.
- Press **Esc** or close the window to quit.
