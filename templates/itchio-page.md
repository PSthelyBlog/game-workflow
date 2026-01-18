# {{ title }}

{{ tagline }}

---

## About This Game

{{ description }}

{% if story %}
### The Story

{{ story }}
{% endif %}

---

## How to Play

{% if controls is iterable and controls is not string %}
{% for control in controls %}
- **{{ control.input }}**: {{ control.action }}
{% endfor %}
{% else %}
{{ controls }}
{% endif %}

{% if tips %}
### Tips for Success

{% for tip in tips %}
- {{ tip }}
{% endfor %}
{% endif %}

---

## Features

{% for feature in features %}
- {{ feature }}
{% endfor %}

{% if highlights %}
### Highlights

{% for highlight in highlights %}
- **{{ highlight.name }}**: {{ highlight.description }}
{% endfor %}
{% endif %}

---

{% if screenshots %}
## Screenshots

{% for screenshot in screenshots %}
![{{ screenshot.caption }}]({{ screenshot.url }})
{% if screenshot.description %}
*{{ screenshot.description }}*
{% endif %}

{% endfor %}
{% endif %}

---

{% if technical_details %}
## Technical Details

{% if technical_details.resolution %}
- **Resolution**: {{ technical_details.resolution }}
{% endif %}
{% if technical_details.browser_support %}
- **Browser Support**: {{ technical_details.browser_support | join(", ") }}
{% endif %}
{% if technical_details.input_methods %}
- **Input Methods**: {{ technical_details.input_methods | join(", ") }}
{% endif %}
{% if technical_details.save_support is defined %}
- **Save Support**: {{ "Yes" if technical_details.save_support else "No" }}
{% endif %}
{% if technical_details.audio is defined %}
- **Audio**: {{ "Yes - sound effects and music" if technical_details.audio else "No audio" }}
{% endif %}

{% endif %}

---

{% if credits %}
## Credits

{% for credit in credits %}
- **{{ credit.role }}**: {{ credit.name }}{% if credit.link %} ([link]({{ credit.link }})){% endif %}

{% endfor %}
{% endif %}

{% if acknowledgments %}
### Special Thanks

{{ acknowledgments }}
{% endif %}

---

{% if version %}
## Version History

{% if version.current %}
**Current Version**: {{ version.current }}
{% endif %}

{% if version.changelog %}
### Changelog

{% for entry in version.changelog %}
- **{{ entry.version }}** ({{ entry.date }}): {{ entry.description }}
{% endfor %}
{% endif %}
{% endif %}

---

{% if support %}
## Support

{{ support.message }}

{% if support.links %}
{% for link in support.links %}
- [{{ link.label }}]({{ link.url }})
{% endfor %}
{% endif %}
{% endif %}

---

Made with {{ engine | default("Phaser.js") }}

{% if tags %}
---
*Tags: {{ tags | join(", ") }}*
{% endif %}
