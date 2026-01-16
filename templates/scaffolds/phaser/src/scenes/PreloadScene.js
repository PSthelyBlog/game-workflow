import Phaser from 'phaser';

/**
 * PreloadScene - Loads all game assets with a progress bar
 *
 * This scene should:
 * - Display a loading progress indicator
 * - Load all game assets (images, audio, spritesheets, etc.)
 * - Transition to MenuScene when complete
 */
export class PreloadScene extends Phaser.Scene {
    constructor() {
        super({ key: 'PreloadScene' });
    }

    preload() {
        // Create loading progress bar
        const width = this.cameras.main.width;
        const height = this.cameras.main.height;

        // Progress bar background
        const progressBarBg = this.add.rectangle(
            width / 2,
            height / 2,
            320,
            30,
            0x222222
        );

        // Progress bar fill
        const progressBar = this.add.rectangle(
            width / 2 - 150,
            height / 2,
            0,
            20,
            0x4a9fff
        );
        progressBar.setOrigin(0, 0.5);

        // Loading text
        const loadingText = this.add.text(width / 2, height / 2 - 50, 'Loading...', {
            fontSize: '24px',
            color: '#ffffff'
        });
        loadingText.setOrigin(0.5);

        // Percent text
        const percentText = this.add.text(width / 2, height / 2 + 50, '0%', {
            fontSize: '18px',
            color: '#ffffff'
        });
        percentText.setOrigin(0.5);

        // Update progress bar as assets load
        this.load.on('progress', (value) => {
            progressBar.width = 300 * value;
            percentText.setText(`${Math.round(value * 100)}%`);
        });

        // Clean up when loading complete
        this.load.on('complete', () => {
            progressBarBg.destroy();
            progressBar.destroy();
            loadingText.destroy();
            percentText.destroy();
        });

        // ==============================
        // LOAD YOUR GAME ASSETS HERE
        // ==============================

        // Example asset loading:
        // this.load.image('player', 'assets/images/player.png');
        // this.load.spritesheet('player-walk', 'assets/images/player-walk.png', {
        //     frameWidth: 32,
        //     frameHeight: 32
        // });
        // this.load.audio('bgm', 'assets/audio/background.mp3');
        // this.load.audio('jump', 'assets/audio/jump.wav');
    }

    create() {
        // Create any animations here
        // Example:
        // this.anims.create({
        //     key: 'walk',
        //     frames: this.anims.generateFrameNumbers('player-walk', { start: 0, end: 7 }),
        //     frameRate: 10,
        //     repeat: -1
        // });

        // Transition to the menu scene
        this.scene.start('MenuScene');
    }
}
