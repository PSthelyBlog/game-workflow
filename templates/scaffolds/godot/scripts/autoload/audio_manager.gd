extends Node
## Global audio manager.
## Handles music and sound effects with pooling.

# Audio players
var music_player: AudioStreamPlayer
var sfx_pool: Array[AudioStreamPlayer] = []

# Configuration
const POOL_SIZE: int = 8
var pool_index: int = 0

# Volume settings (0.0 to 1.0)
var music_volume: float = 0.5 : set = set_music_volume
var sfx_volume: float = 0.7 : set = set_sfx_volume
var is_muted: bool = false

func _ready() -> void:
	# Create music player
	music_player = AudioStreamPlayer.new()
	music_player.bus = "Music"
	add_child(music_player)

	# Create SFX pool
	for i in POOL_SIZE:
		var player = AudioStreamPlayer.new()
		player.bus = "SFX"
		add_child(player)
		sfx_pool.append(player)

	# Load saved settings
	_load_settings()

func play_music(stream: AudioStream, fade_duration: float = 1.0) -> void:
	if music_player.playing:
		# Fade out current music
		var tween = create_tween()
		tween.tween_property(music_player, "volume_db", -80, fade_duration)
		await tween.finished

	music_player.stream = stream
	music_player.volume_db = -80
	music_player.play()

	# Fade in new music
	var tween = create_tween()
	tween.tween_property(music_player, "volume_db", linear_to_db(music_volume), fade_duration)

func stop_music(fade_duration: float = 1.0) -> void:
	if not music_player.playing:
		return

	var tween = create_tween()
	tween.tween_property(music_player, "volume_db", -80, fade_duration)
	await tween.finished
	music_player.stop()

func play_sfx(stream: AudioStream, pitch_variance: float = 0.0) -> void:
	if is_muted or stream == null:
		return

	var player = sfx_pool[pool_index]
	pool_index = (pool_index + 1) % POOL_SIZE

	player.stream = stream
	player.volume_db = linear_to_db(sfx_volume)
	player.pitch_scale = 1.0 + randf_range(-pitch_variance, pitch_variance)
	player.play()

func play_sfx_at_position(stream: AudioStream, position: Vector2) -> void:
	if is_muted or stream == null:
		return

	var player = AudioStreamPlayer2D.new()
	player.stream = stream
	player.bus = "SFX"
	player.position = position
	player.volume_db = linear_to_db(sfx_volume)
	player.finished.connect(player.queue_free)
	add_child(player)
	player.play()

func set_music_volume(value: float) -> void:
	music_volume = clampf(value, 0.0, 1.0)
	if music_player:
		music_player.volume_db = linear_to_db(music_volume)
	_save_settings()

func set_sfx_volume(value: float) -> void:
	sfx_volume = clampf(value, 0.0, 1.0)
	_save_settings()

func toggle_mute() -> void:
	is_muted = !is_muted
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"), is_muted)
	_save_settings()

func set_mute(muted: bool) -> void:
	is_muted = muted
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"), is_muted)
	_save_settings()

func _save_settings() -> void:
	var config = ConfigFile.new()
	config.set_value("audio", "music_volume", music_volume)
	config.set_value("audio", "sfx_volume", sfx_volume)
	config.set_value("audio", "is_muted", is_muted)
	config.save("user://audio_settings.cfg")

func _load_settings() -> void:
	var config = ConfigFile.new()
	if config.load("user://audio_settings.cfg") == OK:
		music_volume = config.get_value("audio", "music_volume", 0.5)
		sfx_volume = config.get_value("audio", "sfx_volume", 0.7)
		is_muted = config.get_value("audio", "is_muted", false)
		AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"), is_muted)
