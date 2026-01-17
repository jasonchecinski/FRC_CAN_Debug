# bin/formats/gui_formats.py

GUI_CONFIG = {

    "navigation_screens": {

        "home": {
            "buttons": [
                {"label": "Post Process", "action": "go_pp"},
                {"label": "Real Time", "action": "go_rt"},
            ],
            "bottom_button": {"label": "Exit", "action": "exit"}
        },

        "rt_setup": {
            "message": "Please ensure your CAN device is plugged in and configured before continuing.",
            "buttons": [
                {"label": "Continue", "action": "go_rt_menu"}
            ],
            "bottom_button": {"label": "Back", "action": "go_home"}
        },

        "rt_menu": {
            "buttons": [
                {"label": "Live CAN", "action": "go_live_can_input"},
                {"label": "Auto Detect", "action": "go_auto_detect"},
                {"label": "Replay Log", "action": "go_replay_log_input"}
            ],
            "bottom_button": {"label": "Back", "action": "go_home"}
        }
    },

    "input_screens": {

        "pp_input": {
            "title": "Process Log File",
            "fields": [
                {"type": "file", "label": "Select Log File"},
                {"type": "dropdown", "label": "Logging Source",
                 "options": ["Innomaker", "GUI CSV Output"]}
            ],
            "run_action": "run_pp",
            "back_action": "go_home"
        },

        "live_can_input": {
            "title": "Live CAN Settings",
            "fields": [
                {"type": "text", "label": "CAN ID (optional)"},
                {"type": "text", "label": "Baud Rate"},
                {"type": "text", "label": "Timeout (s)"}
            ],
            "run_action": "run_live_can",
            "back_action": "go_rt"
        },

        "replay_log_input": {
            "title": "Replay CAN Log",
            "fields": [
                {"type": "file", "label": "Select Log File"},
                {"type": "dropdown", "label": "Logging Source",
                 "options": ["Innomaker", "GUI CSV Output"]}
            ],
            "run_action": "run_replay_log",
            "back_action": "go_rt"
        }
    },

    "auto_detect": {
        "buttons": [
            {"label": "Start Auto Detect", "action": "start_auto_detect"}
        ],
        "bottom_button": {"label": "Back", "action": "go_rt"}
    }

}


# Global dark theme
DARK_STYLE = """
QWidget {
    background-color: #1e1e1e;
    color: #dddddd;
    font-size: 18px;
}
QPushButton {
    background-color: #333333;
    padding: 10px;
    border-radius: 5px;
}
QPushButton:hover {
    background-color: #444444;
}
QLineEdit, QComboBox {
    background-color: #2a2a2a;
    padding: 6px;
    border-radius: 4px;
}
"""