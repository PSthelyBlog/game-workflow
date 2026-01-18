# Skills Documentation

Skills are structured knowledge files that provide Claude Code with domain-specific expertise during the build phase. This guide explains how skills work and how to create custom skills.

## Table of Contents

1. [Overview](#overview)
2. [How Skills Work](#how-skills-work)
3. [Available Skills](#available-skills)
4. [Skill File Anatomy](#skill-file-anatomy)
5. [Creating Custom Skills](#creating-custom-skills)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

Skills serve as contextual documentation that Claude Code reads before implementing a game. They provide:

- **Framework knowledge**: API patterns, best practices, common pitfalls
- **Code templates**: Ready-to-use patterns for common features
- **Genre-specific guidance**: Implementation strategies for different game types
- **Build/export instructions**: How to package games for distribution

When the BuildAgent runs, it loads the appropriate skill based on the selected game engine and includes it in Claude Code's context.

---

## How Skills Work

### Loading Process

1. **Engine selection**: The workflow determines which game engine to use (from config or GDD)
2. **Skill lookup**: The BuildAgent finds the corresponding skill in `skills/<engine>/SKILL.md`
3. **Context injection**: The skill content is included in Claude Code's system prompt
4. **Implementation**: Claude Code uses the skill knowledge to build the game

### Skill Selection

Skills are selected based on the `engine` parameter:

| Engine | Skill Path |
|--------|------------|
| `phaser` | `skills/phaser-game/SKILL.md` |
| `godot` | `skills/godot-game/SKILL.md` |

For QA, the testing skill is always loaded:

| Purpose | Skill Path |
|---------|------------|
| Testing | `skills/game-testing/SKILL.md` |

---

## Available Skills

### Phaser.js Game Skill

**Path**: `skills/phaser-game/SKILL.md`

**Covers**:
- Project structure and Vite configuration
- Scene lifecycle and management
- Sprites, animations, and rendering
- Physics systems (Arcade and Matter.js)
- Input handling (keyboard, mouse, touch, gamepad)
- Audio management with autoplay policy handling
- Cameras, tilemaps, and UI patterns
- State management (FSM pattern)
- Save/load with localStorage and IndexedDB
- Mobile and touch controls (virtual joystick, gestures)
- Particle effects and scene transitions
- Common patterns by genre:
  - Platformer
  - Top-down RPG
  - Shooter
  - Puzzle
- Performance optimization (object pooling, texture atlases)
- Build and export for itch.io

**Size**: ~2,700 lines

### Godot Game Skill

**Path**: `skills/godot-game/SKILL.md`

**Covers**:
- GDScript fundamentals and best practices
- Scene system and node lifecycle
- Signals and event bus pattern
- Input handling (keyboard, mouse, touch, gamepad)
- Physics systems (CharacterBody2D, RigidBody2D, Area2D)
- Animation systems (AnimationPlayer, AnimationTree, Tweens)
- Audio management with sound pools
- UI and Control nodes
- Tilemaps and procedural generation
- State management (FSM, singletons)
- Save/load with ConfigFile and ResourceSaver
- Common patterns by genre:
  - Platformer
  - Top-down RPG
  - Shooter
  - Puzzle
- Web export for HTML5/itch.io
- Performance optimization and debugging

**Size**: ~2,100 lines

### Game Testing Skill

**Path**: `skills/game-testing/SKILL.md`

**Covers**:
- Playwright setup and configuration
- Test fixtures and utilities
- Smoke tests (page loads, canvas, errors)
- Functional tests (gameplay mechanics)
- Visual regression testing
- Performance benchmarking (FPS, memory, load time)
- Console error detection and filtering
- Input simulation (keyboard, mouse, touch)
- Canvas inspection techniques
- Accessibility testing:
  - WCAG color contrast
  - Keyboard navigation
  - Screen reader support
  - Reduced motion
  - Colorblind modes
- Mobile device testing:
  - Device emulation
  - Touch gestures
  - Responsive layouts
  - Touch target sizes
- Audio testing (playback, controls, accessibility)
- Network testing for multiplayer:
  - API mocking
  - WebSocket mocking
  - Latency simulation
  - Reconnection testing
- CI/CD integration examples

**Size**: ~3,700 lines

---

## Skill File Anatomy

A skill file is a Markdown document with a specific structure:

```markdown
# [Framework] Game Development Skill

[Brief description of what this skill provides]

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Core Concepts](#core-concepts)
...

---

## Overview

[High-level explanation of the framework/tool]
- Key features
- When to use this skill
- Prerequisites

---

## Project Structure

[Standard directory layout with explanations]

```
project/
├── src/
│   └── ...
├── assets/
│   └── ...
└── config files
```

---

## [Core Topic 1]

### Subtopic

[Explanation with code examples]

```javascript
// Example code
function example() {
    // Implementation
}
```

### Best Practices

- Practice 1
- Practice 2

### Common Pitfalls

- Pitfall 1: [Description and solution]
- Pitfall 2: [Description and solution]

---

## Common Patterns by Genre

### Genre 1

[Implementation guidance specific to this genre]

```javascript
// Genre-specific code example
```

---

## Troubleshooting

### Issue 1
**Problem**: Description
**Solution**: How to fix

### Issue 2
...
```

### Key Sections

| Section | Purpose |
|---------|---------|
| Overview | Quick introduction and scope |
| Project Structure | File organization |
| Core Concepts | Framework fundamentals |
| API Reference | Common methods and classes |
| Patterns by Genre | Genre-specific implementations |
| Performance | Optimization techniques |
| Build/Export | Packaging for distribution |
| Troubleshooting | Common issues and solutions |

---

## Creating Custom Skills

### Step 1: Create the Skill Directory

```bash
mkdir -p skills/<skill-name>
```

### Step 2: Create SKILL.md

Create a `SKILL.md` file in the skill directory:

```bash
touch skills/<skill-name>/SKILL.md
```

### Step 3: Write the Skill Content

Follow the [anatomy](#skill-file-anatomy) structure above. Start with:

```markdown
# [Framework/Tool] Development Skill

This skill provides Claude Code with comprehensive knowledge for
implementing games using [Framework/Tool].

---

## Table of Contents

[List all major sections]

---

## Overview

[Describe what this skill covers and when to use it]
```

### Step 4: Add Code Examples

Include practical, copy-paste-ready code examples:

```markdown
## Player Movement

### Basic Movement

```javascript
// Player class with movement
class Player extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y) {
        super(scene, x, y, 'player');
        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.speed = 200;
        this.cursors = scene.input.keyboard.createCursorKeys();
    }

    update() {
        // Reset velocity
        this.setVelocity(0);

        // Horizontal movement
        if (this.cursors.left.isDown) {
            this.setVelocityX(-this.speed);
        } else if (this.cursors.right.isDown) {
            this.setVelocityX(this.speed);
        }

        // Vertical movement
        if (this.cursors.up.isDown) {
            this.setVelocityY(-this.speed);
        } else if (this.cursors.down.isDown) {
            this.setVelocityY(this.speed);
        }
    }
}
```
```

### Step 5: Include Genre Patterns

Add sections for common game types:

```markdown
## Common Patterns by Genre

### Platformer

Key mechanics for a platformer:
- Gravity-based movement
- Jump with coyote time
- One-way platforms
- Wall sliding/jumping

```javascript
// Platformer player with jump
class PlatformerPlayer extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y) {
        super(scene, x, y, 'player');
        // ... setup code

        this.jumpVelocity = -400;
        this.coyoteTime = 100; // ms
        this.lastOnGround = 0;
    }

    update(time) {
        // Track last time on ground (for coyote time)
        if (this.body.onFloor()) {
            this.lastOnGround = time;
        }

        // Jump with coyote time
        const canJump = (time - this.lastOnGround) < this.coyoteTime;
        if (this.cursors.up.isDown && canJump) {
            this.setVelocityY(this.jumpVelocity);
            this.lastOnGround = 0; // Prevent double jump
        }
    }
}
```
```

### Step 6: Add Troubleshooting

Include common issues and solutions:

```markdown
## Troubleshooting

### Assets Not Loading

**Problem**: Images or audio files return 404 errors.

**Solution**: Check the path relative to the HTML file. In Vite projects:
- Use `/assets/` prefix for files in the public folder
- Or import directly: `import playerImg from '../assets/player.png'`

### Physics Not Working

**Problem**: Sprites pass through each other without collision.

**Solution**:
1. Ensure physics is enabled in the game config
2. Add sprites to the physics system: `scene.physics.add.existing(sprite)`
3. Create colliders: `scene.physics.add.collider(player, platforms)`
```

### Step 7: Register the Skill (Optional)

To use a custom skill with the BuildAgent, you have two options:

**Option A: Use the engine name convention**

Name your skill directory to match an engine name, and set that engine in your workflow:

```python
workflow = GameWorkflow(
    prompt="Create a game...",
    engine="my-engine"  # Loads skills/my-engine/SKILL.md
)
```

**Option B: Specify skill path directly**

Pass the skill path to the BuildAgent:

```python
build_agent = BuildAgent(
    skill_path=Path("skills/custom-skill/SKILL.md")
)
```

---

## Best Practices

### Content Guidelines

1. **Be comprehensive but focused**: Cover everything Claude Code needs, but stay on-topic
2. **Use practical examples**: Real, working code > abstract explanations
3. **Include error handling**: Show how to handle common errors gracefully
4. **Document edge cases**: Cover platform-specific issues, browser quirks, etc.
5. **Keep it updated**: Skills should match the latest framework versions

### Code Example Guidelines

1. **Self-contained**: Examples should work when copy-pasted
2. **Commented**: Explain non-obvious lines
3. **Typed**: Include type annotations where applicable
4. **Error-handled**: Show proper error handling patterns

```javascript
// Good example - self-contained, commented, handles errors
class AudioManager {
    constructor(scene) {
        this.scene = scene;
        this.music = null;
        this.isMuted = false;
    }

    /**
     * Play background music with autoplay handling.
     * @param {string} key - Audio key from preload
     * @param {number} volume - Volume level (0-1)
     */
    playMusic(key, volume = 0.5) {
        // Stop existing music
        if (this.music) {
            this.music.stop();
        }

        try {
            this.music = this.scene.sound.add(key, {
                loop: true,
                volume: this.isMuted ? 0 : volume
            });
            this.music.play();
        } catch (error) {
            console.warn('Audio playback failed:', error);
            // Retry on user interaction (autoplay policy)
            this.scene.input.once('pointerdown', () => {
                this.playMusic(key, volume);
            });
        }
    }
}
```

### Organization Guidelines

1. **Logical flow**: Basics first, advanced topics later
2. **Table of contents**: Include a clickable TOC for navigation
3. **Section headers**: Use clear, descriptive headers
4. **Cross-references**: Link related sections
5. **Consistent formatting**: Follow Markdown best practices

---

## Troubleshooting

### Skill Not Loading

**Problem**: Claude Code doesn't seem to have the skill knowledge.

**Causes and solutions**:
1. **Wrong path**: Verify the skill file exists at `skills/<engine>/SKILL.md`
2. **Engine mismatch**: Check that the engine name matches the skill directory
3. **File encoding**: Ensure the file is UTF-8 encoded

### Skill Too Large

**Problem**: Skill content exceeds context limits.

**Solutions**:
1. **Split into sections**: Create multiple skill files for different aspects
2. **Prioritize content**: Keep essential patterns, move advanced topics to separate docs
3. **Use references**: Link to external documentation instead of duplicating

### Code Examples Not Working

**Problem**: Examples from the skill produce errors.

**Solutions**:
1. **Version check**: Ensure examples match the framework version used
2. **Dependencies**: Verify all required packages are listed
3. **Context**: Make sure examples include necessary imports/setup

### Custom Skill Not Recognized

**Problem**: BuildAgent can't find your custom skill.

**Solutions**:
1. **Directory structure**: Must be `skills/<name>/SKILL.md`
2. **Engine parameter**: Set the correct engine name in workflow config
3. **Permissions**: Ensure the file is readable

---

## Related Documentation

- [Setup Guide](setup.md) - Environment configuration
- [Configuration Reference](configuration.md) - Config options
- [MCP Servers](mcp-servers.md) - External integrations

---

## Appendix: Skill Template

Use this template to start a new skill:

```markdown
# [Framework Name] Development Skill

This skill provides Claude Code with comprehensive knowledge for
implementing [type of application] using [Framework Name].

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Getting Started](#getting-started)
4. [Core Concepts](#core-concepts)
5. [Common Patterns](#common-patterns)
6. [Performance](#performance)
7. [Build and Export](#build-and-export)
8. [Troubleshooting](#troubleshooting)

---

## Overview

[Framework Name] is [brief description].

This skill covers:
- [Topic 1]
- [Topic 2]
- [Topic 3]

---

## Project Structure

Standard project layout:

```
project/
├── src/
│   ├── main.js
│   └── ...
├── assets/
│   └── ...
└── package.json
```

---

## Getting Started

### Installation

```bash
npm install [framework]
```

### Basic Setup

```javascript
// Minimal working example
```

---

## Core Concepts

### Concept 1

[Explanation]

```javascript
// Example
```

### Concept 2

[Explanation]

```javascript
// Example
```

---

## Common Patterns

### Pattern 1: [Name]

[When to use this pattern]

```javascript
// Implementation
```

### Pattern 2: [Name]

[When to use this pattern]

```javascript
// Implementation
```

---

## Performance

### Optimization Techniques

1. [Technique 1]
2. [Technique 2]

### Memory Management

[Guidelines]

---

## Build and Export

### Development Build

```bash
npm run dev
```

### Production Build

```bash
npm run build
```

### Deployment

[Platform-specific instructions]

---

## Troubleshooting

### Issue 1

**Problem**: [Description]

**Solution**: [How to fix]

### Issue 2

**Problem**: [Description]

**Solution**: [How to fix]
```
