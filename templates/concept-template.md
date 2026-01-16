# Game Concept: {{ title }}

> Concept {{ concept_number | default("") }} of {{ total_concepts | default("") }}
> Generated: {{ generated_at }}

---

## Elevator Pitch

{{ elevator_pitch }}

---

## Core Hook

{{ core_hook }}

---

## Key Features

{% for feature in key_features %}
- {{ feature }}
{% endfor %}

---

## Target Experience

**Player Fantasy:** {{ player_fantasy }}

**Emotional Journey:** {{ emotional_journey }}

**Session Length:** {{ session_length }}

---

## Genre & Style

**Primary Genre:** {{ primary_genre }}

**Sub-genres:** {{ sub_genres | join(", ") }}

**Tone:** {{ tone }}

**Visual Style:** {{ visual_style }}

---

## Core Mechanics Preview

{% for mechanic in core_mechanics %}
### {{ mechanic.name }}
{{ mechanic.brief_description }}
{% endfor %}

---

## Similar Games

{% for game in similar_games %}
- **{{ game.name }}**: {{ game.what_we_take }}
{% endfor %}

---

## Unique Selling Points

{% for usp in unique_selling_points %}
1. {{ usp }}
{% endfor %}

---

## Technical Fit

**Recommended Engine:** {{ recommended_engine }}

**Complexity Level:** {{ complexity_level }}

**Estimated Scope:** {{ estimated_scope }}

---

## Risks & Considerations

{% for risk in risks %}
- {{ risk }}
{% endfor %}

---

## Why This Concept?

{{ rationale }}
