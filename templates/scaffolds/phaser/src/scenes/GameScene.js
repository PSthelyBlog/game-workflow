import Phaser from 'phaser';

/**
 * GameScene - Main gameplay scene
 *
 * This is where your game logic lives. Customize this scene based on your
 * game design document (GDD).
 *
 * Key methods:
 * - create(): Set up game objects, physics, input handlers
 * - update(time, delta): Game loop - called every frame
 */
export class GameScene extends Phaser.Scene {
    constructor() {
        super({ key: 'GameScene' });

        // Game state
        this.score = 0;
        this.isGameOver = false;
    }

    create() {
        const width = this.cameras.main.width;
        const height = this.cameras.main.height;

        // ==============================
        // SET UP YOUR GAME HERE
        // ==============================

        // Example: Create a simple player placeholder
        this.player = this.add.rectangle(width / 2, height / 2, 50, 50, 0x4a9fff);
        this.physics.add.existing(this.player);
        this.player.body.setCollideWorldBounds(true);

        // Example: Set up keyboard input
        this.cursors = this.input.keyboard.createCursorKeys();

        // Example: WASD keys
        this.wasd = this.input.keyboard.addKeys({
            up: Phaser.Input.Keyboard.KeyCodes.W,
            down: Phaser.Input.Keyboard.KeyCodes.S,
            left: Phaser.Input.Keyboard.KeyCodes.A,
            right: Phaser.Input.Keyboard.KeyCodes.D
        });

        // Score display
        this.scoreText = this.add.text(16, 16, 'Score: 0', {
            fontSize: '24px',
            color: '#ffffff'
        });

        // Instructions
        this.add.text(16, height - 40, 'Arrow keys or WASD to move | ESC to pause', {
            fontSize: '14px',
            color: '#888888'
        });

        // Pause on ESC
        this.input.keyboard.on('keydown-ESC', () => {
            this.togglePause();
        });
    }

    update(time, delta) {
        if (this.isGameOver) return;

        // ==============================
        // UPDATE YOUR GAME LOGIC HERE
        // ==============================

        const speed = 300;
        const body = this.player.body;

        // Reset velocity
        body.setVelocity(0);

        // Horizontal movement
        if (this.cursors.left.isDown || this.wasd.left.isDown) {
            body.setVelocityX(-speed);
        } else if (this.cursors.right.isDown || this.wasd.right.isDown) {
            body.setVelocityX(speed);
        }

        // Vertical movement
        if (this.cursors.up.isDown || this.wasd.up.isDown) {
            body.setVelocityY(-speed);
        } else if (this.cursors.down.isDown || this.wasd.down.isDown) {
            body.setVelocityY(speed);
        }

        // Normalize diagonal movement
        body.velocity.normalize().scale(speed);
    }

    /**
     * Add points to the score
     * @param {number} points - Points to add
     */
    addScore(points) {
        this.score += points;
        this.scoreText.setText(`Score: ${this.score}`);
    }

    /**
     * Toggle pause state
     */
    togglePause() {
        if (this.scene.isPaused()) {
            this.scene.resume();
        } else {
            this.scene.pause();
            // Optionally show a pause menu here
        }
    }

    /**
     * Handle game over
     */
    gameOver() {
        this.isGameOver = true;

        const width = this.cameras.main.width;
        const height = this.cameras.main.height;

        // Game over text
        const gameOverText = this.add.text(width / 2, height / 2 - 50, 'GAME OVER', {
            fontSize: '48px',
            fontStyle: 'bold',
            color: '#ff4444'
        });
        gameOverText.setOrigin(0.5);

        // Final score
        const finalScore = this.add.text(width / 2, height / 2 + 10, `Final Score: ${this.score}`, {
            fontSize: '24px',
            color: '#ffffff'
        });
        finalScore.setOrigin(0.5);

        // Restart prompt
        const restartText = this.add.text(width / 2, height / 2 + 70, 'Press SPACE to restart', {
            fontSize: '20px',
            color: '#4a9fff'
        });
        restartText.setOrigin(0.5);

        // Restart on space
        this.input.keyboard.once('keydown-SPACE', () => {
            this.score = 0;
            this.isGameOver = false;
            this.scene.restart();
        });
    }
}
