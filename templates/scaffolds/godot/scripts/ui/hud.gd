extends CanvasLayer
## HUD controller.
## Displays score, health, and other game information.

@onready var health_label: Label = $MarginContainer/TopBar/HealthLabel
@onready var score_label: Label = $MarginContainer/TopBar/ScoreLabel

func _ready() -> void:
	# Connect to game events
	GameManager.score_changed.connect(_on_score_changed)
	EventBus.player_health_changed.connect(_on_health_changed)

	# Initialize display
	_update_score_display(GameManager.score)
	_update_health_display(100, 100)

func _on_score_changed(new_score: int) -> void:
	_update_score_display(new_score)

	# Pop animation
	var tween = create_tween()
	tween.tween_property(score_label, "scale", Vector2(1.2, 1.2), 0.1)
	tween.tween_property(score_label, "scale", Vector2.ONE, 0.1)

func _on_health_changed(new_health: int, max_health: int) -> void:
	_update_health_display(new_health, max_health)

	# Flash red on damage
	var tween = create_tween()
	tween.tween_property(health_label, "modulate", Color.RED, 0.1)
	tween.tween_property(health_label, "modulate", Color.WHITE, 0.1)

func _update_score_display(score: int) -> void:
	score_label.text = "Score: %d" % score

func _update_health_display(health: int, max_health: int) -> void:
	health_label.text = "Health: %d" % health
