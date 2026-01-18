extends CanvasLayer
## Pause menu controller.
## Handles pausing and resuming the game.

@onready var panel: Panel = $Panel
@onready var resume_button: Button = $Panel/VBoxContainer/ResumeButton

var is_paused: bool = false

func _ready() -> void:
	panel.visible = false
	# Process even when game is paused
	process_mode = Node.PROCESS_MODE_ALWAYS

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		toggle_pause()

func toggle_pause() -> void:
	is_paused = !is_paused
	panel.visible = is_paused
	get_tree().paused = is_paused

	if is_paused:
		resume_button.grab_focus()
		GameManager.is_paused = true
		EventBus.game_paused.emit()
	else:
		GameManager.is_paused = false
		EventBus.game_resumed.emit()

func _on_resume_pressed() -> void:
	toggle_pause()

func _on_main_menu_pressed() -> void:
	get_tree().paused = false
	GameManager.reset_game()
	get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")

func _on_quit_pressed() -> void:
	get_tree().quit()
