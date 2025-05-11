# The Last Crusade - V1.0

## 🎮 Game Overview

**The Last Crusade** is a fast-paced 2D survival game where players level up by defeating enemies, facing challenging bosses, and striving for victory. The game features an EXP-based progression system, class specialization, and a dynamic boss hierarchy, making each run unique and exciting.

---

## 🎯 Game Objective

* Survive against waves of enemies and powerful bosses.
* Level up by earning EXP from defeating foes.
* Choose a class specialization at level 15 to unlock unique abilities.
* Defeat the final boss, the Elite Orc, or perish in the attempt.

---

## 🧩 Key Features - V1.0

* ⚔️ **Melee and Ranged Combat:** Use left-click for melee attacks and right-click for bow or spell attacks.
* 🆕 **Class System:** At level 15, select between **Knight**, **Wizard**, or **Judiciar**, each with unique special skills and stat modifiers.
* 📈 **Level & EXP System:** EXP base and growth rate govern player progression; stat upgrades and health resets on level-up.
* 🤖 **Dynamic Enemy AI & Bosses:** Enemies adapt to player level; minibosses (Greatsword Skeleton at level 10, Werewolf at level 20) and the Elite Orc final boss (unleashed at level 30 or after 10 minutes).
* 📝 **Run Logging:** Records each run in `runs.csv`, including player name, play time, chosen class, max level, miniboss kills, and victory status.
* 🛠️ **Main Menu & Leaderboard Placeholder:** Enter player name before playing; leaderboard integration is coming soon.
* 🕰️ **HUD Enhancements:** On-screen timer, health bar, EXP bar, and boss health bar integrated into gameplay.
* 🗺️ **Map & Collision:** Tiled map support with layered rendering and refined collision detection.
* 🎨 **Visual & Animation Improvements:** Smooth animations for player and enemy actions, plus refined death animations with delay.

---

## 🎮 Controls

| Action         | Control           |
|----------------| ----------------- |
| Move Up        | `W` / `↑`         |
| Move Down      | `S` / `↓`         |
| Move Left      | `A` / `←`         |
| Move Right     | `D` / `→`         |
| Melee Attack   | Left Mouse Click  |
| Special Attack | Right Mouse Click |

---

## 🚀 How to Run

### 🧰 Requirements

* Python 3.x
* `pygame`
* `pytmx`

### 📦 Installation

```bash
pip install pygame pytmx
```

### ▶️ Run the Game

Run from the project root (same level as `main.py`):

```bash
python main.py
```

---

## 📋 Patch Notes

### v1.0 - Stable Release

* Introduced **Class Specialization** with unique abilities for each class.
* Implemented **CSV Run Logging** in `runs.csv`.
* Completed **Boss Hierarchy**: Greatsword Skeleton, Werewolf, Elite Orc.
* Enhanced **HUD**: boss health bar, EXP bar, on-screen timer.
* Added **Player Name Input** and menu background support.
* Improved **Enemy AI** and collision mechanics.
* Fixed death animation timing and game over logic.

### v0.5 - Beta Release

* ⚔️ **Melee and Ranged Combat:** Basic attacks and cooldowns.
* 🧠 **Enemy AI:** Tracking and attack behaviors.
* 🔥 **Death Animation & Delay:** One-time death animation before game over.
* 🗺️ **Tiled Map Integration:** Ground, object, and collision layers.
* 🏆 **Leaderboard (coming soon):** Placeholder for future feature.
* ⚡ **Quick Play Loop:** Fast-paced gameplay and replayability.
