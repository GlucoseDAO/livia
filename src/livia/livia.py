"""Livia Zaharia personal website built with Reflex.

This is the app entrypoint. All logic lives in submodules:
- constants.py: shared constants, paths, data classes
- content.py: content loading, markdown preprocessing, tab scanning
- components.py: reusable UI components
- pages.py: page definitions, content state, app registration
"""

from livia.pages import create_app

app = create_app()
