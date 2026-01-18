extends CharacterBody2D
class_name Player
## Player controller with basic movement.
## Supports platformer and top-down movement styles.

# Signals
signal health_changed(new_health: int)
signal died

# Movement configuration
@export_group("Movement")
@export var speed: float = 200.0
@export var jump_velocity: float = -350.0
@export var gravity_scale: float = 1.0

# Combat configuration
@export_group("Combat")
@export var max_health: int = 100
@export var invulnerability_time: float = 1.0

# State
var health: int = 100
var is_invulnerable: bool = false

# References
@onready var sprite: Sprite2D = $Sprite2D
@onready var anim: AnimationPlayer = $AnimationPlayer
@onready var collision_shape: CollisionShape2D = $CollisionShape2D

# Physics constants
const GRAVITY: float = 980.0

func _ready() -> void:
	health = max_health
	add_to_group("player")
	EventBus.player_spawned.emit(self)

func _physics_process(delta: float) -> void:
	_handle_movement(delta)
	_update_animation()

func _handle_movement(delta: float) -> void:
	# Apply gravity (for platformer mode)
	if not is_on_floor():
		velocity.y += GRAVITY * gravity_scale * delta

	# Handle jump
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	# Handle horizontal movement
	var direction := Input.get_axis("move_left", "move_right")
	if direction:
		velocity.x = direction * speed
	else:
		velocity.x = move_toward(velocity.x, 0, speed)

	# For top-down mode, also handle vertical input
	# Uncomment the following for top-down movement:
	# var v_direction := Input.get_axis("move_up", "move_down")
	# velocity.y = v_direction * speed

	move_and_slide()

	# Flip sprite based on direction
	if velocity.x != 0:
		sprite.flip_h = velocity.x < 0

func _update_animation() -> void:
	if not anim:
		return

	if is_on_floor():
		if abs(velocity.x) > 10:
			_play_animation("walk")
		else:
			_play_animation("idle")
	else:
		if velocity.y < 0:
			_play_animation("jump")
		else:
			_play_animation("fall")

func _play_animation(anim_name: String) -> void:
	if anim.has_animation(anim_name) and anim.current_animation != anim_name:
		anim.play(anim_name)

func take_damage(amount: int) -> void:
	if is_invulnerable:
		return

	health = maxi(health - amount, 0)
	health_changed.emit(health)
	EventBus.player_health_changed.emit(health, max_health)
	EventBus.damage_taken.emit(amount, null)

	if health <= 0:
		die()
	else:
		_start_invulnerability()

func _start_invulnerability() -> void:
	is_invulnerable = true

	# Flash effect
	var tween = create_tween()
	for i in 5:
		tween.tween_property(sprite, "modulate:a", 0.3, 0.1)
		tween.tween_property(sprite, "modulate:a", 1.0, 0.1)

	await get_tree().create_timer(invulnerability_time).timeout
	is_invulnerable = false
	sprite.modulate.a = 1.0

func heal(amount: int) -> void:
	health = mini(health + amount, max_health)
	health_changed.emit(health)
	EventBus.player_health_changed.emit(health, max_health)

func die() -> void:
	died.emit()
	EventBus.player_died.emit()
	GameManager.lose_life()

	# Death animation/effect
	var tween = create_tween()
	tween.tween_property(sprite, "modulate", Color.RED, 0.2)
	tween.tween_property(self, "scale", Vector2.ZERO, 0.3)
	await tween.finished

	queue_free()
