# Phaser.js Game Development Skill

This skill provides Claude Code with comprehensive knowledge for implementing Phaser.js games. Use this when building browser-based games with Phaser 3.

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
│   └── utils/              # Helpers
│       ├── Constants.js    # Game constants
│       └── Helpers.js      # Utility functions
└── assets/
    ├── images/             # Sprites, backgrounds, UI
    ├── audio/              # Music and sound effects
    ├── fonts/              # Custom fonts (bitmap or web)
    └── data/               # JSON data files (levels, dialogue)
```

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
if (sprite.anims.currentAnim.key === 'walk') {
    // ...
}

// Stop animation
sprite.stop();
```

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

### Touch/Mobile

```javascript
// Touch is handled automatically via pointer events
// For multitouch:
this.input.addPointer(1);  // Support 2 touches (default is 1)

this.input.on('pointerdown', (pointer) => {
    if (pointer.x < this.cameras.main.width / 2) {
        // Left side touched
    } else {
        // Right side touched
    }
});

// Virtual joystick (using plugin or custom)
// Consider: https://github.com/rexrainbow/phaser3-rex-notes/blob/master/docs/docs/virtualjoystick.md
```

## Audio

### Loading Audio

```javascript
// In preload
this.load.audio('bgm', 'assets/audio/music.mp3');
this.load.audio('jump', ['assets/audio/jump.ogg', 'assets/audio/jump.mp3']);
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
```

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
```

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
        this.spawnEnemy(point.x, point.y);
    }
});
```

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
    constructor(scene, x, y, maxHealth) {
        this.scene = scene;
        this.maxHealth = maxHealth;
        this.currentHealth = maxHealth;

        this.bg = scene.add.rectangle(x, y, 200, 20, 0x222222);
        this.bar = scene.add.rectangle(x - 98, y, 196, 16, 0x00ff00);
        this.bar.setOrigin(0, 0.5);
    }

    setHealth(value) {
        this.currentHealth = Phaser.Math.Clamp(value, 0, this.maxHealth);
        const percent = this.currentHealth / this.maxHealth;
        this.bar.width = 196 * percent;

        // Color based on health
        if (percent > 0.6) {
            this.bar.setFillStyle(0x00ff00);
        } else if (percent > 0.3) {
            this.bar.setFillStyle(0xffff00);
        } else {
            this.bar.setFillStyle(0xff0000);
        }
    }
}
```

## Common Game Patterns by Genre

### Platformer

```javascript
update() {
    const onGround = this.player.body.blocked.down;

    // Horizontal movement
    if (this.cursors.left.isDown) {
        this.player.setVelocityX(-200);
        this.player.setFlipX(true);
        if (onGround) this.player.play('walk', true);
    } else if (this.cursors.right.isDown) {
        this.player.setVelocityX(200);
        this.player.setFlipX(false);
        if (onGround) this.player.play('walk', true);
    } else {
        this.player.setVelocityX(0);
        if (onGround) this.player.play('idle', true);
    }

    // Jump
    if (this.cursors.up.isDown && onGround) {
        this.player.setVelocityY(-400);
        this.player.play('jump');
    }

    // Fall animation
    if (!onGround && this.player.body.velocity.y > 0) {
        this.player.play('fall', true);
    }
}
```

### Top-Down Movement

```javascript
update() {
    const speed = 200;
    this.player.body.setVelocity(0);

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
}
```

### Shooting / Bullets

```javascript
create() {
    this.bullets = this.physics.add.group({
        defaultKey: 'bullet',
        maxSize: 20  // Object pooling
    });

    this.input.on('pointerdown', (pointer) => {
        this.shoot(pointer.x, pointer.y);
    });
}

