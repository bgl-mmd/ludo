# Project Overview

## Purpose

This project provides a Ludo game simulator and bot framework for the 1405 Programming Competition (Iranian calendar). The competition server is at `https://rbc.sysx.ir`.

The project has two related but distinct parts:

1. **Competition-compatible game model** — faithfully reproduces the game described in the competition specification so bots can be developed and tested against the challenge rules.
2. **Local simulator / AI framework** — runs complete games without the real server, supports deterministic/reproducible games, pluggable bots, statistics collection, replay, and eventually RL training.

## Source of Truth

The competition specification is the authoritative source for:
- Game rules, board layout, token positions
- Movement rules, dice behavior, winning conditions
- Invalid actions, game states
- REST API, request/response formats
- Bot interaction model

Standard Ludo/Mensch rules are **not** authoritative. Where this competition differs, the competition rules win.

## Architecture

The key architectural insight: the bot only knows `Observation` and `Action`. It never touches HTTP or engine internals. A **runner** function owns the game loop and produces observations. In competition mode the runner talks to the server; in simulation mode the runner threads immutable state through pure engine functions. The whole system is **functional**: state is data, logic is functions, and nothing is mutated.

```
                              ┌─────────────────────┐
                              │    Observation       │
                              │  (same format always)│
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │       Bot            │
                              │  BotFn: obs → action │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │      Action          │
                              └──────────┬──────────┘
                                         │
            ┌────────────────────────────┼────────────────────────────┐
            │                            │                            │
┌──────────▼──────────┐   ┌────────────▼────────────┐   ┌──────────▼──────────┐
 │  run_competition()  │   │    run_simulation()      │   │  make_env() closures│
 │  (IO at the edge)   │   │  (pure game loop)        │   │  (RL training)      │
 │                     │   │                          │   │                     │
 │  get_board()   ────►│   │  new_game(config)        │   │  new_game(config)   │
 │  parse_board()      │   │  roll_dice(state, rng)   │   │  roll_dice(s, rng)  │
 │  bot(obs)           │   │  apply_action(s, a, cfg) │   │  apply_action(...)  │
 │  make_move()  ◄──── │   │  bot(obs)                │   │  bot(obs)           │
 └─────────────────────┘   └──────────────────────────┘   └─────────────────────┘
```

### What the runner owns

The runner is responsible for the full game loop:

1. **Game setup** — initialize state (or register with server)
2. **Dice rolls** — either call the engine or receive from server
3. **Turn management** — track whose turn it is, handle extra turns
4. **Observation building** — translate game state into the bot's view
5. **Action routing** — pass bot's action to engine or server
6. **Win detection** — check after every move
7. **Game termination** — detect and report final result

In competition mode, the server handles items 2–6. The runner just translates between REST and the bot interface.

In simulation mode, the engine functions handle items 2–6. The runner composes those pure functions, threading immutable `GameState` and an event log through the loop and returning `(result, history)`.

### What the bot knows

The bot receives:
- Token positions (player-relative)
- Dice value
- Legal actions
- Game state
- Turn information

The bot returns:
- Exactly one action from the legal actions list

The bot never knows:
- Whether it's talking to a real server or a local engine
- How dice are rolled
- How turns are managed
- The global board coordinates

## Key Design Principles

1. **Bot interface is uniform.** Same `Observation` → `Action` contract whether against the server or the simulator.
2. **Runner owns the game loop.** A runner function composes the engine functions (or the server) and threads state through the loop.
3. **Engine is a library of pure functions.** The engine must faithfully reproduce the server's behavior so the same bot works in both modes.
4. **State is immutable data.** `GameState` is a frozen dataclass; every transition returns a new state.
5. **Coordinate conversion is centralized.** Global ↔ player-relative conversion lives in one place.
6. **Deterministic by default.** Randomness is seeded for reproducibility.
7. **Errors are detected, not bypassed.** The engine classifies every action as legal, illegal, or no-action.

## Directory Structure

```
spec/
├── 00-overview.md            ← this file
├── 01-game-rules.md          ← exact game rules
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
