extends Control
## Main menu controller.

@onready var play_button: Button = $VBoxContainer/PlayButton
@onready var options_button: Button = $VBoxContainer/OptionsButton
@onready var quit_button: Button = $VBoxContainer/QuitButton

func _ready() -> void:
	# Grab focus for gamepad support
	play_button.grab_focus()

	# Fade in
	modulate.a = 0
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 1.0, 0.5)

func _on_play_pressed() -> void:
	_transition_to_game()

func _on_options_pressed() -> void:
	# TODO: Show options panel
	pass

func _on_quit_pressed() -> void:
	get_tree().quit()

func _transition_to_game() -> void:
	# Fade out
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.3)
	await tween.finished

	get_tree().change_scene_to_file("res://scenes/main.tscn")

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept") and play_button.has_focus():
		_on_play_pressed()
