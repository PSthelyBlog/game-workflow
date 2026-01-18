# Godot Game Scaffold

A ready-to-use Godot 4.x project scaffold for game development.

## Structure

```
godot/
├── project.godot           # Project configuration
├── export_presets.cfg      # Web export preset
├── icon.svg                # Game icon
├── scenes/
│   ├── main.tscn           # Main game scene
│   ├── ui/
│   │   ├── main_menu.tscn  # Main menu
│   │   ├── hud.tscn        # Heads-up display
│   │   ├── pause_menu.tscn # Pause menu
│   │   └── game_over.tscn  # Game over screen
│   └── entities/
│       └── player.tscn     # Player character
├── scripts/
│   ├── main.gd             # Main scene controller
│   ├── autoload/
│   │   ├── game_manager.gd # Game state singleton
│   │   ├── audio_manager.gd# Audio singleton
│   │   └── event_bus.gd    # Global events singleton
│   ├── ui/
│   │   ├── main_menu.gd
│   │   ├── hud.gd
│   │   ├── pause_menu.gd
│   │   └── game_over.gd
│   └── entities/
│       └── player.gd       # Player controller
└── assets/
    ├── sprites/
    ├── audio/
    │   ├── music/
    │   └── sfx/
    └── fonts/
```

## Features

- **Autoload Singletons**: GameManager, AudioManager, EventBus
- **Complete UI System**: Main menu, HUD, pause menu, game over screen
- **Player Controller**: Supports platformer and top-down movement
- **Input Actions**: Pre-configured for movement, jump, attack, pause, interact
- **Web Export**: Pre-configured export preset for HTML5
- **Event-Driven**: Decoupled systems using signals and EventBus

## Template Variables

Replace these placeholders when creating a new game:

- `{{GAME_NAME}}` - The name of your game
- `{{GAME_DESCRIPTION}}` - A short description of your game

## Getting Started

1. Copy this scaffold to your game directory
2. Replace template variables in `project.godot` and scene files
3. Add your sprites to `assets/sprites/`
4. Add your audio to `assets/audio/music/` and `assets/audio/sfx/`
5. Customize the player controller in `scripts/entities/player.gd`
6. Add your game-specific scenes to `scenes/`

## Input Actions

| Action     | Keys              | Description        |
|------------|-------------------|--------------------|
| move_left  | A, Left Arrow     | Move left          |
| move_right | D, Right Arrow    | Move right         |
| move_up    | W, Up Arrow       | Move up            |
| move_down  | S, Down Arrow     | Move down          |
| jump       | Space             | Jump               |
| attack     | X, Left Click     | Attack             |
| pause      | Escape            | Pause/resume game  |
| interact   | E                 | Interact with NPCs |

## Exporting for Web

1. Open Project > Export
2. Select the "Web" preset
3. Click "Export Project"
4. Upload the exported files to itch.io

## Customization Tips

### Switching to Top-Down Movement

In `scripts/entities/player.gd`, uncomment the top-down movement lines:

```gdscript
# var v_direction := Input.get_axis("move_up", "move_down")
# velocity.y = v_direction * speed
```

And set `gravity_scale = 0.0` in the player inspector.

### Adding New Entities

1. Create a new scene in `scenes/entities/`
2. Create a corresponding script in `scripts/entities/`
3. Use the EventBus for communication with other systems

### Adding New UI Screens

1. Create a new scene in `scenes/ui/`
2. Create a corresponding script in `scripts/ui/`
3. Connect buttons to methods in the script
