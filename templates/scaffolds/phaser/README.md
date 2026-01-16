# Phaser Game Scaffold

A starter template for Phaser 3 games with Vite for modern development.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
├── index.html          # Entry point
├── package.json        # Dependencies and scripts
├── vite.config.js      # Build configuration
├── src/
│   ├── main.js         # Game configuration and initialization
│   ├── scenes/         # Game scenes
│   │   ├── BootScene.js     # Initial boot and setup
│   │   ├── PreloadScene.js  # Asset loading with progress bar
│   │   ├── MenuScene.js     # Main menu
│   │   └── GameScene.js     # Main gameplay
│   ├── objects/        # Reusable game objects (Player, Enemy, etc.)
│   └── utils/          # Helper functions
└── assets/
    ├── images/         # Sprites, backgrounds, UI
    ├── audio/          # Music and sound effects
    └── fonts/          # Custom fonts
```

## Customization

1. **Game Settings**: Edit `src/main.js` to change resolution, physics, and scaling
2. **Asset Loading**: Add your assets in `src/scenes/PreloadScene.js`
3. **Game Logic**: Implement your gameplay in `src/scenes/GameScene.js`
4. **Add Scenes**: Create new scenes in `src/scenes/` and register them in `main.js`

## Features

- Phaser 3.80+ with Arcade Physics
- Vite for fast HMR development
- Responsive scaling (FIT mode)
- Scene management structure
- Loading progress bar
- Keyboard and pointer input handling
- Game over / restart flow
- Tab visibility handling (auto-pause)

## Deployment

Run `npm run build` to create a production build in the `dist/` folder. Upload the contents to any static hosting service (itch.io, GitHub Pages, Netlify, etc.).