shoot(targetX, targetY) {
    const bullet = this.bullets.get(this.player.x, this.player.y);
    if (!bullet) return;  // Pool exhausted

    bullet.setActive(true);
    bullet.setVisible(true);
    bullet.body.enable = true;

    // Calculate angle to target
    const angle = Phaser.Math.Angle.Between(
        this.player.x, this.player.y,
        targetX, targetY
    );

    // Set velocity towards target
    this.physics.velocityFromRotation(angle, 400, bullet.body.velocity);

    // Destroy when off-screen
    bullet.setData('lifespan', 2000);
}

update(time, delta) {
    this.bullets.children.each((bullet) => {
        if (!bullet.active) return;

        const lifespan = bullet.getData('lifespan') - delta;
        bullet.setData('lifespan', lifespan);

        if (lifespan <= 0) {
            bullet.setActive(false);
            bullet.setVisible(false);
            bullet.body.enable = false;
        }
    });
}
```

### Object Pooling

```javascript
// For frequently created/destroyed objects (bullets, particles, enemies)
create() {
    this.enemyPool = this.physics.add.group({
        classType: Enemy,
        maxSize: 50,
        runChildUpdate: true  // Calls update() on each active child
    });
}

spawnEnemy(x, y) {
    const enemy = this.enemyPool.get(x, y);
    if (enemy) {
        enemy.spawn(x, y);  // Custom method to initialize
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
    // Returns to pool automatically
}
```

## Save/Load Game State

```javascript
// Save to localStorage
saveGame() {
    const saveData = {
        level: this.currentLevel,
        score: this.score,
        playerX: this.player.x,
        playerY: this.player.y,
        inventory: this.inventory,
        timestamp: Date.now()
    };

    localStorage.setItem('gameSave', JSON.stringify(saveData));
}

// Load from localStorage
loadGame() {
    const saveJson = localStorage.getItem('gameSave');
    if (!saveJson) return null;

    try {
        return JSON.parse(saveJson);
    } catch (e) {
        console.error('Failed to load save:', e);
        return null;
    }
}

// Use in scene
create() {
    const save = this.loadGame();
    if (save) {
        this.score = save.score;
        this.player.setPosition(save.playerX, save.playerY);
    }
}
```

## Performance Tips

1. **Use Object Pools**: Reuse objects instead of create/destroy
2. **Texture Atlases**: Combine sprites into atlas for fewer draw calls
3. **Minimize Physics Bodies**: Disable physics on off-screen objects
4. **Use Static Groups**: For non-moving collision objects
5. **Cull Off-Screen**: `camera.cull = true` (automatic in most cases)
6. **Reduce Draw Calls**: Group similar objects, use batching

```javascript
// Disable updates for off-screen objects
update() {
    this.enemies.children.each((enemy) => {
        const inView = this.cameras.main.worldView.contains(enemy.x, enemy.y);
        enemy.body.enable = inView;
        enemy.setActive(inView);
    });
}
```

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

## Troubleshooting

### Common Issues

1. **Assets not loading**: Check paths are relative to index.html
2. **Sprite not showing**: Check depth/z-order, alpha, visibility
3. **Physics not working**: Ensure sprite was created with `this.physics.add`
4. **Animation not playing**: Verify animation key matches, check if animation exists
5. **Mobile performance**: Reduce particle counts, simplify physics

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
this.add.text(10, 10, '', { fontSize: '16px', color: '#fff' })
    .setScrollFactor(0)
    .setDepth(1000);

update() {
    this.debugText.setText([
        `FPS: ${Math.round(this.game.loop.actualFps)}`,
        `Player: ${Math.round(this.player.x)}, ${Math.round(this.player.y)}`,
        `Velocity: ${Math.round(this.player.body.velocity.x)}, ${Math.round(this.player.body.velocity.y)}`
    ].join('\n'));
}
```

## Resources

- [Phaser 3 Documentation](https://photonstorm.github.io/phaser3-docs/)
- [Phaser 3 Examples](https://phaser.io/examples)
- [Phaser 3 API](https://newdocs.phaser.io/docs/3.80.0)
- [Phaser Discord](https://discord.gg/phaser)
