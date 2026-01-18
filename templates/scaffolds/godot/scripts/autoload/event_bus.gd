extends Node
## Global event bus for decoupled communication between systems.
## Use signals here for game-wide events that don't belong to any specific node.

# Game flow signals
signal game_started
signal game_paused
signal game_resumed
signal game_over

# Player signals
signal player_spawned(player: Node2D)
signal player_died
signal player_health_changed(new_health: int, max_health: int)

# Score and progression
signal score_changed(new_score: int)
signal level_completed(level_number: int)
signal checkpoint_reached(checkpoint_id: String)

# Collectibles
signal item_collected(item_type: String, value: int)
signal powerup_activated(powerup_type: String)
signal powerup_expired(powerup_type: String)

# Combat
signal enemy_killed(enemy_type: String, position: Vector2)
signal damage_dealt(amount: int, target: Node2D)
signal damage_taken(amount: int, source: Node2D)

# UI
signal show_notification(message: String, duration: float)
signal dialog_started(dialog_id: String)
signal dialog_ended(dialog_id: String)

# Audio cues (optional integration with AudioManager)
signal play_sound(sound_name: String)
signal play_music(track_name: String)
