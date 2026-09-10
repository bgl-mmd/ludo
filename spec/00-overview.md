# Project Overview

## Purpose

This project provides a Ludo game simulator and bot framework for the 1405 Programming Competition (Iranian calendar). The competition server is at `https://rbc.sysx.ir`.

The project has two related but distinct parts:

1. **Competition-compatible game model** — faithfully reproduces the game described in the competition PDF so bots can be developed and tested against the challenge rules.
2. **Local simulator / AI framework** — runs complete games without the real server, supports deterministic/reproducible games, pluggable bots, statistics collection, replay, and eventually RL training.

## Source of Truth

The competition PDF (`document-v2.pdf`) is the authoritative source for:
- Game rules, board layout, token positions
- Movement rules, dice behavior, winning conditions
- Invalid actions, game states
- REST API, request/response formats
- Bot interaction model

Standard Ludo/Mensch rules are **not** authoritative. Where this competition differs, the competition rules win.

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│                  Bot / Agent                     │
│  (Random, Greedy, MCTS, RL, etc.)               │
│  Receives: Observation + Legal Actions           │
│  Returns:  Action                                │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              Game Engine (Core)                  │
│  - Authoritative game state                     │
│  - Rules enforcement                            │
│  - Legal action generation                      │
│  - Turn management, dice, win detection         │
│  - Coordinate conversion (global ↔ player-rel)  │
│  - No HTTP dependency                           │
└───────┬──────────────────────────┬──────────────┘
        │                          │
┌───────▼──────────┐  ┌───────────▼──────────────┐
│  Local Simulator │  │  Competition REST Adapter │
│  (in-process)    │  │  (HTTP client)            │
│  - Run N games   │  │  - Login / Board / Move   │
│  - Statistics    │  │  - Callback handler       │
│  - Replay        │  │  - Token auth             │
│  - Deterministic │  │                           │
└──────────────────┘  └───────────────────────────┘
```

## Key Design Principles

1. **Engine has no HTTP dependency.** The core engine is a pure function of state + action → new state.
2. **Bots are plugins.** A bot receives an observation and returns an action. It cannot mutate game state.
3. **Coordinate conversion is centralized.** Global ↔ player-relative conversion lives in one place.
4. **Competition protocol is an adapter.** The REST API layer wraps the engine for server communication.
5. **Deterministic by default.** Randomness is seeded for reproducibility.
6. **Errors are detected, not bypassed.** The engine classifies every action as legal, illegal, or no-action.

## Directory Structure

```
spec/
├── 00-overview.md            ← this file
├── 01-game-rules.md          ← exact rules from the PDF
├── 02-board-coordinates.md   ← board model and coordinate conversion
├── 03-state-machine.md       ← game lifecycle and states
├── 04-action-model.md        ← action semantics and Move(0)
├── 05-engine-architecture.md ← engine design
├── 06-bot-interface.md       ← bot interface and observation model
├── 07-simulation.md          ← simulation and RL architecture
├── 08-competition-protocol.md← REST API specification
├── 09-testing.md             ← testing strategy
└── 10-open-questions.md      ← ambiguities and unresolved items
```
