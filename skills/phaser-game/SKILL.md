# Phaser.js Game Development Skill

This skill provides Claude Code with knowledge for implementing Phaser.js games.

## Overview

Phaser is a fast, free, and fun open source HTML5 game framework. This skill covers:
- Project structure and setup
- Common game patterns
- Asset handling
- Build configuration

## Project Structure

```
game/
├── index.html          # Entry point
├── package.json        # Dependencies
├── vite.config.js      # Build config
├── src/
│   ├── main.js         # Game initialization
│   ├── scenes/         # Game scenes
│   │   ├── Boot.js     # Asset loading
│   │   ├── Menu.js     # Main menu
│   │   └── Game.js     # Main gameplay
│   ├── objects/        # Game objects
│   └── utils/          # Helpers
└── assets/
    ├── images/
    ├── audio/
    └── fonts/
```

## Common Patterns

### Scene Setup
```javascript
class GameScene extends Phaser.Scene {
    constructor() {
        super({ key: 'GameScene' });
    }

    preload() {
        // Load assets
    }

    create() {
        // Initialize game objects
    }

    update(time, delta) {
        // Game loop
    }
}
```

### Input Handling
```javascript
// Keyboard
this.cursors = this.input.keyboard.createCursorKeys();

// Mouse/Touch
this.input.on('pointerdown', (pointer) => {
    // Handle click/tap
});
```

### Physics
```javascript
// Enable arcade physics
this.physics.add.sprite(x, y, 'player');

// Collisions
this.physics.add.collider(player, platforms);
this.physics.add.overlap(player, coins, collectCoin);
```

## Build Configuration

Use Vite for modern, fast builds:

```javascript
// vite.config.js
export default {
    base: './',
    build: {
        outDir: 'dist',
        assetsDir: 'assets'
    }
};
```

## Best Practices

1. Use scene management for game states
2. Pool frequently created/destroyed objects
3. Use texture atlases for multiple sprites
4. Implement responsive scaling
5. Handle browser tab visibility changes
