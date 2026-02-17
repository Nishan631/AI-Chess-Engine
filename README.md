# AI Chess Engine (Python + Pygame)

An interactive AI-powered chess game built with Python and Pygame, featuring a custom chess engine, Minimax + Alpha-Beta search, multiple AI difficulty levels, advanced draw rules, SAN move logging, and SQLite-backed player stats.

## Features

- Full chess gameplay with legal move validation
- AI opponent with difficulty levels:
  - `Beginner`
  - `Intermediate`
  - `Advanced`
- Search engine:
  - Minimax
  - Alpha-Beta pruning
  - Iterative deepening + time-limited search
  - Move ordering heuristics
- Advanced chess rules:
  - Castling
  - En passant
  - Pawn promotion
  - Threefold repetition
  - 50-move rule
  - Insufficient material draw detection
- SAN move log (Standard Algebraic Notation)
- Interactive UI:
  - Board flip
  - Last-move highlight
  - Legal-move indicators
  - Captured pieces panel
  - In-app debug/status strip
- Persistent storage with SQLite:
  - Player stats
  - Match history
  - Leaderboard
  - Rich game metadata (mode, result details, AI level/depth, duration, draw reason, etc.)

## Tech Stack

- Python 3.x
- Pygame
- SQLite3

## Project Structure

- `main.py` - Pygame UI, game loop, interaction handling, persistence wiring
- `ChessEngine.py` - Core chess logic and legal move generation
- `ai_engine.py` - AI search/evaluation logic
- `chess_db.py` - Database schema, migrations, and persistence APIs
- `images/` - Piece assets
- `requirements.txt` - Python dependencies

## Setup

### 1) Clone and open project

```bash
git clone <your-repo-url>
cd AI_Chess_Engine
```

### 2) Create and activate virtual environment (recommended)

#### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

## Run

### Windows (recommended)

```powershell
py main.py
```

### macOS/Linux

```bash
python3 main.py
```

## Controls

- `Mouse Click` - Select and move pieces
- `F` - Flip board
- `Z` - Undo move
- `R` - Restart game
- `M` - Toggle move log view
- `D` - Toggle debug/status strip
- `Esc` - Exit menu screens

## Database

On first run, the app creates/updates `chess_data.db` automatically.

Stored data includes:
- players and cumulative stats
- game history
- mode/status/result metadata
- draw reason for drawn games
- AI level/depth, move count, and game duration

## Troubleshooting

- If `pygame` import fails, ensure the same interpreter is used for install and run:
  - install with `py -m pip install -r requirements.txt`
  - run with `py main.py`
- Advanced AI mode is intentionally slower due to deeper search.

## Value of this project

This project demonstrates:
- algorithmic problem solving (game tree search)
- stateful systems design (engine + UI + persistence)
- software quality improvements (rule correctness, migration-safe schema updates, debugging support)
- end-to-end product thinking (gameplay, UX, and data features)
