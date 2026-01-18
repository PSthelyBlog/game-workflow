# Godot Game Development Skill

This skill provides Claude Code with comprehensive knowledge for implementing games using the Godot Engine (version 4.x with GDScript). Use this when building games with Godot.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Scene System](#scene-system)
4. [Node Lifecycle](#node-lifecycle)
5. [GDScript Fundamentals](#gdscript-fundamentals)
6. [Signals and Communication](#signals-and-communication)
7. [Input Handling](#input-handling)
8. [Physics Systems](#physics-systems)
9. [Animation](#animation)
10. [Audio System](#audio-system)
11. [UI and Control Nodes](#ui-and-control-nodes)
12. [Tilemaps](#tilemaps)
13. [State Management](#state-management)
14. [Save/Load System](#saveload-system)
15. [Common Game Patterns by Genre](#common-game-patterns-by-genre)
16. [Export for Web (HTML5)](#export-for-web-html5)
17. [Performance Optimization](#performance-optimization)
18. [Debugging](#debugging)

---

## Overview

Godot is a free and open source game engine that uses a scene-based architecture with nodes. This skill covers:

- Scene and node composition
- GDScript programming patterns
- Signal-based communication
- 2D and 3D physics
- Animation systems
- Input handling across platforms
- UI development
- Export for web deployment

### Why Godot?

- **Free and open source** - MIT license, no royalties
- **Lightweight** - Small download, fast iteration
- **Node-based architecture** - Intuitive scene composition
- **GDScript** - Python-like, easy to learn
- **Built-in tools** - Animation, tilemap, shader editors
- **Cross-platform** - Deploy to web, desktop, mobile

---

## Project Structure

Standard Godot 4.x project layout:

```
game/
├── project.godot           # Project configuration
├── icon.svg                # Game icon
├── export_presets.cfg      # Export settings
│
├── scenes/
│   ├── main.tscn           # Main scene (entry point)
│   ├── levels/
│   │   ├── level_1.tscn
│   │   └── level_2.tscn
│   ├── ui/
│   │   ├── main_menu.tscn
│   │   ├── hud.tscn
│   │   ├── pause_menu.tscn
│   │   └── game_over.tscn
│   └── entities/
│       ├── player.tscn
│       ├── enemy.tscn
│       └── collectible.tscn
│
├── scripts/
│   ├── player.gd           # Player controller
│   ├── enemy.gd            # Enemy AI
│   ├── game_manager.gd     # Game state (autoload)
│   ├── audio_manager.gd    # Audio control (autoload)
│   └── save_manager.gd     # Save/load (autoload)
│
├── assets/
│   ├── sprites/            # 2D graphics
│   │   ├── player/
│   │   ├── enemies/
│   │   └── tiles/
│   ├── audio/
│   │   ├── music/
│   │   └── sfx/
│   ├── fonts/
│   └── shaders/
│
└── resources/              # Godot resources (.tres, .res)
    ├── themes/
    └── data/
```

### Project Configuration (project.godot)

```ini
[application]
config/name="My Game"
config/description="A great game"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.2", "GL Compatibility")
config/icon="res://icon.svg"

[autoload]
GameManager="*res://scripts/game_manager.gd"
AudioManager="*res://scripts/audio_manager.gd"
SaveManager="*res://scripts/save_manager.gd"

[display]
window/size/viewport_width=1280
window/size/viewport_height=720
window/stretch/mode="canvas_items"
window/stretch/aspect="expand"

[input]
move_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":65,"key_label":0,"unicode":0,"echo":false,"script":null)]
}
move_right={...}
move_up={...}
move_down={...}
jump={...}
attack={...}

[rendering]
renderer/rendering_method="gl_compatibility"
textures/canvas_textures/default_texture_filter=0
```

---

## Scene System

### Scene Basics

Scenes are the fundamental building blocks in Godot. Every scene is a tree of nodes.

```
PlayerScene
├── CharacterBody2D (root)
│   ├── Sprite2D
│   ├── CollisionShape2D
│   ├── AnimationPlayer
│   └── Camera2D
```

### Creating Scenes

```gdscript
# Load and instantiate a scene
var enemy_scene = preload("res://scenes/entities/enemy.tscn")

func spawn_enemy(position: Vector2) -> void:
    var enemy = enemy_scene.instantiate()
    enemy.position = position
    add_child(enemy)

# Or load dynamically
func spawn_dynamic() -> void:
    var scene = load("res://scenes/entities/enemy.tscn")
    var instance = scene.instantiate()
    add_child(instance)
```

### Changing Scenes

```gdscript
# Change to a new scene (replaces current)
get_tree().change_scene_to_file("res://scenes/levels/level_2.tscn")

# Or with a packed scene
var next_level = preload("res://scenes/levels/level_2.tscn")
get_tree().change_scene_to_packed(next_level)

# Reload current scene
get_tree().reload_current_scene()
```

### Scene Inheritance

Create a base scene and extend it:

```gdscript
# base_enemy.gd (attached to BaseEnemy scene)
class_name BaseEnemy
extends CharacterBody2D

@export var speed: float = 100.0
@export var health: int = 100

func take_damage(amount: int) -> void:
    health -= amount
    if health <= 0:
        die()

func die() -> void:
    queue_free()
```

Then inherit in the editor or instantiate:

```gdscript
# flying_enemy.gd (extends BaseEnemy)
extends BaseEnemy

@export var fly_height: float = 50.0

func _physics_process(delta: float) -> void:
    # Flying enemy specific behavior
    position.y = sin(Time.get_ticks_msec() * 0.01) * fly_height
```

---

## Node Lifecycle

### Virtual Methods

```gdscript
extends Node2D

# Called when node enters the scene tree (once)
func _ready() -> void:
    print("Node is ready!")

# Called every frame
func _process(delta: float) -> void:
    # delta = time since last frame in seconds
    pass

# Called at fixed intervals (physics, default 60 Hz)
func _physics_process(delta: float) -> void:
    # Use for physics calculations
    pass

# Called when node receives input
func _input(event: InputEvent) -> void:
    if event.is_action_pressed("jump"):
        jump()

# Called for unhandled input (after _input)
func _unhandled_input(event: InputEvent) -> void:
    pass

# Called when node is about to be removed
func _exit_tree() -> void:
    print("Node is being removed")
```

### Node Tree Operations

```gdscript
# Get nodes
var parent = get_parent()
var child = get_node("ChildName")  # or $ChildName
var child_path = get_node("Path/To/Child")

# Typed node references (recommended)
@onready var sprite: Sprite2D = $Sprite2D
@onready var anim: AnimationPlayer = $AnimationPlayer

# Check if node exists
if has_node("OptionalChild"):
    var optional = $OptionalChild

# Add/remove children
add_child(new_node)
remove_child(node)
node.queue_free()  # Safe delete (deferred)

# Reparent
node.reparent(new_parent)

# Get all children
for child in get_children():
    print(child.name)

# Find nodes by group
var enemies = get_tree().get_nodes_in_group("enemies")
```

---

## GDScript Fundamentals

### Variables and Types

```gdscript
# Basic types
var health: int = 100
var speed: float = 200.0
var player_name: String = "Hero"
var is_alive: bool = true

# Vectors (commonly used)
var position: Vector2 = Vector2(100, 200)
var velocity: Vector2 = Vector2.ZERO
var direction: Vector2 = Vector2.RIGHT

# 3D vectors
var position_3d: Vector3 = Vector3(1, 2, 3)

# Arrays
var items: Array[String] = ["sword", "shield"]
var numbers: Array[int] = [1, 2, 3]

# Dictionaries
var player_data: Dictionary = {
    "name": "Hero",
    "level": 1,
    "inventory": []
}

# Enums
enum State { IDLE, WALKING, JUMPING, ATTACKING }
var current_state: State = State.IDLE

# Constants
const MAX_SPEED: float = 500.0
const GRAVITY: float = 980.0
```

### Export Variables (Inspector)

```gdscript
# Basic exports
@export var health: int = 100
@export var speed: float = 200.0
@export var player_name: String = "Player"

# Range slider
@export_range(0, 100) var percentage: int = 50
@export_range(0.0, 1.0, 0.01) var alpha: float = 1.0

# File/folder paths
@export_file("*.tscn") var next_level: String
@export_dir var assets_folder: String

# Enums in inspector
@export var state: State = State.IDLE

# Node references (set in inspector)
@export var target: Node2D

# Resource exports
@export var character_data: Resource

# Groups in inspector
@export_group("Movement")
@export var walk_speed: float = 100.0
@export var run_speed: float = 200.0

@export_group("Combat")
@export var damage: int = 10
@export var attack_range: float = 50.0
```

### Functions

```gdscript
# Basic function
func take_damage(amount: int) -> void:
    health -= amount

# Function with return value
func calculate_damage(base: int, multiplier: float) -> int:
    return int(base * multiplier)

# Optional parameters
func move(direction: Vector2, speed: float = 100.0) -> void:
    position += direction * speed

# Static function
static func clamp_health(value: int) -> int:
    return clampi(value, 0, 100)

# Lambda/anonymous function
var double = func(x: int) -> int: return x * 2
print(double.call(5))  # 10
```

### Classes

```gdscript
# player.gd
class_name Player
extends CharacterBody2D

signal health_changed(new_health: int)
signal died

@export var max_health: int = 100
var health: int

func _ready() -> void:
    health = max_health

func take_damage(amount: int) -> void:
    health = maxi(health - amount, 0)
    health_changed.emit(health)

    if health <= 0:
        died.emit()

func heal(amount: int) -> void:
    health = mini(health + amount, max_health)
    health_changed.emit(health)
```

### Inner Classes

```gdscript
# Useful for small data structures
class_name Inventory
extends Node

class Item:
    var name: String
    var quantity: int

    func _init(item_name: String, qty: int = 1) -> void:
        name = item_name
        quantity = qty

var items: Array[Item] = []

func add_item(item_name: String, quantity: int = 1) -> void:
    for item in items:
        if item.name == item_name:
            item.quantity += quantity
            return

    items.append(Item.new(item_name, quantity))
```

---

## Signals and Communication

Signals are Godot's implementation of the observer pattern - essential for decoupled communication.

### Defining Signals

```gdscript
# Simple signal
signal game_started

# Signal with parameters
signal health_changed(new_health: int)
signal player_died
signal score_updated(old_score: int, new_score: int)
signal item_collected(item_name: String, position: Vector2)
```

### Emitting Signals

```gdscript
func take_damage(amount: int) -> void:
    health -= amount
    health_changed.emit(health)

    if health <= 0:
        player_died.emit()

func collect_item(item: Node2D) -> void:
    item_collected.emit(item.name, item.global_position)
    item.queue_free()
```

### Connecting Signals

```gdscript
# Connect in code
func _ready() -> void:
    # Method 1: Connect to a method
    var player = $Player
    player.health_changed.connect(_on_player_health_changed)
    player.player_died.connect(_on_player_died)

    # Method 2: Connect with lambda
    player.health_changed.connect(func(h): print("Health: ", h))

    # One-shot connection (disconnects after first emit)
    player.player_died.connect(_on_player_died, CONNECT_ONE_SHOT)

func _on_player_health_changed(new_health: int) -> void:
    $HUD.update_health_bar(new_health)

func _on_player_died() -> void:
    get_tree().change_scene_to_file("res://scenes/ui/game_over.tscn")
```

### Disconnecting Signals

```gdscript
# Disconnect specific connection
player.health_changed.disconnect(_on_player_health_changed)

# Check if connected
if player.health_changed.is_connected(_on_player_health_changed):
    player.health_changed.disconnect(_on_player_health_changed)
```

### Built-in Signals

Many nodes have built-in signals:

```gdscript
func _ready() -> void:
    # Button signals
    $Button.pressed.connect(_on_button_pressed)

    # Timer signals
    $Timer.timeout.connect(_on_timer_timeout)

    # Area2D signals
    $Area2D.body_entered.connect(_on_body_entered)
    $Area2D.area_entered.connect(_on_area_entered)

    # AnimationPlayer signals
    $AnimationPlayer.animation_finished.connect(_on_animation_finished)

    # Visibility signals
    visibility_changed.connect(_on_visibility_changed)
```

### Signal Bus Pattern (Global Events)

```gdscript
# event_bus.gd - Autoload singleton
extends Node

signal game_started
signal game_paused
signal game_resumed
signal level_completed(level_number: int)
signal player_died
signal score_changed(new_score: int)
signal achievement_unlocked(achievement_id: String)
```

Usage:

```gdscript
# In player.gd
func die() -> void:
    EventBus.player_died.emit()

# In hud.gd
func _ready() -> void:
    EventBus.score_changed.connect(_on_score_changed)
    EventBus.player_died.connect(_on_player_died)
```

---

## Input Handling

### Input Map

Define inputs in Project Settings > Input Map or `project.godot`:

```ini
[input]
move_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"physical_keycode":65)]  # A key
}
move_right={
"deadzone": 0.5,
"events": [Object(InputEventKey,"physical_keycode":68)]  # D key
}
jump={
"deadzone": 0.5,
"events": [Object(InputEventKey,"physical_keycode":32)]  # Space
}
```

### Checking Input

```gdscript
func _physics_process(delta: float) -> void:
    var direction := Vector2.ZERO

    # Check if action is held
    if Input.is_action_pressed("move_left"):
        direction.x -= 1
    if Input.is_action_pressed("move_right"):
        direction.x += 1
    if Input.is_action_pressed("move_up"):
        direction.y -= 1
    if Input.is_action_pressed("move_down"):
        direction.y += 1

    # Get axis value (-1 to 1, handles analog input)
    direction.x = Input.get_axis("move_left", "move_right")
    direction.y = Input.get_axis("move_up", "move_down")

    # Get as vector (2D movement)
    direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")

    # Normalize for consistent diagonal speed
    direction = direction.normalized()

    velocity = direction * speed
    move_and_slide()

func _input(event: InputEvent) -> void:
    # Check for just pressed (once per press)
    if event.is_action_pressed("jump"):
        jump()

    # Check for just released
    if event.is_action_released("attack"):
        release_attack()
```

### Mouse Input

```gdscript
func _input(event: InputEvent) -> void:
    # Mouse button
    if event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
            shoot()
        if event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
            aim()

    # Mouse motion
    if event is InputEventMouseMotion:
        rotate_towards_mouse(event.position)

func _physics_process(delta: float) -> void:
    # Get mouse position
    var mouse_pos = get_global_mouse_position()

    # Look at mouse
    look_at(mouse_pos)

    # Move towards mouse
    var direction = (mouse_pos - global_position).normalized()
    velocity = direction * speed
```

### Touch Input

```gdscript
func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        if event.pressed:
            # Touch started
            handle_touch_start(event.position, event.index)
        else:
            # Touch ended
            handle_touch_end(event.index)

    if event is InputEventScreenDrag:
        handle_drag(event.position, event.relative, event.index)

# Multi-touch tracking
var touch_points: Dictionary = {}

func handle_touch_start(pos: Vector2, index: int) -> void:
    touch_points[index] = pos

func handle_touch_end(index: int) -> void:
    touch_points.erase(index)

func handle_drag(pos: Vector2, relative: Vector2, index: int) -> void:
    touch_points[index] = pos

    # Pinch to zoom (2 fingers)
    if touch_points.size() == 2:
        var points = touch_points.values()
        var distance = points[0].distance_to(points[1])
        # Use distance for zoom
```

### Gamepad Input

```gdscript
func _physics_process(delta: float) -> void:
    # Left stick
    var left_stick = Vector2(
        Input.get_joy_axis(0, JOY_AXIS_LEFT_X),
        Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
    )

    # Apply deadzone
    if left_stick.length() < 0.2:
        left_stick = Vector2.ZERO

    # Right stick
    var right_stick = Vector2(
        Input.get_joy_axis(0, JOY_AXIS_RIGHT_X),
        Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y)
    )

    # Triggers (0 to 1)
    var left_trigger = Input.get_joy_axis(0, JOY_AXIS_TRIGGER_LEFT)
    var right_trigger = Input.get_joy_axis(0, JOY_AXIS_TRIGGER_RIGHT)

func _input(event: InputEvent) -> void:
    if event is InputEventJoypadButton:
        if event.button_index == JOY_BUTTON_A and event.pressed:
            jump()
```

---

## Physics Systems

### CharacterBody2D (Platformer)

```gdscript
extends CharacterBody2D

const SPEED = 300.0
const JUMP_VELOCITY = -400.0
const GRAVITY = 980.0

func _physics_process(delta: float) -> void:
    # Apply gravity
    if not is_on_floor():
        velocity.y += GRAVITY * delta

    # Handle jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    # Handle horizontal movement
    var direction := Input.get_axis("move_left", "move_right")
    if direction:
        velocity.x = direction * SPEED
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)

    move_and_slide()
```

### CharacterBody2D (Top-Down)

```gdscript
extends CharacterBody2D

const SPEED = 200.0

func _physics_process(delta: float) -> void:
    var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")

    if direction != Vector2.ZERO:
        velocity = direction.normalized() * SPEED
    else:
        velocity = velocity.move_toward(Vector2.ZERO, SPEED * delta * 10)

    move_and_slide()
```

### RigidBody2D

```gdscript
extends RigidBody2D

@export var jump_force: float = 500.0

func _ready() -> void:
    # Configure physics
    gravity_scale = 1.0
    linear_damp = 0.1
    angular_damp = 0.1

func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
    # Custom physics integration
    if Input.is_action_just_pressed("jump"):
        state.apply_central_impulse(Vector2.UP * jump_force)

func _physics_process(delta: float) -> void:
    # Apply force for movement
    var direction := Input.get_axis("move_left", "move_right")
    apply_central_force(Vector2(direction * 1000, 0))
```

### Area2D (Triggers/Overlaps)

```gdscript
extends Area2D

signal player_entered
signal player_exited

func _ready() -> void:
    body_entered.connect(_on_body_entered)
    body_exited.connect(_on_body_exited)

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        player_entered.emit()

func _on_body_exited(body: Node2D) -> void:
    if body.is_in_group("player"):
        player_exited.emit()

# Check for overlapping bodies
func get_overlapping_enemies() -> Array[Node2D]:
    var enemies: Array[Node2D] = []
    for body in get_overlapping_bodies():
        if body.is_in_group("enemies"):
            enemies.append(body)
    return enemies
```

### Raycasting

```gdscript
extends Node2D

@onready var ray: RayCast2D = $RayCast2D

func _physics_process(delta: float) -> void:
    if ray.is_colliding():
        var collider = ray.get_collider()
        var point = ray.get_collision_point()
        var normal = ray.get_collision_normal()

        if collider.is_in_group("enemies"):
            collider.take_damage(10)

# Direct space state query
func cast_ray_to_point(target: Vector2) -> Dictionary:
    var space = get_world_2d().direct_space_state
    var query = PhysicsRayQueryParameters2D.create(global_position, target)
    query.exclude = [self]  # Exclude self
    query.collision_mask = 1  # Layer to check

    return space.intersect_ray(query)

func check_line_of_sight(target: Node2D) -> bool:
    var result = cast_ray_to_point(target.global_position)
    return result.is_empty() or result.collider == target
```

### 3D Physics

```gdscript
extends CharacterBody3D

const SPEED = 5.0
const JUMP_VELOCITY = 4.5
const GRAVITY = 9.8

func _physics_process(delta: float) -> void:
    # Gravity
    if not is_on_floor():
        velocity.y -= GRAVITY * delta

    # Jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    # Movement
    var input_dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()

    if direction:
        velocity.x = direction.x * SPEED
        velocity.z = direction.z * SPEED
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        velocity.z = move_toward(velocity.z, 0, SPEED)

    move_and_slide()
```

---

## Animation

### AnimationPlayer

```gdscript
extends CharacterBody2D

@onready var anim: AnimationPlayer = $AnimationPlayer
@onready var sprite: Sprite2D = $Sprite2D

func _physics_process(delta: float) -> void:
    # Play animations based on state
    if is_on_floor():
        if velocity.x != 0:
            anim.play("walk")
        else:
            anim.play("idle")
    else:
        if velocity.y < 0:
            anim.play("jump")
        else:
            anim.play("fall")

    # Flip sprite based on direction
    if velocity.x != 0:
        sprite.flip_h = velocity.x < 0

# Animation callbacks
func _on_animation_finished(anim_name: StringName) -> void:
    if anim_name == "attack":
        anim.play("idle")

func _ready() -> void:
    anim.animation_finished.connect(_on_animation_finished)
```

### AnimationTree (State Machine)

```gdscript
extends CharacterBody2D

@onready var anim_tree: AnimationTree = $AnimationTree
@onready var state_machine: AnimationNodeStateMachinePlayback = anim_tree["parameters/playback"]

func _physics_process(delta: float) -> void:
    # Update blend parameters
    anim_tree["parameters/move/blend_position"] = velocity.normalized()

    # Transition between states
    if is_on_floor():
        if velocity.length() > 10:
            state_machine.travel("move")
        else:
            state_machine.travel("idle")
    else:
        state_machine.travel("jump")

func attack() -> void:
    state_machine.travel("attack")

func _ready() -> void:
    anim_tree.active = true
```

### Sprite Animation (AnimatedSprite2D)

```gdscript
extends CharacterBody2D

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D

func _physics_process(delta: float) -> void:
    if velocity.x != 0:
        sprite.play("walk")
        sprite.flip_h = velocity.x < 0
    else:
        sprite.play("idle")

func _ready() -> void:
    sprite.animation_finished.connect(_on_animation_finished)

func _on_animation_finished() -> void:
    if sprite.animation == "attack":
        sprite.play("idle")
```

### Tween Animations

```gdscript
# Simple property animation
func flash_red() -> void:
    var tween = create_tween()
    tween.tween_property($Sprite2D, "modulate", Color.RED, 0.1)
    tween.tween_property($Sprite2D, "modulate", Color.WHITE, 0.1)

# Chained animations
func animate_ui() -> void:
    var tween = create_tween()
    tween.tween_property($Panel, "position", Vector2(100, 100), 0.5)
    tween.tween_property($Panel, "modulate:a", 1.0, 0.3)
    tween.tween_callback(func(): print("Animation done!"))

# Parallel animations
func animate_parallel() -> void:
    var tween = create_tween()
    tween.set_parallel(true)
    tween.tween_property($Sprite2D, "position", Vector2(200, 200), 1.0)
    tween.tween_property($Sprite2D, "rotation", PI, 1.0)
    tween.tween_property($Sprite2D, "scale", Vector2(2, 2), 1.0)

# Easing
func animate_with_ease() -> void:
    var tween = create_tween()
    tween.tween_property($Sprite2D, "position:y", 100.0, 0.5).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BOUNCE)

# Looping
func animate_loop() -> void:
    var tween = create_tween().set_loops()  # Infinite
    # Or set_loops(3) for specific count
    tween.tween_property($Sprite2D, "rotation", TAU, 2.0)
```

---

## Audio System

### Playing Audio

```gdscript
extends Node2D

@onready var audio_player: AudioStreamPlayer2D = $AudioStreamPlayer2D

func play_sound(sound: AudioStream) -> void:
    audio_player.stream = sound
    audio_player.play()

# Preload sounds
var jump_sound: AudioStream = preload("res://assets/audio/sfx/jump.wav")

func jump() -> void:
    audio_player.stream = jump_sound
    audio_player.play()
```

### Audio Manager (Autoload)

```gdscript
# audio_manager.gd - Autoload
extends Node

var music_player: AudioStreamPlayer
var sfx_pool: Array[AudioStreamPlayer] = []
var pool_size: int = 8
var pool_index: int = 0

var music_volume: float = 0.5 : set = set_music_volume
var sfx_volume: float = 0.7 : set = set_sfx_volume
var is_muted: bool = false

func _ready() -> void:
    # Create music player
    music_player = AudioStreamPlayer.new()
    music_player.bus = "Music"
    add_child(music_player)

    # Create SFX pool
    for i in pool_size:
        var player = AudioStreamPlayer.new()
        player.bus = "SFX"
        add_child(player)
        sfx_pool.append(player)

    # Load saved settings
    load_settings()

func play_music(stream: AudioStream, fade_duration: float = 1.0) -> void:
    if music_player.playing:
        # Crossfade
        var tween = create_tween()
        tween.tween_property(music_player, "volume_db", -80, fade_duration)
        await tween.finished

    music_player.stream = stream
    music_player.volume_db = -80
    music_player.play()

    var tween = create_tween()
    tween.tween_property(music_player, "volume_db", linear_to_db(music_volume), fade_duration)

func stop_music(fade_duration: float = 1.0) -> void:
    var tween = create_tween()
    tween.tween_property(music_player, "volume_db", -80, fade_duration)
    await tween.finished
    music_player.stop()

func play_sfx(stream: AudioStream, pitch_variance: float = 0.0) -> void:
    if is_muted:
        return

    var player = sfx_pool[pool_index]
    pool_index = (pool_index + 1) % pool_size

    player.stream = stream
    player.pitch_scale = 1.0 + randf_range(-pitch_variance, pitch_variance)
    player.play()

func play_sfx_at_position(stream: AudioStream, position: Vector2) -> void:
    # Use AudioStreamPlayer2D for positional audio
    var player = AudioStreamPlayer2D.new()
    player.stream = stream
    player.bus = "SFX"
    player.position = position
    player.finished.connect(player.queue_free)
    add_child(player)
    player.play()

func set_music_volume(value: float) -> void:
    music_volume = value
    music_player.volume_db = linear_to_db(value)

func set_sfx_volume(value: float) -> void:
    sfx_volume = value
    AudioServer.set_bus_volume_db(AudioServer.get_bus_index("SFX"), linear_to_db(value))

func toggle_mute() -> void:
    is_muted = !is_muted
    AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"), is_muted)

func save_settings() -> void:
    var config = ConfigFile.new()
    config.set_value("audio", "music_volume", music_volume)
    config.set_value("audio", "sfx_volume", sfx_volume)
    config.set_value("audio", "is_muted", is_muted)
    config.save("user://audio_settings.cfg")

func load_settings() -> void:
    var config = ConfigFile.new()
    if config.load("user://audio_settings.cfg") == OK:
        music_volume = config.get_value("audio", "music_volume", 0.5)
        sfx_volume = config.get_value("audio", "sfx_volume", 0.7)
        is_muted = config.get_value("audio", "is_muted", false)
```

### Audio Buses

Configure in Project Settings > Audio > Buses or via code:

```gdscript
func _ready() -> void:
    # Get bus indices
    var master_bus = AudioServer.get_bus_index("Master")
    var music_bus = AudioServer.get_bus_index("Music")
    var sfx_bus = AudioServer.get_bus_index("SFX")

    # Set volume (-80 to 0 dB typically)
    AudioServer.set_bus_volume_db(music_bus, -10)

    # Mute bus
    AudioServer.set_bus_mute(music_bus, true)

    # Add effect
    # AudioServer.add_bus_effect(bus_idx, effect)
```

---

## UI and Control Nodes

### Common UI Nodes

```gdscript
# Button
func _ready() -> void:
    $Button.pressed.connect(_on_button_pressed)
    $Button.mouse_entered.connect(_on_button_hover)

func _on_button_pressed() -> void:
    print("Button clicked!")

# Label
$Label.text = "Score: %d" % score

# TextureProgressBar (health bar)
$HealthBar.max_value = max_health
$HealthBar.value = current_health

# HSlider
$VolumeSlider.value_changed.connect(_on_volume_changed)

func _on_volume_changed(value: float) -> void:
    AudioManager.sfx_volume = value

# LineEdit
$NameInput.text_submitted.connect(_on_name_submitted)

func _on_name_submitted(text: String) -> void:
    player_name = text

# TextEdit
var text_content = $TextEdit.text
```

### HUD Example

```gdscript
# hud.gd
extends CanvasLayer

@onready var health_bar: TextureProgressBar = $HealthBar
@onready var score_label: Label = $ScoreLabel
@onready var ammo_label: Label = $AmmoLabel

func _ready() -> void:
    GameManager.health_changed.connect(update_health)
    GameManager.score_changed.connect(update_score)

func update_health(new_health: int) -> void:
    var tween = create_tween()
    tween.tween_property(health_bar, "value", new_health, 0.2)

    # Flash red on damage
    if new_health < health_bar.value:
        health_bar.modulate = Color.RED
        tween.tween_property(health_bar, "modulate", Color.WHITE, 0.2)

func update_score(new_score: int) -> void:
    score_label.text = "Score: %d" % new_score

    # Pop animation
    var tween = create_tween()
    tween.tween_property(score_label, "scale", Vector2(1.2, 1.2), 0.1)
    tween.tween_property(score_label, "scale", Vector2.ONE, 0.1)

func update_ammo(current: int, max_ammo: int) -> void:
    ammo_label.text = "%d / %d" % [current, max_ammo]
```

### Menu System

```gdscript
# main_menu.gd
extends Control

@onready var play_button: Button = $VBoxContainer/PlayButton
@onready var options_button: Button = $VBoxContainer/OptionsButton
@onready var quit_button: Button = $VBoxContainer/QuitButton
@onready var options_panel: Control = $OptionsPanel

func _ready() -> void:
    play_button.pressed.connect(_on_play_pressed)
    options_button.pressed.connect(_on_options_pressed)
    quit_button.pressed.connect(_on_quit_pressed)

    # Grab focus for gamepad support
    play_button.grab_focus()

func _on_play_pressed() -> void:
    get_tree().change_scene_to_file("res://scenes/levels/level_1.tscn")

func _on_options_pressed() -> void:
    options_panel.visible = true
    # Animate
    var tween = create_tween()
    options_panel.modulate.a = 0
    tween.tween_property(options_panel, "modulate:a", 1.0, 0.3)

func _on_quit_pressed() -> void:
    get_tree().quit()

# Handle back/escape
func _input(event: InputEvent) -> void:
    if event.is_action_pressed("ui_cancel"):
        if options_panel.visible:
            options_panel.visible = false
            play_button.grab_focus()
```

### Pause Menu

```gdscript
# pause_menu.gd
extends CanvasLayer

@onready var panel: Control = $Panel

var is_paused: bool = false

func _ready() -> void:
    panel.visible = false
    process_mode = Node.PROCESS_MODE_ALWAYS

func _input(event: InputEvent) -> void:
    if event.is_action_pressed("pause"):
        toggle_pause()

func toggle_pause() -> void:
    is_paused = !is_paused
    panel.visible = is_paused
    get_tree().paused = is_paused

    if is_paused:
        $Panel/ResumeButton.grab_focus()

func _on_resume_pressed() -> void:
    toggle_pause()

func _on_main_menu_pressed() -> void:
    get_tree().paused = false
    get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")

func _on_quit_pressed() -> void:
    get_tree().quit()
```

---

## Tilemaps

### TileMapLayer (Godot 4.3+)

```gdscript
extends Node2D

@onready var tilemap: TileMapLayer = $TileMapLayer

func _ready() -> void:
    # Get tile at position
    var cell_pos = tilemap.local_to_map(player.position)
    var tile_data = tilemap.get_cell_tile_data(cell_pos)

    if tile_data:
        var is_hazard = tile_data.get_custom_data("hazard")
        if is_hazard:
            player.take_damage(10)

# Set tile
func place_tile(world_pos: Vector2, tile_id: int) -> void:
    var cell_pos = tilemap.local_to_map(world_pos)
    tilemap.set_cell(cell_pos, 0, Vector2i(tile_id, 0))

# Remove tile
func remove_tile(world_pos: Vector2) -> void:
    var cell_pos = tilemap.local_to_map(world_pos)
    tilemap.erase_cell(cell_pos)

# Get world position of cell
func get_cell_world_pos(cell: Vector2i) -> Vector2:
    return tilemap.map_to_local(cell)
```

### Procedural Tilemap

```gdscript
extends Node2D

@onready var tilemap: TileMapLayer = $TileMapLayer

const TILE_GROUND: int = 0
const TILE_WALL: int = 1
const TILE_GRASS: int = 2

func generate_level(width: int, height: int) -> void:
    for x in range(width):
        for y in range(height):
            var cell = Vector2i(x, y)

            # Border walls
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                tilemap.set_cell(cell, 0, Vector2i(TILE_WALL, 0))
            # Random grass
            elif randf() < 0.1:
                tilemap.set_cell(cell, 0, Vector2i(TILE_GRASS, 0))
            # Ground
            else:
                tilemap.set_cell(cell, 0, Vector2i(TILE_GROUND, 0))
```

---

## State Management

### Game Manager (Autoload)

```gdscript
# game_manager.gd - Autoload
extends Node

signal score_changed(new_score: int)
signal health_changed(new_health: int)
signal lives_changed(new_lives: int)
signal game_over
signal level_completed

var score: int = 0 : set = set_score
var high_score: int = 0
var current_level: int = 1
var lives: int = 3 : set = set_lives

var player: Node2D
var is_game_over: bool = false

func _ready() -> void:
    load_high_score()

func set_score(value: int) -> void:
    score = value
    score_changed.emit(score)

    if score > high_score:
        high_score = score
        save_high_score()

func add_score(amount: int) -> void:
    score += amount

func set_lives(value: int) -> void:
    lives = value
    lives_changed.emit(lives)

    if lives <= 0:
        trigger_game_over()

func lose_life() -> void:
    lives -= 1

func trigger_game_over() -> void:
    is_game_over = true
    game_over.emit()

func complete_level() -> void:
    current_level += 1
    level_completed.emit()

func reset_game() -> void:
    score = 0
    lives = 3
    current_level = 1
    is_game_over = false

func save_high_score() -> void:
    var config = ConfigFile.new()
    config.set_value("game", "high_score", high_score)
    config.save("user://game_data.cfg")

func load_high_score() -> void:
    var config = ConfigFile.new()
    if config.load("user://game_data.cfg") == OK:
        high_score = config.get_value("game", "high_score", 0)
```

### Finite State Machine

```gdscript
# state_machine.gd
class_name StateMachine
extends Node

signal state_changed(old_state: State, new_state: State)

var current_state: State
var states: Dictionary = {}

func _ready() -> void:
    await owner.ready

    for child in get_children():
        if child is State:
            states[child.name.to_lower()] = child
            child.state_machine = self

    if states.size() > 0:
        current_state = states.values()[0]
        current_state.enter()

func _process(delta: float) -> void:
    if current_state:
        current_state.update(delta)

func _physics_process(delta: float) -> void:
    if current_state:
        current_state.physics_update(delta)

func transition_to(state_name: String) -> void:
    if not states.has(state_name):
        push_error("State not found: " + state_name)
        return

    var new_state = states[state_name]
    if new_state == current_state:
        return

    var old_state = current_state
    current_state.exit()
    current_state = new_state
    current_state.enter()

    state_changed.emit(old_state, current_state)
```

```gdscript
# state.gd
class_name State
extends Node

var state_machine: StateMachine

func enter() -> void:
    pass

func exit() -> void:
    pass

func update(delta: float) -> void:
    pass

func physics_update(delta: float) -> void:
    pass
```

```gdscript
# player_idle_state.gd
extends State

@onready var player: CharacterBody2D = owner

func enter() -> void:
    player.anim.play("idle")

func physics_update(delta: float) -> void:
    # Transition to move state
    var direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")
    if direction != Vector2.ZERO:
        state_machine.transition_to("move")

    # Transition to jump state
    if Input.is_action_just_pressed("jump") and player.is_on_floor():
        state_machine.transition_to("jump")
```

---

## Save/Load System

### Basic Save System

```gdscript
# save_manager.gd - Autoload
extends Node

const SAVE_PATH: String = "user://save_game.json"

func save_game(data: Dictionary) -> void:
    var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file:
        var json_string = JSON.stringify(data, "\t")
        file.store_string(json_string)
        file.close()
        print("Game saved!")
    else:
        push_error("Failed to save game")

func load_game() -> Dictionary:
    if not FileAccess.file_exists(SAVE_PATH):
        return {}

    var file = FileAccess.open(SAVE_PATH, FileAccess.READ)
    if file:
        var json_string = file.get_as_text()
        file.close()

        var json = JSON.new()
        var error = json.parse(json_string)
        if error == OK:
            return json.data
        else:
            push_error("Failed to parse save file")

    return {}

func delete_save() -> void:
    if FileAccess.file_exists(SAVE_PATH):
        DirAccess.remove_absolute(SAVE_PATH)

func has_save() -> bool:
    return FileAccess.file_exists(SAVE_PATH)
```

### Using the Save System

```gdscript
# In game scene
func save_game_data() -> void:
    var save_data = {
        "version": "1.0",
        "timestamp": Time.get_unix_time_from_system(),
        "player": {
            "position": {
                "x": player.position.x,
                "y": player.position.y
            },
            "health": player.health,
            "inventory": player.inventory
        },
        "game_state": {
            "score": GameManager.score,
            "level": GameManager.current_level,
            "completed_quests": completed_quests
        }
    }

    SaveManager.save_game(save_data)

func load_game_data() -> void:
    var data = SaveManager.load_game()
    if data.is_empty():
        return

    # Restore player
    if data.has("player"):
        player.position = Vector2(
            data.player.position.x,
            data.player.position.y
        )
        player.health = data.player.health
        player.inventory = data.player.inventory

    # Restore game state
    if data.has("game_state"):
        GameManager.score = data.game_state.score
        GameManager.current_level = data.game_state.level
```

### Multiple Save Slots

```gdscript
const MAX_SLOTS: int = 3

func get_save_path(slot: int) -> String:
    return "user://save_slot_%d.json" % slot

func save_to_slot(slot: int, data: Dictionary) -> void:
    var path = get_save_path(slot)
    var file = FileAccess.open(path, FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(data))
        file.close()

func load_from_slot(slot: int) -> Dictionary:
    var path = get_save_path(slot)
    if not FileAccess.file_exists(path):
        return {}

    var file = FileAccess.open(path, FileAccess.READ)
    if file:
        var json = JSON.new()
        json.parse(file.get_as_text())
        file.close()
        return json.data

    return {}

func get_all_saves() -> Array[Dictionary]:
    var saves: Array[Dictionary] = []
    for i in MAX_SLOTS:
        var data = load_from_slot(i)
        if not data.is_empty():
            data["slot"] = i
            saves.append(data)
    return saves
```

---

## Common Game Patterns by Genre

### Platformer

```gdscript
extends CharacterBody2D

const SPEED = 200.0
const JUMP_VELOCITY = -350.0
const GRAVITY = 800.0
const COYOTE_TIME = 0.15
const JUMP_BUFFER_TIME = 0.1

var coyote_timer: float = 0.0
var jump_buffer_timer: float = 0.0

@onready var anim: AnimationPlayer = $AnimationPlayer
@onready var sprite: Sprite2D = $Sprite2D

func _physics_process(delta: float) -> void:
    # Gravity
    if not is_on_floor():
        velocity.y += GRAVITY * delta
        coyote_timer -= delta
    else:
        coyote_timer = COYOTE_TIME

    # Jump buffer
    if Input.is_action_just_pressed("jump"):
        jump_buffer_timer = JUMP_BUFFER_TIME
    else:
        jump_buffer_timer -= delta

    # Jump with coyote time and jump buffer
    if jump_buffer_timer > 0 and coyote_timer > 0:
        velocity.y = JUMP_VELOCITY
        jump_buffer_timer = 0
        coyote_timer = 0

    # Variable jump height
    if Input.is_action_just_released("jump") and velocity.y < 0:
        velocity.y *= 0.5

    # Horizontal movement
    var direction := Input.get_axis("move_left", "move_right")
    velocity.x = direction * SPEED

    # Flip sprite
    if direction != 0:
        sprite.flip_h = direction < 0

    # Animation
    if is_on_floor():
        if direction != 0:
            anim.play("walk")
        else:
            anim.play("idle")
    else:
        if velocity.y < 0:
            anim.play("jump")
        else:
            anim.play("fall")

    move_and_slide()
```

### Top-Down Shooter

```gdscript
extends CharacterBody2D

const SPEED = 200.0
const BULLET_SPEED = 600.0

var bullet_scene: PackedScene = preload("res://scenes/entities/bullet.tscn")

@onready var muzzle: Marker2D = $Muzzle

func _physics_process(delta: float) -> void:
    # Movement
    var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    velocity = direction * SPEED
    move_and_slide()

    # Look at mouse
    look_at(get_global_mouse_position())

func _input(event: InputEvent) -> void:
    if event.is_action_pressed("shoot"):
        shoot()

func shoot() -> void:
    var bullet = bullet_scene.instantiate()
    bullet.position = muzzle.global_position
    bullet.rotation = rotation
    bullet.direction = Vector2.RIGHT.rotated(rotation)
    get_parent().add_child(bullet)
```

```gdscript
# bullet.gd
extends Area2D

var speed: float = 600.0
var direction: Vector2 = Vector2.RIGHT
var damage: int = 10

func _ready() -> void:
    body_entered.connect(_on_body_entered)

    # Auto-destroy after 5 seconds
    await get_tree().create_timer(5.0).timeout
    queue_free()

func _physics_process(delta: float) -> void:
    position += direction * speed * delta

func _on_body_entered(body: Node2D) -> void:
    if body.has_method("take_damage"):
        body.take_damage(damage)
    queue_free()
```

### RPG/Adventure

```gdscript
extends CharacterBody2D

const SPEED = 150.0

var facing_direction: Vector2 = Vector2.DOWN

@onready var anim_tree: AnimationTree = $AnimationTree
@onready var interaction_area: Area2D = $InteractionArea

func _physics_process(delta: float) -> void:
    var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")

    if direction != Vector2.ZERO:
        facing_direction = direction.normalized()
        velocity = direction.normalized() * SPEED

        # Update animation blend
        anim_tree["parameters/idle/blend_position"] = facing_direction
        anim_tree["parameters/walk/blend_position"] = facing_direction
        anim_tree["parameters/playback"].travel("walk")
    else:
        velocity = Vector2.ZERO
        anim_tree["parameters/playback"].travel("idle")

    move_and_slide()

func _input(event: InputEvent) -> void:
    if event.is_action_pressed("interact"):
        interact()

func interact() -> void:
    var bodies = interaction_area.get_overlapping_bodies()
    for body in bodies:
        if body.has_method("interact"):
            body.interact(self)
            return
```

### Puzzle/Match-3

```gdscript
extends Node2D

const GRID_SIZE = Vector2i(8, 8)
const CELL_SIZE = 64
const TILE_TYPES = 5

var grid: Array[Array] = []
var selected_cell: Vector2i = Vector2i(-1, -1)

func _ready() -> void:
    create_grid()

func create_grid() -> void:
    for x in GRID_SIZE.x:
        var column: Array = []
        for y in GRID_SIZE.y:
            var tile_type = randi() % TILE_TYPES
            var tile = create_tile(tile_type, Vector2i(x, y))
            column.append(tile)
        grid.append(column)

    # Check and remove initial matches
    while check_and_remove_matches():
        await get_tree().process_frame
        drop_tiles()
        await get_tree().create_timer(0.3).timeout
        fill_empty()
        await get_tree().create_timer(0.3).timeout

func create_tile(type: int, cell: Vector2i) -> Sprite2D:
    var tile = Sprite2D.new()
    tile.texture = load("res://assets/sprites/tiles/tile_%d.png" % type)
    tile.position = cell_to_position(cell)
    tile.set_meta("type", type)
    tile.set_meta("cell", cell)
    add_child(tile)
    return tile

func cell_to_position(cell: Vector2i) -> Vector2:
    return Vector2(cell) * CELL_SIZE + Vector2.ONE * CELL_SIZE / 2

func position_to_cell(pos: Vector2) -> Vector2i:
    return Vector2i(pos / CELL_SIZE)

func _input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        var cell = position_to_cell(event.position)
        if is_valid_cell(cell):
            select_cell(cell)

func select_cell(cell: Vector2i) -> void:
    if selected_cell == Vector2i(-1, -1):
        selected_cell = cell
        highlight_tile(cell)
    else:
        if is_adjacent(selected_cell, cell):
            swap_tiles(selected_cell, cell)
        clear_selection()

func is_adjacent(a: Vector2i, b: Vector2i) -> bool:
    return abs(a.x - b.x) + abs(a.y - b.y) == 1

func swap_tiles(a: Vector2i, b: Vector2i) -> void:
    var tile_a = grid[a.x][a.y]
    var tile_b = grid[b.x][b.y]

    grid[a.x][a.y] = tile_b
    grid[b.x][b.y] = tile_a

    animate_swap(tile_a, b)
    animate_swap(tile_b, a)

    await get_tree().create_timer(0.3).timeout

    if not check_and_remove_matches():
        # Swap back if no match
        swap_tiles(a, b)
```

---

## Export for Web (HTML5)

### Export Configuration

1. **Install export templates**: Editor > Manage Export Templates > Download
2. **Create export preset**: Project > Export > Add > Web

### Export Settings

```ini
# export_presets.cfg
[preset.0]
name="Web"
platform="Web"
runnable=true
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="export/web/index.html"

[preset.0.options]
custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=true
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
html/experimental_virtual_keyboard=false
progressive_web_app/enabled=false
```

### Web-Specific Considerations

```gdscript
# Check if running in browser
func is_web() -> bool:
    return OS.get_name() == "Web"

# Handle browser fullscreen
func toggle_fullscreen() -> void:
    if DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN:
        DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
    else:
        DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)

# Disable certain features on web
func _ready() -> void:
    if is_web():
        # Disable file system access UI
        $SaveButton.visible = false
        $LoadButton.visible = false

# Handle audio autoplay
func _input(event: InputEvent) -> void:
    if event is InputEventMouseButton or event is InputEventKey:
        # Start audio after user interaction (browser policy)
        if not AudioManager.is_initialized:
            AudioManager.initialize()
```

### itch.io Upload

1. Export as Web
2. Zip the `export/web/` folder contents
3. Upload to itch.io
4. Set viewport size (match your game resolution)
5. Enable fullscreen option
6. Mark as mobile-friendly if touch controls are implemented

---

## Performance Optimization

### General Tips

```gdscript
# 1. Use object pooling for frequently spawned objects
class_name BulletPool
extends Node

var pool: Array[Node2D] = []
var bullet_scene: PackedScene = preload("res://scenes/entities/bullet.tscn")
var pool_size: int = 50

func _ready() -> void:
    for i in pool_size:
        var bullet = bullet_scene.instantiate()
        bullet.set_process(false)
        bullet.visible = false
        pool.append(bullet)
        add_child(bullet)

func get_bullet() -> Node2D:
    for bullet in pool:
        if not bullet.visible:
            bullet.visible = true
            bullet.set_process(true)
            return bullet
    return null

func return_bullet(bullet: Node2D) -> void:
    bullet.visible = false
    bullet.set_process(false)

# 2. Use groups for efficient queries
func _ready() -> void:
    add_to_group("enemies")

func damage_all_enemies(amount: int) -> void:
    for enemy in get_tree().get_nodes_in_group("enemies"):
        enemy.take_damage(amount)

# 3. Disable processing for inactive objects
func deactivate() -> void:
    set_process(false)
    set_physics_process(false)
    visible = false

func activate() -> void:
    set_process(true)
    set_physics_process(true)
    visible = true

# 4. Use call_deferred for non-urgent operations
func spawn_many_enemies(count: int) -> void:
    for i in count:
        call_deferred("spawn_enemy_deferred")

# 5. Cache frequently accessed nodes
@onready var player: Node2D = get_node("/root/Main/Player")
# Instead of get_node() every frame
```

### Memory Management

```gdscript
# Free nodes properly
func remove_enemy(enemy: Node2D) -> void:
    enemy.queue_free()  # Deferred, safe

# Clear references
func _exit_tree() -> void:
    target = null
    weapons.clear()

# Preload vs Load
var always_used = preload("res://common.tscn")  # Load at startup
var sometimes_used: PackedScene  # Load when needed

func load_optional() -> void:
    if sometimes_used == null:
        sometimes_used = load("res://optional.tscn")
```

---

## Debugging

### Debug Drawing

```gdscript
# Draw debug shapes
func _draw() -> void:
    draw_circle(Vector2.ZERO, attack_range, Color(1, 0, 0, 0.3))
    draw_line(Vector2.ZERO, velocity, Color.GREEN, 2)

# Force redraw
queue_redraw()

# Debug label
@onready var debug_label: Label = $DebugLabel

func _process(delta: float) -> void:
    if OS.is_debug_build():
        debug_label.text = "FPS: %d\nPos: %s\nState: %s" % [
            Engine.get_frames_per_second(),
            position,
            current_state.name
        ]
```

### Print Debugging

```gdscript
# Basic print
print("Value: ", value)
print("Dict: ", some_dict)

# Formatted
print("Player at (%d, %d)" % [position.x, position.y])

# Warnings/errors
push_warning("Something might be wrong")
push_error("Something is definitely wrong")

# Assertions (debug only)
assert(health >= 0, "Health cannot be negative")
```

### Remote Debugger

```gdscript
# Breakpoints: Click line number in editor
# Or use breakpoint() function
func suspicious_function() -> void:
    if some_condition:
        breakpoint()  # Pause here

# Profiler: available in editor during play
# Shows function call times, physics, etc.
```

---

## Resources

- [Godot Documentation](https://docs.godotengine.org/en/stable/)
- [GDScript Reference](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_basics.html)
- [Godot Asset Library](https://godotengine.org/asset-library/asset)
- [Godot Forums](https://forum.godotengine.org/)
- [Godot Discord](https://discord.gg/godotengine)
- [KidsCanCode Tutorials](https://kidscancode.org/godot_recipes/)
