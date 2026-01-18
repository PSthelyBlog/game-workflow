extends Node
## Global game state manager.
## Handles score, health, lives, and game flow.

# Signals
signal score_changed(new_score: int)
signal health_changed(new_health: int)
signal lives_changed(new_lives: int)
signal game_started
signal game_over

# Game state
var score: int = 0 : set = set_score
var high_score: int = 0
var lives: int = 3 : set = set_lives
var is_game_over: bool = false
var is_paused: bool = false

# Player reference
var player: Node2D = null

# Configuration
const STARTING_LIVES: int = 3

func _ready() -> void:
	_load_high_score()

func start_game() -> void:
	score = 0
	lives = STARTING_LIVES
	is_game_over = false
	is_paused = false
	game_started.emit()

func set_score(value: int) -> void:
	score = value
	score_changed.emit(score)

	if score > high_score:
		high_score = score
		_save_high_score()

func add_score(amount: int) -> void:
	score += amount

func set_lives(value: int) -> void:
	lives = value
	lives_changed.emit(lives)

	if lives <= 0 and not is_game_over:
		trigger_game_over()

func lose_life() -> void:
	lives -= 1

func trigger_game_over() -> void:
	is_game_over = true
	game_over.emit()
	EventBus.game_over.emit()

func pause_game() -> void:
	is_paused = true
	get_tree().paused = true
	EventBus.game_paused.emit()

func resume_game() -> void:
	is_paused = false
	get_tree().paused = false
	EventBus.game_resumed.emit()

func toggle_pause() -> void:
	if is_paused:
		resume_game()
	else:
		pause_game()

func reset_game() -> void:
	score = 0
	lives = STARTING_LIVES
	is_game_over = false
	is_paused = false
	get_tree().paused = false

func _save_high_score() -> void:
	var config = ConfigFile.new()
	config.set_value("game", "high_score", high_score)
	config.save("user://game_data.cfg")

func _load_high_score() -> void:
	var config = ConfigFile.new()
	if config.load("user://game_data.cfg") == OK:
		high_score = config.get_value("game", "high_score", 0)
