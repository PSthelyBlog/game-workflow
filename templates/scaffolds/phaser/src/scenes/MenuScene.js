import Phaser from 'phaser';

/**
 * MenuScene - Main menu screen
 *
 * This scene should:
 * - Display the game title
 * - Show start game button/prompt
 * - Optionally show settings, credits, etc.
 */
export class MenuScene extends Phaser.Scene {
    constructor() {
        super({ key: 'MenuScene' });
    }

    create() {
        const width = this.cameras.main.width;
        const height = this.cameras.main.height;

        // Game title
        const title = this.add.text(width / 2, height / 3, 'PHASER GAME', {
            fontSize: '48px',
            fontStyle: 'bold',
            color: '#ffffff',
            stroke: '#000000',
            strokeThickness: 4
        });
        title.setOrigin(0.5);

        // Start button
        const startButton = this.add.text(width / 2, height / 2, 'START GAME', {
            fontSize: '32px',
            color: '#4a9fff',
            backgroundColor: '#222222',
            padding: { x: 20, y: 10 }
        });
        startButton.setOrigin(0.5);
        startButton.setInteractive({ useHandCursor: true });

        // Button hover effects
        startButton.on('pointerover', () => {
            startButton.setColor('#ffffff');
            startButton.setBackgroundColor('#4a9fff');
        });

        startButton.on('pointerout', () => {
            startButton.setColor('#4a9fff');
            startButton.setBackgroundColor('#222222');
        });

        // Start game on click
        startButton.on('pointerdown', () => {
            this.scene.start('GameScene');
        });

        // Also start on spacebar or enter
        this.input.keyboard.once('keydown-SPACE', () => {
            this.scene.start('GameScene');
        });

        this.input.keyboard.once('keydown-ENTER', () => {
            this.scene.start('GameScene');
        });

        // Instructions
        const instructions = this.add.text(width / 2, height - 50, 'Press SPACE or click to start', {
            fontSize: '16px',
            color: '#888888'
        });
        instructions.setOrigin(0.5);
    }
}
