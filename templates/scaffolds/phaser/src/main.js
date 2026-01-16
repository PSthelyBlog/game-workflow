import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene.js';
import { PreloadScene } from './scenes/PreloadScene.js';
import { MenuScene } from './scenes/MenuScene.js';
import { GameScene } from './scenes/GameScene.js';

/**
 * Phaser Game Configuration
 *
 * Customize these settings based on your game requirements:
 * - width/height: Game resolution
 * - physics: Enable/disable physics systems
 * - scale: Responsive scaling behavior
 */
const config = {
    type: Phaser.AUTO,
    parent: 'game-container',
    width: 800,
    height: 600,
    backgroundColor: '#2d2d44',
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    },
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
        min: {
            width: 400,
            height: 300
        },
        max: {
            width: 1600,
            height: 1200
        }
    },
    scene: [BootScene, PreloadScene, MenuScene, GameScene]
};

// Create the game instance
const game = new Phaser.Game(config);

// Handle visibility change (pause when tab is hidden)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        game.scene.pause();
    } else {
        game.scene.resume();
    }
});

export default game;
