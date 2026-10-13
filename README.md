<div align="center">

# Temple Run Arcade 3D

> **High-performance, deterministic endless runner built with specialized ECS architecture.**

![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge&logo=appveyor)
![Version](https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)
![Framework](https://img.shields.io/badge/Engine-Ursina-orange?style=for-the-badge)
![Architecture](https://img.shields.io/badge/Architecture-Modular-red?style=for-the-badge)

<br/>
</div>

## 📖 About

**Temple Run Arcade 3D** is a specialized engine implementation of the classic endless runner genre, re-engineered for **deterministic arcade compliance**. Unlike traditional physics-based runners, this engine utilizes a discrete state machine and lane-based coordinate system to ensure pixel-perfect collision detection and zero-latency input response.

Built for developers who need to understand **game loop architecture** and **procedural generation** without the overhead of heavy commercial engines.

---

## 🚀 Key Features

*   **Deterministic State Machine** — Uses discrete integer-based lane logic (0, 1, 2) rather than floating-point physics to guarantee predictable outcomes.
*   **Efficient Entity Management** — Clean separation of visual and logical layers with automatic entity cleanup to prevent memory leaks.
*   **Procedural Track Generation** — Infinite world generation using dynamic difficulty scaling and pattern-based spawning.
*   **Modular System Architecture** — Decoupled game systems (collision, scoring, spawning) that communicate through well-defined interfaces.
*   **Hot-Reloadable Config** — Centralized configuration management for rapid gameplay tuning without recompilation.

---

## 🛠 Tech Stack

| **Category** | **Technologies** |
| :--- | :--- |
| **Language** | ![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white) |
| **Engine** | ![Ursina](https://img.shields.io/badge/Ursina-Engine-FF006E?style=for-the-badge) ![Panda3D](https://img.shields.io/badge/Panda3D-Backend-green?style=for-the-badge) |
| **Systems** | ![ECS](https://img.shields.io/badge/Pattern-ECS-8B5CF6?style=for-the-badge) ![GLSL](https://img.shields.io/badge/Shaders-GLSL-purple?style=for-the-badge) |
| **Tooling** | ![Pip](https://img.shields.io/badge/Package_Manager-Pip-yellow?style=for-the-badge) ![Venv](https://img.shields.io/badge/Env-Venv-blue?style=for-the-badge) |

---

## 🏗 Architecture

### System Design
The engine follows a strict separation of concerns, decoupling the **Game Loop** from **Entity Logic**.

```mermaid
graph TD
    A[Main Loop] -->|Delta Time| B[Game Managers]
    B --> C[Spawning System]
    B --> D[Collision System]
    B --> E[Camera System]
    
    C -->|Instantiate| F[Entities]
    F -->|Position Data| D
    D -->|Hit Events| G[Score/GameState]
    
    subgraph Core Loop
    A
    end
    
    subgraph Logic Layer
    B
    C
    D
    E
    end
    
    subgraph Data Layer
    F
    G
    end
```

### Component Interaction
Entities are data-driven wrappers around Ursina Visuals, controlled by external systems.

```mermaid
sequenceDiagram
    participant Input
    participant Player
    participant CollisionSystem
    participant GameState
    
    Input->>Player: Lane Switch (Left/Right)
    Player->>Player: Update Lane Index (Int)
    Player->>Player: Tween Visual Position
    
    loop Every Frame
        CollisionSystem->>Player: Get Lane & Depth
        CollisionSystem->>Obstacles: Check Lane Match
        
        alt Collision Detected
            CollisionSystem->>GameState: Trigger Game Over
            GameState->>Input: Disable Controls
        end
    end
```

---

## 📚 Documentation & Examples

### Lane Logic Implementation
The core mechanic relies on integer-based positioning to prevent "floaty" movement.

```python
# entities/player.py

def switch_lane(self, direction):
    """
    Deterministic lane switching with boundary checks.
    Args:
        direction (int): -1 for Left, 1 for Right
    """
    new_lane = self.lane + direction
    
    # Boundary Check (Lanes 0, 1, 2)
    if 0 <= new_lane <= 2:
        self.lane = new_lane
        # Trigger visual tween (does not affect logical position)
        self.animate_x(self.lane_positions[self.lane], duration=0.2)
```

### Collision Detection
Collisions are calculated mathematically, not via physics engine raycasts, ensuring 100% reliability.

```python
# systems/collision.py

def check_collision(self, player, obstacles):
    for obs in obstacles:
        # 1. Lane Filter (Logical)
        if obs.lane != player.lane:
            continue
            
        # 2. Depth Check (Math)
        distance = abs(player.z - obs.z)
        if distance < self.COLLISION_THRESHOLD:
            return True, obs
    return False, None
```

---

## ⚡ Getting Started

### Prerequisites
*   **Python 3.10+**
*   **Graphics Card** supporting OpenGL 2.0+

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/temple-run-arcade.git
    cd temple-run-arcade
    ```

2.  **Initialize Environment**
    ```bash
    # Create virtual environment
    python -m venv venv
    
    # Activate (Windows)
    .\venv\Scripts\activate
    
    # Activate (Unix)
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Engine
```bash
python main.py
```

**First-Time Setup:**
The game will automatically generate all required texture assets on first run. You should see:
```
[SETUP] Generating missing textures...
[SETUP] Texture generation complete!
```

This only happens once. Subsequent runs will skip this step.

**Manual Texture Generation (Optional):**
If you want to regenerate textures or inspect the generation process:
```bash
python utils/texture_gen.py
```

---

## 📂 Project Structure

```text
/temple-run
├── assets/              # Generated textures and models
├── config.py            # Global configuration (Constants)
├── entities/            # Game Objects (Player, Track, Obstacles)
├── systems/             # Logic Systems (Collision, Spawning)
├── utils/               # Helper modules (Procedural gen)
├── main.py              # Application Entry Point
└── requirements.txt     # Dependency Manifest
```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

<div align="center">
    <sub>Built with ❤️ by the Engineering Team</sub>
</div>
