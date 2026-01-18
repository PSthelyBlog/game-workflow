extends Control
## Game over screen controller.

@onready var score_label: Label = $VBoxContainer/ScoreLabel
@onready var retry_button: Button = $VBoxContainer/RetryButton

func _ready() -> void:
	# Display final score
	score_label.text = "Score: %d" % GameManager.score

	# Show high score if achieved
	if GameManager.score >= GameManager.high_score and GameManager.score > 0:
		score_label.text += "\nNEW HIGH SCORE!"

	# Grab focus
	retry_button.grab_focus()

	# Fade in
	modulate.a = 0
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 1.0, 0.5)

func _on_retry_pressed() -> void:
	GameManager.reset_game()
	get_tree().change_scene_to_file("res://scenes/main.tscn")

func _on_main_menu_pressed() -> void:
	GameManager.reset_game()
	get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")
