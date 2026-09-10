from src.ui.command_center import render_command_center
from src.ui.theme import configure_page, render_sidebar_context


configure_page("Command Center")
render_sidebar_context()
render_command_center()

