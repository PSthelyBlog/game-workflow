import Phaser from 'phaser';

/**
 * BootScene - First scene that loads essential assets
 *
 * This scene should:
 * - Load any assets needed for the loading screen (logo, loading bar graphics)
 * - Set up any global game settings
 * - Transition to PreloadScene when ready
 */
export class BootScene extends Phaser.Scene {
    constructor() {
        super({ key: 'BootScene' });
    }

    preload() {
        // Load assets needed for the loading screen
        // Example:
        // this.load.image('logo', 'assets/images/logo.png');
        // this.load.image('loading-bar', 'assets/images/loading-bar.png');
    }

    create() {
        // Set up any global game settings here
        // Example: this.registry.set('highScore', 0);

        // Transition to the preload scene
        this.scene.start('PreloadScene');
    }
}
