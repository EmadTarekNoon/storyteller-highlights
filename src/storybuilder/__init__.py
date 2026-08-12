"""storybuilder: turn sports match events into a Story (JSON bundle of Pages).

The package is intentionally split into sport-agnostic core logic and two
pluggable seams so it works for any two teams and can scale to other sports:

- ``adapters``: parse a raw provider feed into the internal :class:`~storybuilder.models.Match` model.
- ``profiles``: supply sport-specific semantics (scoring, ranking weights, captions).
"""

__version__ = "0.1.0"
