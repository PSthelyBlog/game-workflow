extends Node2D
## Main game scene controller.
## Handles scene initialization and coordinates between game systems.

@onready var ui: CanvasLayer = $UI

func _ready() -> void:
	# Connect to global signals
	EventBus.game_started.connect(_on_game_started)
	EventBus.game_over.connect(_on_game_over)

	# Initialize game
	_setup_game()

func _setup_game() -> void:
	# Add HUD
	var hud_scene = preload("res://scenes/ui/hud.tscn")
	var hud = hud_scene.instantiate()
	ui.add_child(hud)

	# Add Pause Menu
	var pause_scene = preload("res://scenes/ui/pause_menu.tscn")
	var pause_menu = pause_scene.instantiate()
	add_child(pause_menu)

	# Spawn player
	_spawn_player()

	# Start game
	GameManager.start_game()

func _spawn_player() -> void:
	var player_scene = preload("res://scenes/entities/player.tscn")
	var player = player_scene.instantiate()
	player.position = Vector2(400, 300)
	add_child(player)
	GameManager.player = player

func _on_game_started() -> void:
	# Game started logic
	pass

func _on_game_over() -> void:
	# Transition to game over screen
	await get_tree().create_timer(1.0).timeout
	get_tree().change_scene_to_file("res://scenes/ui/game_over.tscn")
