# The Last Crusade - V0.5

## 🎮 Game Overview
**The Last Crusade** is a fast-paced 2D survival game where players must keep leveling up by defeating enemies and surviving for as long as possible. The longer you survive, the higher your score. A **Leaderboard** system (in progress) will track and rank players based on their survival time and performance.

> This game is designed for short and exciting play sessions — perfect for quick gaming during breaks!

---

## 🎯 Game Objective
- Survive incoming waves of enemies.
- Level up by defeating enemies.
- Try to stay alive long enough to conquer the final stage.
- Your goal: **Beat the final challenge or die trying.**

---

## 🧩 Key Features - V0.5
- ⚔️ **Melee and Ranged Combat:** Choose to attack up close or from a distance.
- 🧠 **Enemy AI:** Enemies track the player and launch attacks intelligently.
- 🔥 **Death Animation & Delay:** Player death triggers a one-time animation before ending the game.
- 🗺️ **Tiled Map Integration:** Game uses a `.tmx` map file for world design.
- 🏆 **Leaderboard (coming soon):** Tracks top survivors.
- ⚡ **Quick Play Loop:** Designed for fast-paced gameplay and replayability.

---

## 🎮 Controls

| Action              | Control           |
|---------------------|-------------------|
| Move Up             | `W` / `↑`         |
| Move Down           | `S` / `↓`         |
| Move Left           | `A` / `←`         |
| Move Right          | `D` / `→`         |
| Melee Attack        | Left Mouse Click  |
| Ranged (Bow) Attack | Right Mouse Click |

---

## 🚀 How to Run

### 🧰 Requirements
- Python 3.x
- `pygame`
- `pytmx`

### 📦 Installation
Install the required packages using pip:
```bash
pip install pygame pytmx
```
### ▶️ Run the Game
Make sure you are in the root directory of the project (same level as `main.py`), then run:

```bash
python main.py
```
---

---

## 📋 Patch Notes

### v0.5 - Beta Release

- 🧍‍♂️ **Player System**
  - Basic movement and 8-direction control
  - Melee and bow attacks with cooldowns
  - Health system and invincibility window after taking damage

- 💀 **Death Mechanic**
  - One-time death animation with delay before game over
  - Game Over screen with 2-second pause

- 🤖 **Enemy AI**
  - Enemies follow the player and attack within range
  - Hurt and death animations included
  - Collision-aware movement

- 🏹 **Arrow System**
  - Projectiles with directional rotation and lifetime
  - Collide with enemies and disappear after impact or timeout

- 🗺️ **Map System**
  - Supports loading `.tmx` maps created in Tiled
  - Ground, object, and collision layers handled

- 🖼️ **Main Menu**
  - Simple start menu with player name input
  - Options for Play, Leaderboard (placeholder), and Quit

- 🧱 **Collision System**
  - Player and enemies react to walls and obstacles
  - Hitboxes separate from sprite bounding boxes

> Note: Leaderboard, Final Boss, and EXP system are planned for future updates.

