# Godot Game Development Skill

This skill provides Claude Code with knowledge for implementing Godot games.

## Overview

Godot is a free and open source game engine. This skill covers:
- GDScript patterns
- Scene structure
- Export configuration
- Best practices

## Project Structure

```
game/
├── project.godot       # Project configuration
├── icon.svg            # Game icon
├── export_presets.cfg  # Export settings
├── scenes/
│   ├── Main.tscn       # Main scene
│   ├── Player.tscn     # Player scene
│   └── UI.tscn         # UI scene
├── scripts/
│   ├── Player.gd       # Player script
│   ├── GameManager.gd  # Game state
│   └── autoload/       # Singletons
├── assets/
│   ├── sprites/
│   ├── audio/
│   └── fonts/
└── addons/             # Plugins
```

## GDScript Patterns

### Node Script
```gdscript
extends CharacterBody2D

@export var speed: float = 200.0
@onready var sprite = $Sprite2D

func _ready():
    pass

func _physics_process(delta):
    var velocity = Vector2.ZERO
    velocity.x = Input.get_axis("ui_left", "ui_right")
    velocity.y = Input.get_axis("ui_up", "ui_down")
    velocity = velocity.normalized() * speed
    move_and_slide()
```

### Signals
```gdscript
signal health_changed(new_health)

func take_damage(amount):
    health -= amount
    health_changed.emit(health)
```

### Scene Instantiation
```gdscript
var enemy_scene = preload("res://scenes/Enemy.tscn")

func spawn_enemy():
    var enemy = enemy_scene.instantiate()
    add_child(enemy)
    enemy.global_position = spawn_point
```

## Export Configuration

### Web Export
```ini
[preset.0]
name="Web"
platform="Web"
export_path="export/web/index.html"
```

### Export Features
- Enable threads for better performance
- Set appropriate memory limits
- Include required features only

## Best Practices

1. Use scenes for composition
2. Leverage signals for loose coupling
3. Use autoload for global state
4. Implement object pooling for performance
5. Use typed variables for better performance
