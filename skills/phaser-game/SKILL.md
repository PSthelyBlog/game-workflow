# Phaser.js Game Development Skill

This skill provides Claude Code with comprehensive knowledge for implementing Phaser.js games. Use this when building browser-based games with Phaser 3.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Scene Lifecycle](#scene-lifecycle)
4. [Sprites and GameObjects](#sprites-and-gameobjects)
5. [Animations](#animations)
6. [Physics](#physics)
7. [Input Handling](#input-handling)
8. [Audio](#audio)
9. [Cameras](#cameras)
10. [Tilemaps](#tilemaps)
11. [UI Patterns](#ui-patterns)
12. [State Management](#state-management)
13. [Save/Load Game State](#saveload-game-state)
14. [Mobile and Touch Controls](#mobile-and-touch-controls)
15. [Particle Effects](#particle-effects)
16. [Scene Transitions](#scene-transitions)
17. [Common Game Patterns by Genre](#common-game-patterns-by-genre)
18. [Performance Optimization](#performance-optimization)
19. [Build and Export](#build-and-export)
20. [Troubleshooting](#troubleshooting)

---

## Overview

Phaser is a fast, free, and fun open source HTML5 game framework. This skill covers:
- Project structure and setup
- Scene management and game flow
- Sprites, animations, and rendering
- Physics systems (Arcade and Matter.js)
- Input handling (keyboard, mouse, touch)
- Audio management
- Asset loading and optimization
- Common game patterns by genre

---

## Project Structure

The standard project structure for a Phaser game:

```
game/
├── index.html              # Entry point
├── package.json            # Dependencies
├── vite.config.js          # Build config
├── src/
│   ├── main.js             # Game initialization and config
│   ├── scenes/             # Game scenes
│   │   ├── BootScene.js    # Initial boot, minimal loading
│   │   ├── PreloadScene.js # Main asset loading with progress
│   │   ├── MenuScene.js    # Main menu
│   │   ├── GameScene.js    # Main gameplay
│   │   └── UIScene.js      # Optional: Overlay UI scene
│   ├── objects/            # Game object classes
│   │   ├── Player.js       # Player character
│   │   ├── Enemy.js        # Enemy types
│   │   └── Collectible.js  # Items, powerups
│   ├── managers/           # Game managers
│   │   ├── StateManager.js # Game state management
│   │   ├── AudioManager.js # Audio control
│   │   └── SaveManager.js  # Save/load functionality
│   └── utils/              # Helpers
│       ├── Constants.js    # Game constants
│       └── Helpers.js      # Utility functions
└── assets/
    ├── images/             # Sprites, backgrounds, UI
    ├── audio/              # Music and sound effects
    ├── fonts/              # Custom fonts (bitmap or web)
    └── data/               # JSON data files (levels, dialogue)
```

---

## Scene Lifecycle

Every Phaser scene has these key methods:

```javascript
class GameScene extends Phaser.Scene {
    constructor() {
        super({ key: 'GameScene' });
    }

    // Called once before preload (rarely needed)
    init(data) {
        // Receive data from previous scene
        this.level = data.level || 1;
    }

    // Load assets (if not loaded in PreloadScene)
    preload() {
        this.load.image('key', 'path/to/image.png');
    }

    // Create game objects, set up physics, input
    create() {
        this.player = this.add.sprite(100, 100, 'player');
    }

    // Game loop - called every frame (60fps default)
    update(time, delta) {
        // time: total elapsed ms
        // delta: ms since last frame
        this.player.update(time, delta);
    }
}
```

### Scene Communication

```javascript
// Start a new scene
this.scene.start('GameScene', { level: 1 });

// Launch scene in parallel
this.scene.launch('UIScene');

// Stop current scene
this.scene.stop();

// Pause/resume scene
this.scene.pause();
this.scene.resume();

// Get another scene
const uiScene = this.scene.get('UIScene');
uiScene.updateScore(this.score);

// Scene events
this.scene.get('GameScene').events.on('scoreChanged', (score) => {
    this.updateScoreDisplay(score);
});
```

---

## Sprites and GameObjects

### Creating Sprites

```javascript
// Basic sprite
const sprite = this.add.sprite(x, y, 'textureKey');

// With physics (Arcade)
const physicsSprite = this.physics.add.sprite(x, y, 'textureKey');

// From spritesheet frame
const frame = this.add.sprite(x, y, 'spritesheet', frameNumber);
```

### Sprite Properties

```javascript
sprite.setPosition(x, y);
sprite.setScale(2);               // 2x size
sprite.setAlpha(0.5);             // 50% transparent
sprite.setTint(0xff0000);         // Red tint
sprite.setOrigin(0.5, 1);         // Bottom center
sprite.setFlipX(true);            // Mirror horizontally
sprite.setDepth(10);              // Z-order (higher = front)
sprite.setVisible(false);         // Hide
sprite.setActive(false);          // Disable update
```

### Groups (for managing multiple objects)

```javascript
// Static group (no physics updates)
const platforms = this.physics.add.staticGroup();
platforms.create(400, 568, 'ground');

// Dynamic group
const enemies = this.physics.add.group({
    key: 'enemy',
    repeat: 10,
    setXY: { x: 50, y: 0, stepX: 70 }
});

// Iterate over group
enemies.children.iterate((enemy) => {
    enemy.setVelocityY(Phaser.Math.Between(50, 100));
});
```

### Custom Game Objects

```javascript
// Player.js
class Player extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y) {
        super(scene, x, y, 'player');

        // Add to scene
        scene.add.existing(this);
        scene.physics.add.existing(this);

        // Configure physics
        this.setCollideWorldBounds(true);
        this.setBounce(0.1);

        // Player state
        this.health = 100;
        this.maxHealth = 100;
        this.isInvulnerable = false;
    }

    update(cursors) {
        // Movement logic
        if (cursors.left.isDown) {
            this.setVelocityX(-200);
            this.setFlipX(true);
        } else if (cursors.right.isDown) {
            this.setVelocityX(200);
            this.setFlipX(false);
        } else {
            this.setVelocityX(0);
        }
    }

    takeDamage(amount) {
        if (this.isInvulnerable) return;

        this.health -= amount;
        this.isInvulnerable = true;

        // Flash effect
        this.scene.tweens.add({
            targets: this,
            alpha: 0.5,
            duration: 100,
            repeat: 5,
            yoyo: true,
            onComplete: () => {
                this.isInvulnerable = false;
                this.alpha = 1;
            }
        });

        if (this.health <= 0) {
            this.die();
        }
    }

    die() {
        this.scene.events.emit('playerDied');
        this.destroy();
    }
}
```

---

## Animations

### Creating Animations

```javascript
// In PreloadScene.create() or BootScene.create()
this.anims.create({
    key: 'walk',
    frames: this.anims.generateFrameNumbers('player', { start: 0, end: 7 }),
    frameRate: 10,
    repeat: -1  // -1 = loop forever
});

this.anims.create({
    key: 'jump',
    frames: [{ key: 'player', frame: 4 }],
    frameRate: 20
});

// From texture atlas
this.anims.create({
    key: 'explode',
    frames: this.anims.generateFrameNames('atlas', {
        prefix: 'explosion_',
        start: 1,
        end: 8,
        suffix: '.png'
    }),
    frameRate: 15,
    hideOnComplete: true
});
```

### Playing Animations

```javascript
// Play animation
sprite.play('walk');

// Play with callback
sprite.play('explode').once('animationcomplete', () => {
    sprite.destroy();
});

// Check current animation
if (sprite.anims.currentAnim?.key === 'walk') {
    // ...
}

// Stop animation
sprite.stop();
```

---

## Physics

### Arcade Physics (Simple, Fast)

```javascript
// In main.js config
physics: {
    default: 'arcade',
    arcade: {
        gravity: { y: 300 },
        debug: false  // Set true to see hitboxes
    }
}

// In scene
create() {
    this.player = this.physics.add.sprite(100, 100, 'player');
    this.player.setCollideWorldBounds(true);
    this.player.setBounce(0.2);

    // Custom hitbox
    this.player.body.setSize(30, 50);
    this.player.body.setOffset(10, 5);

    // Platforms
    const platforms = this.physics.add.staticGroup();
    platforms.create(400, 568, 'ground').setScale(2).refreshBody();

    // Collisions
    this.physics.add.collider(this.player, platforms);

    // Overlap (trigger without collision)
    this.physics.add.overlap(
        this.player,
        this.coins,
        this.collectCoin,
        null,
        this
    );
}

collectCoin(player, coin) {
    coin.destroy();
    this.score += 10;
}
```

### Common Physics Operations

```javascript
// Velocity
body.setVelocity(100, -200);       // x, y
body.setVelocityX(100);
body.setVelocityY(-200);

// Acceleration
body.setAcceleration(100, 0);

// Drag (friction)
body.setDrag(100, 0);
body.setDragX(100);

// Max velocity
body.setMaxVelocity(300, 600);

// Immovable (won't be pushed)
body.setImmovable(true);

// Check if on ground
if (body.touching.down || body.blocked.down) {
    // Player is on ground
}
```

### Matter.js Physics (Complex)

```javascript
// In main.js config
physics: {
    default: 'matter',
    matter: {
        gravity: { y: 1 },
        debug: true
    }
}

// Create Matter sprite
const ball = this.matter.add.sprite(400, 100, 'ball', null, {
    restitution: 0.8,
    friction: 0.1,
    shape: { type: 'circle', radius: 32 }
});

// Apply force
ball.applyForce({ x: 0.05, y: 0 });

// Collision events
this.matter.world.on('collisionstart', (event) => {
    event.pairs.forEach((pair) => {
        const { bodyA, bodyB } = pair;
        // Handle collision
    });
});
```

---

## Input Handling

### Keyboard

```javascript
create() {
    // Cursor keys (arrows)
    this.cursors = this.input.keyboard.createCursorKeys();

    // Custom keys
    this.keys = this.input.keyboard.addKeys({
        up: Phaser.Input.Keyboard.KeyCodes.W,
        down: Phaser.Input.Keyboard.KeyCodes.S,
        left: Phaser.Input.Keyboard.KeyCodes.A,
        right: Phaser.Input.Keyboard.KeyCodes.D,
        jump: Phaser.Input.Keyboard.KeyCodes.SPACE,
        attack: Phaser.Input.Keyboard.KeyCodes.X
    });

    // Single key
    this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);

    // One-time key press event
    this.input.keyboard.once('keydown-ENTER', () => {
        this.scene.start('GameScene');
    });

    // Key press event (repeatable)
    this.input.keyboard.on('keydown-P', () => {
        this.togglePause();
    });
}

update() {
    // Check if key is held down
    if (this.cursors.left.isDown) {
        this.player.setVelocityX(-200);
    } else if (this.cursors.right.isDown) {
        this.player.setVelocityX(200);
    }

    // Just pressed (once per press)
    if (Phaser.Input.Keyboard.JustDown(this.keys.jump)) {
        this.player.jump();
    }
}
```

### Mouse/Pointer

```javascript
create() {
    // Click/tap anywhere
    this.input.on('pointerdown', (pointer) => {
        console.log(pointer.x, pointer.y);
    });

    // Make object interactive
    const button = this.add.sprite(100, 100, 'button');
    button.setInteractive({ useHandCursor: true });

    button.on('pointerover', () => button.setTint(0xaaaaaa));
    button.on('pointerout', () => button.clearTint());
    button.on('pointerdown', () => this.startGame());

    // Drag
    button.setInteractive({ draggable: true });
    button.on('drag', (pointer, dragX, dragY) => {
        button.x = dragX;
        button.y = dragY;
    });
}

update() {
    // Check if pointer is down
    if (this.input.activePointer.isDown) {
        // Move towards pointer
        this.physics.moveTo(
            this.player,
            this.input.activePointer.x,
            this.input.activePointer.y,
            200  // speed
        );
    }
}
```

### Gamepad Support

```javascript
create() {
    // Enable gamepad
    this.input.gamepad.once('connected', (pad) => {
        console.log('Gamepad connected:', pad.id);
        this.gamepad = pad;
    });
}

update() {
    if (!this.gamepad) return;

    // D-pad or left stick
    const leftStickX = this.gamepad.leftStick.x;
    const leftStickY = this.gamepad.leftStick.y;

    if (Math.abs(leftStickX) > 0.1) {
        this.player.setVelocityX(leftStickX * 200);
    }

    // Buttons
    if (this.gamepad.A) {
        this.player.jump();
    }
    if (this.gamepad.B) {
        this.player.attack();
    }
}
```

---

## Audio

### Loading Audio

```javascript
// In preload
this.load.audio('bgm', 'assets/audio/music.mp3');
this.load.audio('jump', ['assets/audio/jump.ogg', 'assets/audio/jump.mp3']);

// Audio sprite (multiple sounds in one file)
this.load.audioSprite('sfx', 'assets/audio/sfx.json', [
    'assets/audio/sfx.ogg',
    'assets/audio/sfx.mp3'
]);
```

### Playing Audio

```javascript
// Sound effect (one-shot)
this.sound.play('jump');

// With config
this.sound.play('jump', { volume: 0.5 });

// Background music (looping)
const music = this.sound.add('bgm', { loop: true, volume: 0.3 });
music.play();

// Store reference for control
this.bgm = this.sound.add('bgm', { loop: true });
this.bgm.play();

// Control
this.bgm.pause();
this.bgm.resume();
this.bgm.stop();
this.bgm.setVolume(0.5);
```

### Audio Manager Pattern

```javascript
// AudioManager.js
class AudioManager {
    constructor(scene) {
        this.scene = scene;
        this.sounds = {};
        this.music = null;
        this.isMuted = false;
        this.musicVolume = 0.5;
        this.sfxVolume = 0.7;
    }

    addSound(key, config = {}) {
        this.sounds[key] = this.scene.sound.add(key, {
            volume: this.sfxVolume,
            ...config
        });
    }

    playSound(key, config = {}) {
        if (this.isMuted) return;

        if (this.sounds[key]) {
            this.sounds[key].play(config);
        } else {
            this.scene.sound.play(key, {
                volume: this.sfxVolume,
                ...config
            });
        }
    }

    playMusic(key, config = {}) {
        if (this.music) {
            this.music.stop();
        }

        this.music = this.scene.sound.add(key, {
            loop: true,
            volume: this.musicVolume,
            ...config
        });

        if (!this.isMuted) {
            this.music.play();
        }
    }

    fadeOutMusic(duration = 1000) {
        if (this.music) {
            this.scene.tweens.add({
                targets: this.music,
                volume: 0,
                duration: duration,
                onComplete: () => {
                    this.music.stop();
                }
            });
        }
    }

    crossfadeMusic(newKey, duration = 1000) {
        const newMusic = this.scene.sound.add(newKey, {
            loop: true,
            volume: 0
        });

        newMusic.play();

        this.scene.tweens.add({
            targets: newMusic,
            volume: this.musicVolume,
            duration: duration
        });

        if (this.music) {
            this.scene.tweens.add({
                targets: this.music,
                volume: 0,
                duration: duration,
                onComplete: () => {
                    this.music.stop();
                    this.music = newMusic;
                }
            });
        } else {
            this.music = newMusic;
        }
    }

    setMute(muted) {
        this.isMuted = muted;
        this.scene.sound.setMute(muted);
    }

    toggleMute() {
        this.setMute(!this.isMuted);
        return this.isMuted;
    }
}
```

### Audio Best Practices

```javascript
// Handle browser autoplay policy
this.input.once('pointerdown', () => {
    if (this.sound.context.state === 'suspended') {
        this.sound.context.resume();
    }
});

// Mute when tab is hidden
document.addEventListener('visibilitychange', () => {
    this.sound.setMute(document.hidden);
});

// Sound pool for frequently played sounds
class SoundPool {
    constructor(scene, key, count = 5) {
        this.sounds = [];
        this.index = 0;

        for (let i = 0; i < count; i++) {
            this.sounds.push(scene.sound.add(key));
        }
    }

    play(config = {}) {
        this.sounds[this.index].play(config);
        this.index = (this.index + 1) % this.sounds.length;
    }
}

// Usage
this.jumpSounds = new SoundPool(this, 'jump', 3);
this.jumpSounds.play();
```

---

## Cameras

```javascript
// Main camera
const camera = this.cameras.main;

// Follow player
camera.startFollow(this.player, true, 0.1, 0.1);

// Set bounds (usually to match tilemap)
camera.setBounds(0, 0, 2000, 600);

// Zoom
camera.setZoom(1.5);

// Effects
camera.shake(500, 0.01);           // duration, intensity
camera.flash(500, 255, 255, 255);  // duration, r, g, b
camera.fade(1000, 0, 0, 0);        // duration, r, g, b

// Screen shake on hit
onPlayerHit() {
    this.cameras.main.shake(200, 0.005);
}

// Dead zones (area where player can move without camera following)
camera.setDeadzone(200, 100);

// Viewport (for split-screen)
const cam1 = this.cameras.main.setViewport(0, 0, 400, 300);
const cam2 = this.cameras.add(400, 0, 400, 300);
cam2.startFollow(player2);
```

---

## Tilemaps

```javascript
// In preload
this.load.image('tiles', 'assets/images/tileset.png');
this.load.tilemapTiledJSON('map', 'assets/data/level1.json');

// In create
const map = this.make.tilemap({ key: 'map' });
const tileset = map.addTilesetImage('tileset-name-in-tiled', 'tiles');

// Create layers
const backgroundLayer = map.createLayer('Background', tileset, 0, 0);
const groundLayer = map.createLayer('Ground', tileset, 0, 0);

// Enable collisions (by tile index or property)
groundLayer.setCollisionByProperty({ collides: true });
// Or by tile indices
groundLayer.setCollisionBetween(1, 10);

// Add collision with player
this.physics.add.collider(this.player, groundLayer);

// Set camera bounds to map size
this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);

// Spawn objects from Tiled object layer
const spawnPoints = map.getObjectLayer('SpawnPoints').objects;
spawnPoints.forEach((point) => {
    if (point.name === 'player') {
        this.player.setPosition(point.x, point.y);
    } else if (point.name === 'enemy') {
        this.spawnEnemy(point.x, point.y, point.properties);
    }
});

// Get tile at position
const tile = groundLayer.getTileAtWorldXY(player.x, player.y);
if (tile?.properties?.hazard) {
    player.takeDamage(10);
}
```

---

## UI Patterns

### HUD (Heads-Up Display)

```javascript
// Create UI scene that runs parallel to game
class UIScene extends Phaser.Scene {
    constructor() {
        super({ key: 'UIScene', active: true });
    }

    create() {
        this.scoreText = this.add.text(16, 16, 'Score: 0', {
            fontSize: '32px',
            color: '#fff',
            stroke: '#000',
            strokeThickness: 4
        });

        // Listen to game events
        const gameScene = this.scene.get('GameScene');
        gameScene.events.on('scoreChanged', (score) => {
            this.scoreText.setText(`Score: ${score}`);
        });
    }
}

// In GameScene
this.events.emit('scoreChanged', this.score);
```

### Health Bar

```javascript
class HealthBar {
    constructor(scene, x, y, maxHealth, width = 200, height = 20) {
        this.scene = scene;
        this.maxHealth = maxHealth;
        this.currentHealth = maxHealth;
        this.width = width;
        this.height = height;

        // Background
        this.bg = scene.add.rectangle(x, y, width, height, 0x222222);
        this.bg.setOrigin(0, 0.5);

        // Border
        this.border = scene.add.rectangle(x, y, width, height);
        this.border.setOrigin(0, 0.5);
        this.border.setStrokeStyle(2, 0xffffff);

        // Health bar
        this.bar = scene.add.rectangle(x + 2, y, width - 4, height - 4, 0x00ff00);
        this.bar.setOrigin(0, 0.5);
    }

    setHealth(value) {
        this.currentHealth = Phaser.Math.Clamp(value, 0, this.maxHealth);
        const percent = this.currentHealth / this.maxHealth;

        // Animate width change
        this.scene.tweens.add({
            targets: this.bar,
            width: (this.width - 4) * percent,
            duration: 200,
            ease: 'Power2'
        });

        // Color based on health
        if (percent > 0.6) {
            this.bar.setFillStyle(0x00ff00);
        } else if (percent > 0.3) {
            this.bar.setFillStyle(0xffff00);
        } else {
            this.bar.setFillStyle(0xff0000);
        }
    }

    setPosition(x, y) {
        this.bg.setPosition(x, y);
        this.border.setPosition(x, y);
        this.bar.setPosition(x + 2, y);
    }

    setVisible(visible) {
        this.bg.setVisible(visible);
        this.border.setVisible(visible);
        this.bar.setVisible(visible);
    }

    destroy() {
        this.bg.destroy();
        this.border.destroy();
        this.bar.destroy();
    }
}
```

### Dialog Box

```javascript
class DialogBox {
    constructor(scene, x, y, width, height) {
        this.scene = scene;
        this.container = scene.add.container(x, y);

        // Background
        this.bg = scene.add.rectangle(0, 0, width, height, 0x000000, 0.8);
        this.bg.setOrigin(0.5);

        // Border
        this.border = scene.add.rectangle(0, 0, width, height);
        this.border.setOrigin(0.5);
        this.border.setStrokeStyle(2, 0xffffff);

        // Text
        this.text = scene.add.text(0, 0, '', {
            fontSize: '20px',
            color: '#ffffff',
            wordWrap: { width: width - 40 },
            align: 'left'
        });
        this.text.setOrigin(0.5);

        this.container.add([this.bg, this.border, this.text]);
        this.container.setDepth(1000);
        this.container.setVisible(false);
    }

    show(message, duration = 0) {
        this.text.setText(message);
        this.container.setVisible(true);

        if (duration > 0) {
            this.scene.time.delayedCall(duration, () => {
                this.hide();
            });
        }
    }

    hide() {
        this.container.setVisible(false);
    }

    typeText(message, speed = 30) {
        this.text.setText('');
        this.container.setVisible(true);

        let index = 0;
        this.scene.time.addEvent({
            callback: () => {
                this.text.setText(message.substring(0, index + 1));
                index++;
            },
            repeat: message.length - 1,
            delay: speed
        });
    }
}
```

---

## State Management

### Finite State Machine

```javascript
// StateMachine.js
class StateMachine {
    constructor(initialState, possibleStates, stateArgs = []) {
        this.initialState = initialState;
        this.possibleStates = possibleStates;
        this.stateArgs = stateArgs;
        this.state = null;

        // State event handlers
        for (const state of Object.values(this.possibleStates)) {
            state.stateMachine = this;
        }
    }

    step() {
        if (this.state === null) {
            this.state = this.initialState;
            this.possibleStates[this.state].enter(...this.stateArgs);
        }

        this.possibleStates[this.state].execute(...this.stateArgs);
    }

    transition(newState, ...enterArgs) {
        this.possibleStates[this.state].exit(...this.stateArgs);
        this.state = newState;
        this.possibleStates[this.state].enter(...this.stateArgs, ...enterArgs);
    }
}

// State.js
class State {
    enter() {}
    execute() {}
    exit() {}
}

// PlayerStates.js
class IdleState extends State {
    enter(player) {
        player.play('idle');
    }

    execute(player) {
        const { left, right, up } = player.scene.cursors;

        if (left.isDown || right.isDown) {
            this.stateMachine.transition('walk');
        }

        if (Phaser.Input.Keyboard.JustDown(up) && player.body.blocked.down) {
            this.stateMachine.transition('jump');
        }
    }
}

class WalkState extends State {
    enter(player) {
        player.play('walk');
    }

    execute(player) {
        const { left, right, up } = player.scene.cursors;

        if (left.isDown) {
            player.setVelocityX(-200);
            player.setFlipX(true);
        } else if (right.isDown) {
            player.setVelocityX(200);
            player.setFlipX(false);
        } else {
            this.stateMachine.transition('idle');
        }

        if (Phaser.Input.Keyboard.JustDown(up) && player.body.blocked.down) {
            this.stateMachine.transition('jump');
        }
    }

    exit(player) {
        player.setVelocityX(0);
    }
}

class JumpState extends State {
    enter(player) {
        player.play('jump');
        player.setVelocityY(-400);
    }

    execute(player) {
        const { left, right } = player.scene.cursors;

        // Air control
        if (left.isDown) {
            player.setVelocityX(-150);
            player.setFlipX(true);
        } else if (right.isDown) {
            player.setVelocityX(150);
            player.setFlipX(false);
        }

        // Landed
        if (player.body.blocked.down) {
            this.stateMachine.transition('idle');
        }
    }
}

// Usage in Player.js
class Player extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y) {
        super(scene, x, y, 'player');
        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.stateMachine = new StateMachine('idle', {
            idle: new IdleState(),
            walk: new WalkState(),
            jump: new JumpState(),
        }, [this]);
    }

    update() {
        this.stateMachine.step();
    }
}
```

### Game State Manager

```javascript
// StateManager.js - Global game state
class StateManager {
    constructor() {
        this.state = {
            score: 0,
            lives: 3,
            level: 1,
            coins: 0,
            unlockedLevels: [1],
            achievements: [],
            settings: {
                musicVolume: 0.5,
                sfxVolume: 0.7,
                fullscreen: false
            }
        };

        this.listeners = new Map();
    }

    get(key) {
        return key.split('.').reduce((obj, k) => obj?.[k], this.state);
    }

    set(key, value) {
        const keys = key.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((obj, k) => obj[k], this.state);
        const oldValue = target[lastKey];
        target[lastKey] = value;

        // Notify listeners
        this.emit(key, value, oldValue);
    }

    increment(key, amount = 1) {
        this.set(key, this.get(key) + amount);
    }

    on(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, []);
        }
        this.listeners.get(key).push(callback);
    }

    off(key, callback) {
        const callbacks = this.listeners.get(key);
        if (callbacks) {
            const index = callbacks.indexOf(callback);
            if (index !== -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(key, newValue, oldValue) {
        const callbacks = this.listeners.get(key);
        if (callbacks) {
            callbacks.forEach(cb => cb(newValue, oldValue));
        }
    }

    reset() {
        this.state.score = 0;
        this.state.lives = 3;
        this.state.coins = 0;
    }

    toJSON() {
        return JSON.stringify(this.state);
    }

    fromJSON(json) {
        this.state = JSON.parse(json);
    }
}

// Make it a singleton
const gameState = new StateManager();
export default gameState;

// Usage
import gameState from './StateManager';

// In any scene
gameState.set('score', 100);
gameState.increment('coins');
gameState.on('lives', (newValue) => {
    console.log('Lives changed to:', newValue);
});
```

---

## Save/Load Game State

### localStorage Save System

```javascript
// SaveManager.js
class SaveManager {
    constructor(storageKey = 'gameSave') {
        this.storageKey = storageKey;
        this.autosaveInterval = null;
    }

    save(data) {
        const saveData = {
            ...data,
            version: '1.0.0',
            timestamp: Date.now()
        };

        try {
            localStorage.setItem(this.storageKey, JSON.stringify(saveData));
            return true;
        } catch (e) {
            console.error('Failed to save game:', e);
            return false;
        }
    }

    load() {
        try {
            const saveJson = localStorage.getItem(this.storageKey);
            if (!saveJson) return null;

            const data = JSON.parse(saveJson);

            // Version migration if needed
            if (data.version !== '1.0.0') {
                return this.migrate(data);
            }

            return data;
        } catch (e) {
            console.error('Failed to load save:', e);
            return null;
        }
    }

    delete() {
        localStorage.removeItem(this.storageKey);
    }

    exists() {
        return localStorage.getItem(this.storageKey) !== null;
    }

    migrate(data) {
        // Handle old save formats
        // Return migrated data
        return data;
    }

    startAutosave(getData, intervalMs = 30000) {
        this.stopAutosave();
        this.autosaveInterval = setInterval(() => {
            this.save(getData());
        }, intervalMs);
    }

    stopAutosave() {
        if (this.autosaveInterval) {
            clearInterval(this.autosaveInterval);
            this.autosaveInterval = null;
        }
    }

    // Multiple save slots
    saveToSlot(slot, data) {
        return this.save({ slot, ...data });
    }

    loadFromSlot(slot) {
        const allSaves = this.getAllSlots();
        return allSaves.find(s => s.slot === slot);
    }

    getAllSlots() {
        const saves = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key?.startsWith(this.storageKey)) {
                try {
                    saves.push(JSON.parse(localStorage.getItem(key)));
                } catch (e) {
                    // Skip invalid saves
                }
            }
        }
        return saves.sort((a, b) => b.timestamp - a.timestamp);
    }
}

// Usage
const saveManager = new SaveManager('myGame');

// Save game
saveManager.save({
    level: this.currentLevel,
    score: this.score,
    playerX: this.player.x,
    playerY: this.player.y,
    inventory: this.inventory,
    completedQuests: this.completedQuests
});

// Load game
const save = saveManager.load();
if (save) {
    this.score = save.score;
    this.player.setPosition(save.playerX, save.playerY);
}

// Autosave every 30 seconds
saveManager.startAutosave(() => ({
    level: this.currentLevel,
    score: this.score,
    // ... other data
}), 30000);
```

### IndexedDB for Large Saves

```javascript
// For games with large save data (levels, maps, etc.)
class IndexedDBSaveManager {
    constructor(dbName = 'gameDB', storeName = 'saves') {
        this.dbName = dbName;
        this.storeName = storeName;
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains(this.storeName)) {
                    db.createObjectStore(this.storeName, { keyPath: 'id' });
                }
            };
        });
    }

    async save(id, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const request = store.put({ id, data, timestamp: Date.now() });

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    async load(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const request = store.get(id);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result?.data || null);
        });
    }

    async delete(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const request = store.delete(id);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }
}

// Usage
const dbSave = new IndexedDBSaveManager();
await dbSave.init();
await dbSave.save('slot1', { level: 5, score: 1000 });
const data = await dbSave.load('slot1');
```

---

## Mobile and Touch Controls

### Virtual Joystick

```javascript
class VirtualJoystick {
    constructor(scene, x, y, options = {}) {
        this.scene = scene;
        this.baseX = x;
        this.baseY = y;

        const {
            baseRadius = 60,
            thumbRadius = 30,
            baseColor = 0x333333,
            thumbColor = 0x666666,
            baseAlpha = 0.5,
            thumbAlpha = 0.7,
            threshold = 0.1
        } = options;

        this.baseRadius = baseRadius;
        this.thumbRadius = thumbRadius;
        this.threshold = threshold;

        // Create base
        this.base = scene.add.circle(x, y, baseRadius, baseColor, baseAlpha);
        this.base.setScrollFactor(0);
        this.base.setDepth(1000);

        // Create thumb
        this.thumb = scene.add.circle(x, y, thumbRadius, thumbColor, thumbAlpha);
        this.thumb.setScrollFactor(0);
        this.thumb.setDepth(1001);

        // Input state
        this.vector = new Phaser.Math.Vector2(0, 0);
        this.isActive = false;
        this.pointerId = null;

        // Setup input
        scene.input.on('pointerdown', this.onPointerDown, this);
        scene.input.on('pointermove', this.onPointerMove, this);
        scene.input.on('pointerup', this.onPointerUp, this);
    }

    onPointerDown(pointer) {
        const distance = Phaser.Math.Distance.Between(
            pointer.x, pointer.y,
            this.baseX, this.baseY
        );

        if (distance <= this.baseRadius * 2) {
            this.isActive = true;
            this.pointerId = pointer.id;
            this.updateThumb(pointer.x, pointer.y);
        }
    }

    onPointerMove(pointer) {
        if (this.isActive && pointer.id === this.pointerId) {
            this.updateThumb(pointer.x, pointer.y);
        }
    }

    onPointerUp(pointer) {
        if (pointer.id === this.pointerId) {
            this.isActive = false;
            this.pointerId = null;
            this.resetThumb();
        }
    }

    updateThumb(x, y) {
        const dx = x - this.baseX;
        const dy = y - this.baseY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance > this.baseRadius) {
            // Clamp to base radius
            const angle = Math.atan2(dy, dx);
            this.thumb.x = this.baseX + Math.cos(angle) * this.baseRadius;
            this.thumb.y = this.baseY + Math.sin(angle) * this.baseRadius;
            this.vector.set(Math.cos(angle), Math.sin(angle));
        } else {
            this.thumb.x = x;
            this.thumb.y = y;
            this.vector.set(dx / this.baseRadius, dy / this.baseRadius);
        }

        // Apply threshold
        if (this.vector.length() < this.threshold) {
            this.vector.set(0, 0);
        }
    }

    resetThumb() {
        this.thumb.x = this.baseX;
        this.thumb.y = this.baseY;
        this.vector.set(0, 0);
    }

    get x() { return this.vector.x; }
    get y() { return this.vector.y; }

    setPosition(x, y) {
        this.baseX = x;
        this.baseY = y;
        this.base.setPosition(x, y);
        if (!this.isActive) {
            this.thumb.setPosition(x, y);
        }
    }

    setVisible(visible) {
        this.base.setVisible(visible);
        this.thumb.setVisible(visible);
    }

    destroy() {
        this.scene.input.off('pointerdown', this.onPointerDown, this);
        this.scene.input.off('pointermove', this.onPointerMove, this);
        this.scene.input.off('pointerup', this.onPointerUp, this);
        this.base.destroy();
        this.thumb.destroy();
    }
}

// Usage
create() {
    // Check if mobile
    this.isMobile = this.sys.game.device.os.android ||
                    this.sys.game.device.os.iOS ||
                    this.sys.game.device.input.touch;

    if (this.isMobile) {
        this.joystick = new VirtualJoystick(this, 120, 450);
        this.jumpButton = this.add.circle(680, 450, 40, 0x00ff00, 0.7);
        this.jumpButton.setScrollFactor(0);
        this.jumpButton.setDepth(1000);
        this.jumpButton.setInteractive();
        this.jumpButton.on('pointerdown', () => this.player.jump());
    }
}

update() {
    if (this.isMobile && this.joystick) {
        this.player.setVelocityX(this.joystick.x * 200);
    }
}
```

### Touch Gestures

```javascript
class GestureDetector {
    constructor(scene, options = {}) {
        this.scene = scene;
        this.swipeThreshold = options.swipeThreshold || 50;
        this.swipeTime = options.swipeTime || 300;
        this.tapTime = options.tapTime || 200;
        this.doubleTapTime = options.doubleTapTime || 300;

        this.startX = 0;
        this.startY = 0;
        this.startTime = 0;
        this.lastTapTime = 0;

        this.callbacks = {
            swipeLeft: [],
            swipeRight: [],
            swipeUp: [],
            swipeDown: [],
            tap: [],
            doubleTap: [],
            longPress: []
        };

        this.longPressTimer = null;

        scene.input.on('pointerdown', this.onPointerDown, this);
        scene.input.on('pointerup', this.onPointerUp, this);
    }

    onPointerDown(pointer) {
        this.startX = pointer.x;
        this.startY = pointer.y;
        this.startTime = Date.now();

        // Long press detection
        this.longPressTimer = this.scene.time.delayedCall(500, () => {
            this.emit('longPress', pointer);
        });
    }

    onPointerUp(pointer) {
        if (this.longPressTimer) {
            this.longPressTimer.destroy();
            this.longPressTimer = null;
        }

        const dx = pointer.x - this.startX;
        const dy = pointer.y - this.startY;
        const dt = Date.now() - this.startTime;

        const absDx = Math.abs(dx);
        const absDy = Math.abs(dy);

        // Check for swipe
        if (dt < this.swipeTime && (absDx > this.swipeThreshold || absDy > this.swipeThreshold)) {
            if (absDx > absDy) {
                if (dx > 0) {
                    this.emit('swipeRight', pointer);
                } else {
                    this.emit('swipeLeft', pointer);
                }
            } else {
                if (dy > 0) {
                    this.emit('swipeDown', pointer);
                } else {
                    this.emit('swipeUp', pointer);
                }
            }
        }
        // Check for tap
        else if (dt < this.tapTime && absDx < 10 && absDy < 10) {
            const now = Date.now();
            if (now - this.lastTapTime < this.doubleTapTime) {
                this.emit('doubleTap', pointer);
                this.lastTapTime = 0;
            } else {
                this.emit('tap', pointer);
                this.lastTapTime = now;
            }
        }
    }

    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
    }

    emit(event, pointer) {
        this.callbacks[event].forEach(cb => cb(pointer));
    }

    destroy() {
        this.scene.input.off('pointerdown', this.onPointerDown, this);
        this.scene.input.off('pointerup', this.onPointerUp, this);
    }
}

// Usage
create() {
    this.gestures = new GestureDetector(this);

    this.gestures.on('swipeLeft', () => this.player.moveLeft());
    this.gestures.on('swipeRight', () => this.player.moveRight());
    this.gestures.on('swipeUp', () => this.player.jump());
    this.gestures.on('tap', () => this.player.attack());
    this.gestures.on('doubleTap', () => this.player.specialAttack());
}
```

### Responsive Controls

```javascript
class ResponsiveControls {
    constructor(scene) {
        this.scene = scene;

        // Detect input method
        this.isMobile = this.detectMobile();
        this.hasGamepad = false;

        // Setup based on device
        if (this.isMobile) {
            this.setupTouchControls();
        } else {
            this.setupKeyboardControls();
        }

        this.setupGamepadDetection();
    }

    detectMobile() {
        return (
            this.scene.sys.game.device.os.android ||
            this.scene.sys.game.device.os.iOS ||
            (this.scene.sys.game.device.input.touch && window.innerWidth < 800)
        );
    }

    setupTouchControls() {
        const { width, height } = this.scene.scale;

        this.joystick = new VirtualJoystick(this.scene, 100, height - 100);

        // Action buttons
        this.buttonA = this.createButton(width - 100, height - 100, 'A', 0x00ff00);
        this.buttonB = this.createButton(width - 180, height - 60, 'B', 0xff0000);
    }

    createButton(x, y, label, color) {
        const button = this.scene.add.container(x, y);
        const bg = this.scene.add.circle(0, 0, 35, color, 0.7);
        const text = this.scene.add.text(0, 0, label, {
            fontSize: '24px',
            color: '#fff'
        }).setOrigin(0.5);

        button.add([bg, text]);
        button.setScrollFactor(0);
        button.setDepth(1000);

        bg.setInteractive();
        button.isPressed = false;

        bg.on('pointerdown', () => { button.isPressed = true; });
        bg.on('pointerup', () => { button.isPressed = false; });
        bg.on('pointerout', () => { button.isPressed = false; });

        return button;
    }

    setupKeyboardControls() {
        this.cursors = this.scene.input.keyboard.createCursorKeys();
        this.keys = this.scene.input.keyboard.addKeys({
            jump: Phaser.Input.Keyboard.KeyCodes.SPACE,
            attack: Phaser.Input.Keyboard.KeyCodes.X,
            special: Phaser.Input.Keyboard.KeyCodes.Z
        });
    }

    setupGamepadDetection() {
        this.scene.input.gamepad.on('connected', (pad) => {
            this.gamepad = pad;
            this.hasGamepad = true;
            // Optionally hide touch controls when gamepad connected
        });

        this.scene.input.gamepad.on('disconnected', () => {
            this.gamepad = null;
            this.hasGamepad = false;
        });
    }

    getInput() {
        const input = {
            horizontal: 0,
            vertical: 0,
            jump: false,
            attack: false,
            special: false
        };

        // Gamepad takes priority
        if (this.hasGamepad && this.gamepad) {
            input.horizontal = this.gamepad.leftStick.x;
            input.vertical = this.gamepad.leftStick.y;
            input.jump = this.gamepad.A;
            input.attack = this.gamepad.X;
            input.special = this.gamepad.Y;
        }
        // Touch controls
        else if (this.isMobile) {
            input.horizontal = this.joystick.x;
            input.vertical = this.joystick.y;
            input.jump = this.buttonA.isPressed;
            input.attack = this.buttonB.isPressed;
        }
        // Keyboard
        else {
            if (this.cursors.left.isDown) input.horizontal = -1;
            else if (this.cursors.right.isDown) input.horizontal = 1;

            if (this.cursors.up.isDown) input.vertical = -1;
            else if (this.cursors.down.isDown) input.vertical = 1;

            input.jump = this.keys.jump.isDown;
            input.attack = this.keys.attack.isDown;
            input.special = this.keys.special.isDown;
        }

        return input;
    }
}
```

---

## Particle Effects

### Basic Particles

```javascript
// In preload
this.load.image('particle', 'assets/images/particle.png');

// In create
this.particles = this.add.particles(0, 0, 'particle', {
    speed: 100,
    scale: { start: 1, end: 0 },
    lifespan: 1000,
    blendMode: 'ADD',
    frequency: 50,
    emitting: false
});

// Emit on event
this.particles.setPosition(this.player.x, this.player.y);
this.particles.explode(20);

// Follow player
this.particles.startFollow(this.player);
this.particles.start();
```

### Pre-configured Particle Effects

```javascript
// Explosion effect
createExplosion(x, y) {
    const particles = this.add.particles(x, y, 'particle', {
        speed: { min: 100, max: 300 },
        angle: { min: 0, max: 360 },
        scale: { start: 1, end: 0 },
        lifespan: 500,
        gravityY: 200,
        blendMode: 'ADD',
        tint: [0xff0000, 0xff6600, 0xffff00],
        emitting: false
    });

    particles.explode(30);

    // Cleanup
    this.time.delayedCall(1000, () => particles.destroy());
}

// Trail effect
createTrail(target) {
    return this.add.particles(0, 0, 'particle', {
        speed: 10,
        scale: { start: 0.5, end: 0 },
        alpha: { start: 0.5, end: 0 },
        lifespan: 300,
        blendMode: 'ADD',
        follow: target,
        frequency: 50
    });
}

// Coin collect effect
coinCollectEffect(x, y) {
    // Sparkle
    const sparkle = this.add.particles(x, y, 'sparkle', {
        speed: { min: 50, max: 100 },
        angle: { min: -120, max: -60 },
        scale: { start: 0.5, end: 0 },
        lifespan: 400,
        gravityY: -100,
        blendMode: 'ADD',
        emitting: false
    });

    sparkle.explode(10);

    // Score popup
    const text = this.add.text(x, y, '+10', {
        fontSize: '24px',
        color: '#ffd700',
        stroke: '#000',
        strokeThickness: 3
    }).setOrigin(0.5);

    this.tweens.add({
        targets: text,
        y: y - 50,
        alpha: 0,
        duration: 800,
        ease: 'Power2',
        onComplete: () => text.destroy()
    });

    this.time.delayedCall(500, () => sparkle.destroy());
}

// Damage numbers
showDamage(x, y, amount, isCritical = false) {
    const color = isCritical ? '#ff0000' : '#ffffff';
    const size = isCritical ? '32px' : '24px';

    const text = this.add.text(x, y, `-${amount}`, {
        fontSize: size,
        color: color,
        stroke: '#000',
        strokeThickness: 4
    }).setOrigin(0.5);

    if (isCritical) {
        text.setScale(0.5);
        this.tweens.add({
            targets: text,
            scale: 1.5,
            duration: 200,
            yoyo: true,
            ease: 'Power2'
        });
    }

    this.tweens.add({
        targets: text,
        y: y - 80,
        alpha: 0,
        duration: 1000,
        ease: 'Power2',
        onComplete: () => text.destroy()
    });
}
```

---

## Scene Transitions

### Basic Transitions

```javascript
// Fade transition
fadeToScene(sceneKey, data = {}) {
    this.cameras.main.fadeOut(500, 0, 0, 0);

    this.cameras.main.once('camerafadeoutcomplete', () => {
        this.scene.start(sceneKey, data);
    });
}

// In new scene's create()
create() {
    this.cameras.main.fadeIn(500, 0, 0, 0);
    // ... rest of create
}
```

### Advanced Transitions

```javascript
// TransitionManager.js
class TransitionManager {
    constructor(scene) {
        this.scene = scene;
    }

    // Circle wipe
    circleWipe(targetScene, data = {}, duration = 1000) {
        const { width, height } = this.scene.scale;
        const cx = width / 2;
        const cy = height / 2;
        const maxRadius = Math.sqrt(cx * cx + cy * cy);

        // Create mask graphics
        const mask = this.scene.add.graphics();
        mask.setScrollFactor(0);
        mask.setDepth(2000);

        // Animate circle shrinking
        let radius = maxRadius;
        const tween = this.scene.tweens.add({
            targets: { radius: maxRadius },
            radius: 0,
            duration: duration,
            ease: 'Power2',
            onUpdate: (tween) => {
                radius = tween.targets[0].radius;
                mask.clear();
                mask.fillStyle(0x000000);
                mask.fillRect(0, 0, width, height);
                mask.fillStyle(0x000000, 0);
                mask.beginPath();
                mask.arc(cx, cy, radius, 0, Math.PI * 2);
                mask.fill();
            },
            onComplete: () => {
                this.scene.scene.start(targetScene, data);
            }
        });
    }

    // Slide transition
    slideOut(direction, targetScene, data = {}, duration = 500) {
        const { width, height } = this.scene.scale;
        const camera = this.scene.cameras.main;

        const targets = {
            left: { x: -width },
            right: { x: width },
            up: { y: -height },
            down: { y: height }
        };

        this.scene.tweens.add({
            targets: camera,
            scrollX: targets[direction].x || 0,
            scrollY: targets[direction].y || 0,
            duration: duration,
            ease: 'Power2',
            onComplete: () => {
                this.scene.scene.start(targetScene, data);
            }
        });
    }

    // Pixelate transition
    pixelate(targetScene, data = {}, duration = 1000) {
        // Add post-fx pipeline for pixelation
        // Note: Requires custom pipeline or Phaser plugin

        const camera = this.scene.cameras.main;
        const fx = camera.postFX.addPixelate(0);

        this.scene.tweens.add({
            targets: fx,
            amount: 20,
            duration: duration / 2,
            ease: 'Power2',
            yoyo: true,
            onYoyo: () => {
                this.scene.scene.start(targetScene, data);
            }
        });
    }

    // Flash transition
    flash(targetScene, data = {}, color = 0xffffff) {
        const camera = this.scene.cameras.main;

        camera.flash(500, (color >> 16) & 0xff, (color >> 8) & 0xff, color & 0xff);

        this.scene.time.delayedCall(250, () => {
            this.scene.scene.start(targetScene, data);
        });
    }
}

// Usage
create() {
    this.transitions = new TransitionManager(this);

    // Later...
    this.transitions.circleWipe('GameScene', { level: 1 });
}
```

---

## Common Game Patterns by Genre

### Platformer

```javascript
update() {
    const onGround = this.player.body.blocked.down;

    // Horizontal movement with acceleration
    if (this.cursors.left.isDown) {
        this.player.body.setAccelerationX(-600);
        this.player.setFlipX(true);
    } else if (this.cursors.right.isDown) {
        this.player.body.setAccelerationX(600);
        this.player.setFlipX(false);
    } else {
        this.player.body.setAccelerationX(0);
        // Apply friction when not moving
        this.player.body.setDragX(800);
    }

    // Animations
    if (onGround) {
        if (Math.abs(this.player.body.velocity.x) > 10) {
            this.player.play('walk', true);
        } else {
            this.player.play('idle', true);
        }
    }

    // Variable jump height
    if (Phaser.Input.Keyboard.JustDown(this.cursors.up) && onGround) {
        this.player.setVelocityY(-500);
        this.player.play('jump');
        this.jumpTimer = this.time.now;
    }

    // Hold jump for higher
    if (this.cursors.up.isDown && this.player.body.velocity.y < 0) {
        if (this.time.now - this.jumpTimer < 250) {
            this.player.body.velocity.y -= 15;
        }
    }

    // Fall animation
    if (!onGround && this.player.body.velocity.y > 0) {
        this.player.play('fall', true);
    }

    // Coyote time (grace period after leaving platform)
    if (onGround) {
        this.lastGroundedTime = this.time.now;
    }

    const coyoteTime = 150; // ms
    const canJump = this.time.now - this.lastGroundedTime < coyoteTime;

    if (Phaser.Input.Keyboard.JustDown(this.cursors.up) && canJump) {
        this.player.setVelocityY(-500);
    }
}

// Wall jump
checkWallJump() {
    const touchingWall = this.player.body.blocked.left || this.player.body.blocked.right;

    if (touchingWall && !this.player.body.blocked.down) {
        // Wall slide
        this.player.body.velocity.y = Math.min(this.player.body.velocity.y, 100);

        if (Phaser.Input.Keyboard.JustDown(this.cursors.up)) {
            const direction = this.player.body.blocked.left ? 1 : -1;
            this.player.setVelocity(direction * 300, -450);
            this.player.setFlipX(direction < 0);
        }
    }
}
```

### Top-Down RPG

```javascript
update() {
    const speed = 200;
    this.player.body.setVelocity(0);

    // 8-directional movement
    if (this.cursors.left.isDown) {
        this.player.body.setVelocityX(-speed);
    } else if (this.cursors.right.isDown) {
        this.player.body.setVelocityX(speed);
    }

    if (this.cursors.up.isDown) {
        this.player.body.setVelocityY(-speed);
    } else if (this.cursors.down.isDown) {
        this.player.body.setVelocityY(speed);
    }

    // Normalize diagonal movement
    this.player.body.velocity.normalize().scale(speed);

    // Animation based on direction
    if (this.player.body.velocity.x !== 0 || this.player.body.velocity.y !== 0) {
        if (Math.abs(this.player.body.velocity.x) > Math.abs(this.player.body.velocity.y)) {
            if (this.player.body.velocity.x < 0) {
                this.player.play('walk-left', true);
            } else {
                this.player.play('walk-right', true);
            }
        } else {
            if (this.player.body.velocity.y < 0) {
                this.player.play('walk-up', true);
            } else {
                this.player.play('walk-down', true);
            }
        }
        this.lastDirection = this.getDirection();
    } else {
        this.player.play(`idle-${this.lastDirection}`, true);
    }
}

getDirection() {
    const vx = this.player.body.velocity.x;
    const vy = this.player.body.velocity.y;

    if (Math.abs(vx) > Math.abs(vy)) {
        return vx < 0 ? 'left' : 'right';
    } else {
        return vy < 0 ? 'up' : 'down';
    }
}

// NPC interaction
interactWithNPC(player, npc) {
    if (Phaser.Input.Keyboard.JustDown(this.keys.interact)) {
        this.showDialog(npc.getData('dialogue'));
    }
}
```

### Shooter / Bullets

```javascript
create() {
    // Bullet pool
    this.bullets = this.physics.add.group({
        defaultKey: 'bullet',
        maxSize: 50,
        createCallback: (bullet) => {
            bullet.setData('damage', 10);
        }
    });

    // Enemy bullets
    this.enemyBullets = this.physics.add.group({
        defaultKey: 'enemy-bullet',
        maxSize: 100
    });

    // Collisions
    this.physics.add.overlap(this.bullets, this.enemies, this.bulletHitEnemy, null, this);
    this.physics.add.overlap(this.enemyBullets, this.player, this.bulletHitPlayer, null, this);

    // Shooting
    this.lastFired = 0;
    this.fireRate = 150; // ms between shots
}

update(time) {
    // Auto-fire or click to fire
    if (this.input.activePointer.isDown && time > this.lastFired + this.fireRate) {
        this.shoot(this.input.activePointer.x, this.input.activePointer.y);
        this.lastFired = time;
    }
}

shoot(targetX, targetY) {
    const bullet = this.bullets.get(this.player.x, this.player.y);
    if (!bullet) return;

    bullet.setActive(true);
    bullet.setVisible(true);
    bullet.body.enable = true;

    // Calculate angle to target
    const angle = Phaser.Math.Angle.Between(
        this.player.x, this.player.y,
        targetX, targetY
    );

    // Set rotation to face direction
    bullet.setRotation(angle);

    // Set velocity
    this.physics.velocityFromRotation(angle, 500, bullet.body.velocity);

    // Auto-destroy off-screen
    bullet.setData('lifespan', 2000);
}

bulletHitEnemy(bullet, enemy) {
    // Deactivate bullet
    bullet.setActive(false);
    bullet.setVisible(false);
    bullet.body.enable = false;

    // Damage enemy
    enemy.takeDamage(bullet.getData('damage'));

    // Hit effect
    this.createHitEffect(bullet.x, bullet.y);
}

// Spread shot
shootSpread(targetX, targetY, count = 3, spreadAngle = 15) {
    const baseAngle = Phaser.Math.Angle.Between(
        this.player.x, this.player.y,
        targetX, targetY
    );

    const startAngle = baseAngle - Phaser.Math.DegToRad(spreadAngle * (count - 1) / 2);

    for (let i = 0; i < count; i++) {
        const angle = startAngle + Phaser.Math.DegToRad(spreadAngle * i);
        this.shootAtAngle(angle);
    }
}

shootAtAngle(angle) {
    const bullet = this.bullets.get(this.player.x, this.player.y);
    if (!bullet) return;

    bullet.setActive(true);
    bullet.setVisible(true);
    bullet.body.enable = true;
    bullet.setRotation(angle);
    this.physics.velocityFromRotation(angle, 500, bullet.body.velocity);
}
```

### Puzzle Game

```javascript
// Grid-based puzzle
class PuzzleGrid {
    constructor(scene, rows, cols, tileSize) {
        this.scene = scene;
        this.rows = rows;
        this.cols = cols;
        this.tileSize = tileSize;
        this.grid = [];
        this.selected = null;

        this.initGrid();
    }

    initGrid() {
        for (let row = 0; row < this.rows; row++) {
            this.grid[row] = [];
            for (let col = 0; col < this.cols; col++) {
                const x = col * this.tileSize + this.tileSize / 2;
                const y = row * this.tileSize + this.tileSize / 2;
                const type = Phaser.Math.Between(0, 4);

                const tile = this.scene.add.sprite(x, y, 'tiles', type);
                tile.setData({ row, col, type });
                tile.setInteractive();

                tile.on('pointerdown', () => this.onTileClick(tile));

                this.grid[row][col] = tile;
            }
        }
    }

    onTileClick(tile) {
        if (!this.selected) {
            this.selected = tile;
            tile.setTint(0xffff00);
        } else {
            const row1 = this.selected.getData('row');
            const col1 = this.selected.getData('col');
            const row2 = tile.getData('row');
            const col2 = tile.getData('col');

            // Check if adjacent
            if (Math.abs(row1 - row2) + Math.abs(col1 - col2) === 1) {
                this.swapTiles(this.selected, tile);
            }

            this.selected.clearTint();
            this.selected = null;
        }
    }

    swapTiles(tile1, tile2) {
        const row1 = tile1.getData('row');
        const col1 = tile1.getData('col');
        const row2 = tile2.getData('row');
        const col2 = tile2.getData('col');

        // Swap in grid
        this.grid[row1][col1] = tile2;
        this.grid[row2][col2] = tile1;

        // Update data
        tile1.setData({ row: row2, col: col2 });
        tile2.setData({ row: row1, col: col1 });

        // Animate swap
        const x1 = tile1.x;
        const y1 = tile1.y;
        const x2 = tile2.x;
        const y2 = tile2.y;

        this.scene.tweens.add({
            targets: tile1,
            x: x2,
            y: y2,
            duration: 200,
            ease: 'Power2'
        });

        this.scene.tweens.add({
            targets: tile2,
            x: x1,
            y: y1,
            duration: 200,
            ease: 'Power2',
            onComplete: () => this.checkMatches()
        });
    }

    checkMatches() {
        const matches = [];

        // Check horizontal matches
        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols - 2; col++) {
                const type = this.grid[row][col].getData('type');
                if (
                    this.grid[row][col + 1].getData('type') === type &&
                    this.grid[row][col + 2].getData('type') === type
                ) {
                    matches.push(
                        { row, col },
                        { row, col: col + 1 },
                        { row, col: col + 2 }
                    );
                }
            }
        }

        // Check vertical matches
        for (let row = 0; row < this.rows - 2; row++) {
            for (let col = 0; col < this.cols; col++) {
                const type = this.grid[row][col].getData('type');
                if (
                    this.grid[row + 1][col].getData('type') === type &&
                    this.grid[row + 2][col].getData('type') === type
                ) {
                    matches.push(
                        { row, col },
                        { row: row + 1, col },
                        { row: row + 2, col }
                    );
                }
            }
        }

        if (matches.length > 0) {
            this.removeMatches(matches);
        }
    }

    removeMatches(matches) {
        // Remove duplicates
        const unique = [...new Set(matches.map(m => `${m.row},${m.col}`))];

        unique.forEach(key => {
            const [row, col] = key.split(',').map(Number);
            const tile = this.grid[row][col];

            this.scene.tweens.add({
                targets: tile,
                scale: 0,
                alpha: 0,
                duration: 200,
                onComplete: () => {
                    tile.destroy();
                    this.grid[row][col] = null;
                }
            });
        });

        // After removal, drop tiles and fill
        this.scene.time.delayedCall(250, () => {
            this.dropTiles();
            this.fillGrid();
        });
    }

    dropTiles() {
        for (let col = 0; col < this.cols; col++) {
            let emptyRow = this.rows - 1;

            for (let row = this.rows - 1; row >= 0; row--) {
                if (this.grid[row][col]) {
                    if (row !== emptyRow) {
                        const tile = this.grid[row][col];
                        this.grid[emptyRow][col] = tile;
                        this.grid[row][col] = null;

                        tile.setData('row', emptyRow);

                        this.scene.tweens.add({
                            targets: tile,
                            y: emptyRow * this.tileSize + this.tileSize / 2,
                            duration: 200,
                            ease: 'Bounce'
                        });
                    }
                    emptyRow--;
                }
            }
        }
    }

    fillGrid() {
        for (let col = 0; col < this.cols; col++) {
            for (let row = 0; row < this.rows; row++) {
                if (!this.grid[row][col]) {
                    const x = col * this.tileSize + this.tileSize / 2;
                    const y = row * this.tileSize + this.tileSize / 2;
                    const type = Phaser.Math.Between(0, 4);

                    const tile = this.scene.add.sprite(x, -this.tileSize, 'tiles', type);
                    tile.setData({ row, col, type });
                    tile.setInteractive();
                    tile.on('pointerdown', () => this.onTileClick(tile));

                    this.grid[row][col] = tile;

                    this.scene.tweens.add({
                        targets: tile,
                        y: y,
                        duration: 300,
                        ease: 'Bounce',
                        delay: col * 50
                    });
                }
            }
        }

        // Check for new matches after fill
        this.scene.time.delayedCall(400, () => this.checkMatches());
    }
}
```

---

## Performance Optimization

### Object Pooling

```javascript
// For frequently created/destroyed objects
create() {
    this.enemyPool = this.physics.add.group({
        classType: Enemy,
        maxSize: 50,
        runChildUpdate: true
    });
}

spawnEnemy(x, y) {
    const enemy = this.enemyPool.get(x, y);
    if (enemy) {
        enemy.spawn(x, y);
    }
}

// In Enemy class
spawn(x, y) {
    this.setPosition(x, y);
    this.setActive(true);
    this.setVisible(true);
    this.body.enable = true;
    this.health = this.maxHealth;
}

die() {
    this.setActive(false);
    this.setVisible(false);
    this.body.enable = false;
}
```

### Performance Tips

```javascript
// 1. Disable updates for off-screen objects
update() {
    this.enemies.children.each((enemy) => {
        const inView = this.cameras.main.worldView.contains(enemy.x, enemy.y);
        enemy.body.enable = inView;
        enemy.setActive(inView);
    });
}

// 2. Use static groups for non-moving objects
const platforms = this.physics.add.staticGroup();

// 3. Texture atlases for fewer draw calls
this.load.atlas('sprites', 'sprites.png', 'sprites.json');

// 4. Reduce physics checks
this.physics.world.setBounds(0, 0, 800, 600);
this.physics.world.OVERLAP_BIAS = 8; // Adjust for your game

// 5. Use WebGL renderer (default)
const config = {
    type: Phaser.WEBGL,
    // ...
};

// 6. Batch similar objects
const batch = this.add.blitter(0, 0, 'tiles');
for (let i = 0; i < 1000; i++) {
    batch.create(x, y);
}

// 7. Avoid creating objects in update()
// BAD
update() {
    const v = new Phaser.Math.Vector2(1, 0); // Creates new object every frame
}

// GOOD
create() {
    this.tempVec = new Phaser.Math.Vector2();
}
update() {
    this.tempVec.set(1, 0); // Reuse existing object
}

// 8. Use integer positions for pixel art
sprite.x = Math.round(sprite.x);
sprite.y = Math.round(sprite.y);

// 9. Profile with browser dev tools
// Enable physics debug sparingly
physics: {
    arcade: { debug: process.env.NODE_ENV === 'development' }
}
```

---

## Build and Export

### Development

```bash
npm run dev    # Start dev server with hot reload
```

### Production Build

```bash
npm run build  # Creates optimized build in dist/
```

### Export for itch.io

1. Run `npm run build`
2. Zip the contents of the `dist/` folder
3. Upload to itch.io as HTML5 game
4. Set "Embed in page" and configure viewport size

### Common itch.io Settings

- **Viewport dimensions**: Match your game resolution (e.g., 800x600)
- **Fullscreen button**: Enable for better experience
- **Mobile friendly**: Enable if you handle touch input
- **SharedArrayBuffer**: Usually not needed unless using Web Workers

### PWA Support

```javascript
// vite.config.js with PWA plugin
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
    plugins: [
        VitePWA({
            registerType: 'autoUpdate',
            manifest: {
                name: 'My Game',
                short_name: 'Game',
                start_url: '/',
                display: 'fullscreen',
                background_color: '#000000',
                theme_color: '#000000',
                icons: [
                    { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
                    { src: 'icon-512.png', sizes: '512x512', type: 'image/png' }
                ]
            }
        })
    ]
});
```

---

## Troubleshooting

### Common Issues

1. **Assets not loading**: Check paths are relative to index.html
2. **Sprite not showing**: Check depth/z-order, alpha, visibility
3. **Physics not working**: Ensure sprite was created with `this.physics.add`
4. **Animation not playing**: Verify animation key matches, check if animation exists
5. **Mobile performance**: Reduce particle counts, simplify physics
6. **Audio not playing**: Handle browser autoplay policy with user interaction

### Debug Mode

```javascript
// In config
physics: {
    default: 'arcade',
    arcade: {
        debug: true  // Shows hitboxes, velocities
    }
}

// In scene
this.debugText = this.add.text(10, 10, '', { fontSize: '16px', color: '#fff' })
    .setScrollFactor(0)
    .setDepth(1000);

update() {
    this.debugText.setText([
        `FPS: ${Math.round(this.game.loop.actualFps)}`,
        `Player: ${Math.round(this.player.x)}, ${Math.round(this.player.y)}`,
        `Velocity: ${Math.round(this.player.body.velocity.x)}, ${Math.round(this.player.body.velocity.y)}`,
        `Active enemies: ${this.enemies.countActive()}`
    ].join('\n'));
}
```

### Memory Debugging

```javascript
// Check for memory leaks
create() {
    // Log active objects periodically
    this.time.addEvent({
        delay: 5000,
        loop: true,
        callback: () => {
            console.log({
                sprites: this.children.list.filter(c => c instanceof Phaser.GameObjects.Sprite).length,
                physics: this.physics.world.bodies.size,
                tweens: this.tweens.getAllTweens().length
            });
        }
    });
}

// Clean up properly
shutdown() {
    // Remove event listeners
    this.events.off('playerDied');
    this.input.keyboard.off('keydown-P');

    // Stop all tweens
    this.tweens.killAll();

    // Clear groups
    this.enemies.clear(true, true);
}
```

---

## Resources

- [Phaser 3 Documentation](https://photonstorm.github.io/phaser3-docs/)
- [Phaser 3 Examples](https://phaser.io/examples)
- [Phaser 3 API](https://newdocs.phaser.io/docs/3.80.0)
- [Phaser Discord](https://discord.gg/phaser)
- [Phaser Labs](https://labs.phaser.io/)
