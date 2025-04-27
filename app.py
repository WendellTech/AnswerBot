import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
import time
import threading
from PIL import Image, ImageTk  
import re
import html as html_parser 
import traceback 
import sys 
import copy 

debug_mode = False

try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from openai import OpenAI, APIError, RateLimitError
except ImportError:
    OpenAI = None
    APIError = None
    RateLimitError = None
try:
    import requests
except ImportError:
    requests = None

CONFIG_FILE = "answerbot_config.json"
SYSTEM_PROMPT_FILE = "SystemPrompt.txt"
RESULT_PROMPT_FILE = "ResultPrompt.txt"
USER_PROMPT_FILE = "UserPrompt.txt"

DEFAULT_SETTINGS = {
    "api_type": "Ollama",  
    "api_key": "",
    "openai_endpoint_url": "", 
    "ollama_endpoint_url": "http://localhost:11434", 
    "model": "llama3", 
    "rate_limit_seconds": 2,
    "theme": "Mocha Dark", 
    "always_on_top": False,
    "openai_system_prompt_support": True, 
}

THEMES = {
    "Mocha": {
        "ctk_mode": "light",
        "ctk_theme": "blue", 
        "bg_color": "#f5e0dc", 
        "fg_color": "#4c4f69", 
        "btn_color": "#dc8a78", 
        "btn_hover_color": "#dd7878", 
        "btn_text_color": "#f5e0dc", 
        "entry_color": "#e6e9ef", 
        "text_color": "#4c4f69", 
        "text_box_bg": "#ccd0da", 
        "text_box_fg": "#4c4f69",
        "code_bg": "#bcc0cc", 
        "code_fg": "#4c4f69", 
        "code_border": "#fe640b", 
        "answer_fg_color": "#40a02b", 
        "error_fg_color": "#d20f39", 
        "box_border_color": "#04a5e5", 
        "box_title_bg": "#eff1f5", 
        "status_text_color": "#4c4f69",
    },
    "Mocha Dark": {
        "ctk_mode": "dark",
        "ctk_theme": "blue", 
        "bg_color": "#1e1e2e", 
        "fg_color": "#cdd6f4", 
        "btn_color": "#f5c2e7", 
        "btn_hover_color": "#cba6f7", 
        "btn_text_color": "#1e1e2e", 
        "entry_color": "#181825", 
        "text_color": "#cdd6f4", 
        "text_box_bg": "#11111b", 
        "text_box_fg": "#cdd6f4",
        "code_bg": "#181825", 
        "code_fg": "#cdd6f4", 
        "code_border": "#fab387", 
        "answer_fg_color": "#a6e3a1", 
        "error_fg_color": "#f38ba8", 
        "box_border_color": "#89b4fa", 
        "box_title_bg": "#313244", 
        "status_text_color": "#cdd6f4",
    },
    "Fluent": {
        "ctk_mode": "light",
        "ctk_theme": "blue",
        "bg_color": "#ffffff",
        "fg_color": "#000000",
        "btn_color": "#0078d4",
        "btn_hover_color": "#106ebe",
        "btn_text_color": "#ffffff",
        "entry_color": "#f3f3f3",
        "text_color": "#000000",
        "text_box_bg": "#f8f8f8",
        "text_box_fg": "#333333",
        "code_bg": "#eeeeee",
        "code_fg": "#000000",
        "code_border": "#0078d4",
        "answer_fg_color": "#107c10", 
        "error_fg_color": "#d83b01", 
        "box_border_color": "#005a9e", 
        "box_title_bg": "#e1dfdd", 
        "status_text_color": "#000000",
    },
    "Fluent Dark": {
        "ctk_mode": "dark",
        "ctk_theme": "dark-blue",
        "bg_color": "#1e1e1e",
        "fg_color": "#d4d4d4",
        "btn_color": "#007acc",
        "btn_hover_color": "#0090f1",
        "btn_text_color": "#ffffff",
        "entry_color": "#252526",
        "text_color": "#d4d4d4",
        "text_box_bg": "#1e1e1e",
        "text_box_fg": "#cccccc",
        "code_bg": "#2d2d2d",
        "code_fg": "#d4d4d4",
        "code_border": "#007acc",
        "answer_fg_color": "#60c760", 
        "error_fg_color": "#f08f7a", 
        "box_border_color": "#2e83cf", 
        "box_title_bg": "#3c3c3c", 
        "status_text_color": "#d4d4d4",
    }
}

def load_settings():
    """Loads settings from the JSON file."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(CONFIG_FILE, 'r') as f:
            settings = json.load(f)

            for key, value in DEFAULT_SETTINGS.items():
                settings.setdefault(key, value)
            return settings
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}. Using default settings.")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Saves settings to the JSON file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except IOError as e:
        print(f"Error saving settings: {e}")

def load_prompt_file(filename):
    """Loads content from a prompt file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Prompt file not found: {filename}")
        return None
    except IOError as e:
        print(f"ERROR: Could not read prompt file {filename}: {e}")
        return None

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.settings = parent.settings.copy() 

        self.title("AnswerBot Settings")
        self.geometry("450x580") 
        self.transient(parent) 
        self.grab_set() 

        self.protocol("WM_DELETE_WINDOW", self.cancel) 

        self.grid_columnconfigure(1, weight=1)
        row_index = 0

        theme_label = ctk.CTkLabel(self, text="Theme:")
        theme_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.theme_var = ctk.StringVar(value=self.settings["theme"])
        theme_menu = ctk.CTkOptionMenu(self, variable=self.theme_var, values=list(THEMES.keys()))
        theme_menu.grid(row=row_index, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_index += 1

        api_type_label = ctk.CTkLabel(self, text="API Type:")
        api_type_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.api_type_var = ctk.StringVar(value=self.settings["api_type"])
        api_type_menu = ctk.CTkOptionMenu(self, variable=self.api_type_var,
                                          values=["OpenAI", "Gemini", "Ollama"],
                                          command=self.update_api_fields)
        api_type_menu.grid(row=row_index, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_index += 1

        self.api_key_label = ctk.CTkLabel(self, text="API Key:")
        self.api_key_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.api_key_entry = ctk.CTkEntry(self, show="*")
        self.api_key_entry.insert(0, self.settings.get("api_key", ""))
        self.api_key_entry.grid(row=row_index, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_index += 1

        self.openai_endpoint_label = ctk.CTkLabel(self, text="OpenAI Endpoint URL (Optional):")
        self.openai_endpoint_entry = ctk.CTkEntry(self)
        self.openai_endpoint_entry.insert(0, self.settings.get("openai_endpoint_url", ""))
        self.openai_endpoint_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.openai_endpoint_entry.grid(row=row_index, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_index += 1

        self.openai_system_prompt_label = ctk.CTkLabel(self, text="Use System Prompt Role:")
        self.openai_system_prompt_var = ctk.BooleanVar(value=self.settings.get("openai_system_prompt_support", True))
        self.openai_system_prompt_switch = ctk.CTkSwitch(self, variable=self.openai_system_prompt_var, text="")
        self.openai_system_prompt_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.openai_system_prompt_switch.grid(row=row_index, column=1, padx=10, pady=5, sticky="w")
        row_index += 1

        self.ollama_endpoint_label = ctk.CTkLabel(self, text="Ollama Endpoint URL:")
        self.ollama_endpoint_entry = ctk.CTkEntry(self)
        self.ollama_endpoint_entry.insert(0, self.settings.get("ollama_endpoint_url", DEFAULT_SETTINGS["ollama_endpoint_url"]))
        self.ollama_endpoint_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.ollama_endpoint_entry.grid(row=row_index, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_index += 1

        model_label = ctk.CTkLabel(self, text="Model Name:")
        model_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.model_entry = ctk.CTkEntry(self)
        self.model_entry.insert(0, self.settings.get("model", DEFAULT_SETTINGS["model"]))
        self.model_entry.grid(row=row_index, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        row_index += 1

        rate_limit_label = ctk.CTkLabel(self, text="Rate Limit (seconds):")
        rate_limit_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.rate_limit_var = tk.IntVar(value=self.settings["rate_limit_seconds"])
        self.rate_limit_slider = ctk.CTkSlider(self, from_=0, to=60, number_of_steps=60,
                                               variable=self.rate_limit_var, command=self.update_rate_limit_label)
        self.rate_limit_slider.grid(row=row_index, column=1, padx=10, pady=5, sticky="ew")
        self.rate_limit_value_label = ctk.CTkLabel(self, text=f"{self.settings['rate_limit_seconds']}s")
        self.rate_limit_value_label.grid(row=row_index, column=2, padx=5, pady=5, sticky="w")
        row_index += 1

        always_on_top_label = ctk.CTkLabel(self, text="Always on Top:")
        always_on_top_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
        self.always_on_top_var = ctk.BooleanVar(value=self.settings["always_on_top"])
        always_on_top_switch = ctk.CTkSwitch(self, variable=self.always_on_top_var, text="")
        always_on_top_switch.grid(row=row_index, column=1, padx=10, pady=5, sticky="w")
        row_index += 1

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=row_index, column=0, columnspan=3, pady=20)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save)
        save_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.cancel, fg_color="grey")
        cancel_button.pack(side="left", padx=10)

        self.update_api_fields(self.settings["api_type"])
        self.update_rate_limit_label(self.settings["rate_limit_seconds"]) 

    def update_rate_limit_label(self, value):
        """Updates the label next to the slider."""
        self.rate_limit_value_label.configure(text=f"{int(value)}s")

    def update_api_fields(self, selected_api):
        """Shows/hides API key and endpoint fields based on selection."""

        # Hide everything initially
        self.api_key_label.grid_remove()
        self.api_key_entry.grid_remove()
        self.openai_endpoint_label.grid_remove()
        self.openai_endpoint_entry.grid_remove()
        self.openai_system_prompt_label.grid_remove() # Keep generic name or rename later
        self.openai_system_prompt_switch.grid_remove()
        self.ollama_endpoint_label.grid_remove()
        self.ollama_endpoint_entry.grid_remove()

        if selected_api == "OpenAI":
            self.api_key_label.grid()
            self.api_key_entry.grid()
            self.openai_endpoint_label.grid()
            self.openai_endpoint_entry.grid()
            self.openai_system_prompt_label.grid() # Show the label
            self.openai_system_prompt_switch.grid(sticky='w') # Show the switch
            if not OpenAI:
                messagebox.showwarning("Missing Library", "The 'openai' library is not installed. Please install it (`pip install openai`) to use the OpenAI API.", parent=self)
        elif selected_api == "Gemini":
            self.api_key_label.grid()
            self.api_key_entry.grid()
            if not genai:
                 messagebox.showwarning("Missing Library", "The 'google-generativeai' library is not installed. Please install it (`pip install google-generativeai`) to use the Gemini API.", parent=self)
        elif selected_api == "Ollama":
            self.ollama_endpoint_label.grid()
            self.ollama_endpoint_entry.grid()
            self.openai_system_prompt_label.grid() # <-- ADD THIS LINE: Show the label
            self.openai_system_prompt_switch.grid(sticky='w') # <-- ADD THIS LINE: Show the switch
            if not requests:
                 messagebox.showwarning("Missing Library", "The 'requests' library is not installed. Please install it (`pip install requests`) to use the Ollama API.", parent=self)

    def save(self):
        """Saves the settings and closes the window."""
        self.settings["theme"] = self.theme_var.get()
        self.settings["api_type"] = self.api_type_var.get()
        self.settings["api_key"] = self.api_key_entry.get()
        self.settings["openai_endpoint_url"] = self.openai_endpoint_entry.get()
        self.settings["ollama_endpoint_url"] = self.ollama_endpoint_entry.get()
        self.settings["model"] = self.model_entry.get()
        self.settings["rate_limit_seconds"] = self.rate_limit_var.get()
        self.settings["always_on_top"] = self.always_on_top_var.get()
        self.settings["openai_system_prompt_support"] = self.openai_system_prompt_var.get()

        api_changed = self.parent.settings["api_type"] != self.settings["api_type"]
        model_changed = self.parent.settings["model"] != self.settings["model"]

        self.parent.settings = self.settings.copy() 
        save_settings(self.parent.settings)
        self.parent.apply_theme() 
        self.parent.toggle_always_on_top(force_state=self.settings["always_on_top"]) 
        self.parent.cancel_rate_limit_timers() 

        if api_changed or model_changed:
            if debug_mode: print("DEBUG: API type or Model changed. Forcing new chat.")
            messagebox.showinfo("Settings Changed", "API type or model was changed. Starting a new chat session.", parent=self.parent)
            self.parent.new_chat() 

        self.destroy()

    def cancel(self):
        """Closes the window without saving."""
        self.destroy()

class AnswerBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()
        self.conversation_history = [] 
        self.last_api_call_time = 0
        self.rate_limit_api_call_timer_id = None 
        self.rate_limit_countdown_timer_id = None 
        self.status_clear_timer_id = None 
        self.is_ai_thinking = False
        self.current_api_thread = None 
        self.expecting_response = True 
        self.current_theme_settings = None 
        self.conversation_active = False 
        self.waiting_for_user_detail = False 
        self.last_tool_invoked = None 
        self._gemini_chat_session = None 

        self.system_prompt_template = load_prompt_file(SYSTEM_PROMPT_FILE)
        self.result_prompt_template = load_prompt_file(RESULT_PROMPT_FILE)
        self.user_prompt_template = load_prompt_file(USER_PROMPT_FILE)

        if not all([self.system_prompt_template, self.result_prompt_template, self.user_prompt_template]):
             messagebox.showerror("Error", "Could not load required prompt files (SystemPrompt.txt, ResultPrompt.txt, UserPrompt.txt). Please ensure they exist in the same directory as the script.")
             self.destroy() 
             return

        self.title("AnswerBot")
        self.geometry("600x700") 
        self.minsize(400, 500)

        initial_theme_name = self.settings.get("theme", "Mocha Dark")
        if initial_theme_name not in THEMES:
            initial_theme_name = "Mocha Dark" 
        initial_ctk_mode = THEMES[initial_theme_name]["ctk_mode"]
        ctk.set_appearance_mode(initial_ctk_mode)

        self._always_on_top = self.settings.get("always_on_top", False)

        self.grid_rowconfigure(1, weight=1) 
        self.grid_rowconfigure(2, weight=0) 
        self.grid_columnconfigure(0, weight=1) 

        self.top_frame = ctk.CTkFrame(self, height=40)
        self.top_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.top_frame.grid_columnconfigure(0, weight=0) 
        self.top_frame.grid_columnconfigure(1, weight=0) 
        self.top_frame.grid_columnconfigure(2, weight=0) 
        self.top_frame.grid_columnconfigure(3, weight=1) 

        self.settings_button = ctk.CTkButton(self.top_frame, text="⚙️", width=30, command=self.open_settings)
        self.settings_button.grid(row=0, column=0, padx=(0, 5))

        self.always_on_top_button = ctk.CTkButton(self.top_frame, text="📌", width=30, command=self.toggle_always_on_top)
        self.always_on_top_button.grid(row=0, column=1, padx=5)

        self.new_chat_button = ctk.CTkButton(self.top_frame, text="✨ New Chat", width=80, command=self.new_chat)
        self.new_chat_button.grid(row=0, column=2, padx=5)

        self.status_label = ctk.CTkLabel(self.top_frame, text="", anchor="e") 
        self.status_label.grid(row=0, column=3, padx=(10, 0), sticky="e")

        self.chat_scroll_frame = ctk.CTkScrollableFrame(self, border_width=0)
        self.chat_scroll_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.chat_scroll_frame.grid_columnconfigure(0, weight=1) 

        self.message_widgets = [] 

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkTextbox(self.input_frame, height=40, wrap="word", border_width=1)
        self.input_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.input_entry.bind("<KeyPress>", self.handle_input_keypress)

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=70, command=self.send_message_event)
        self.send_button.grid(row=0, column=1, sticky="e") 

        self.apply_theme() 
        self.toggle_always_on_top(force_state=self._always_on_top) 
        self.protocol("WM_DELETE_WINDOW", self.on_closing) 

    def handle_input_keypress(self, event):
        """Handles key presses in the input textbox for Shift+Enter."""
        is_shift_pressed = (event.state & 0x1) != 0

        if event.keysym == 'Return' and is_shift_pressed:
            pass 
        elif event.keysym == 'Return' and not is_shift_pressed:
            self.send_message_event()
            return "break" 
        return None

    def _configure_chat_display_tags(self):
        """ Configures tags for basic text styling (color, simple emphasis).
            No complex markdown. Needs to be called by apply_theme.
            Operates on the underlying Text widget if needed, but might not be
            necessary if just adding labels to scrollable frame.
            However, let's configure basic tags for potential direct text insertion.
        """
        if not hasattr(self, 'current_theme_settings') or not self.current_theme_settings:
             if debug_mode: print("DEBUG: Skipping tag config, theme settings not ready.")
             return

        theme = self.current_theme_settings
        answer_fg = theme.get("answer_fg_color", "green")
        text_fg = theme.get("text_box_fg", "#FFFFFF") 

        try:

            base_font_ctk = self.input_entry.cget("font")
            base_family = "Arial"
            base_size = 12
            if isinstance(base_font_ctk, ctk.CTkFont):
                 base_family = base_font_ctk.cget("family")
                 base_size = base_font_ctk.cget("size")
            elif isinstance(base_font_ctk, (tuple, list)) and len(base_font_ctk) >= 2:
                base_family = base_font_ctk[0]; base_size = int(base_font_ctk[1])

            font_bold = ctk.CTkFont(family=base_family, size=base_size, weight="bold")
            font_monospace = ctk.CTkFont(family="monospace", size=base_size -1)
            font_default = ctk.CTkFont(family=base_family, size=base_size)

            self.tag_configs = {
                "user_prefix": {"font": font_bold, "text_color": theme.get("btn_color", "blue")},
                "ai_prefix": {"font": font_bold, "text_color": theme.get("btn_hover_color", "lightblue")},
                "answer_text": {"text_color": answer_fg, "font": font_default},
                "latex_text": {"text_color": text_fg, "font": font_monospace}, 
                "latex_answer_text": {"text_color": answer_fg, "font": font_monospace}, 
                "error_text": {"text_color": theme.get("error_fg_color", "red"), "font": font_default},
                "default_text": {"text_color": text_fg, "font": font_default},
                "code_text": {"font": font_monospace, "text_color": theme.get("code_fg", text_fg)}
            }
            if debug_mode: print("DEBUG: Stored basic tag configurations.")

        except Exception as e:
             print(f"ERROR: Could not configure basic text styles: {e}")
             self.tag_configs = {}

    def apply_theme(self):
        """Applies the selected theme to the application."""
        theme_name = self.settings.get("theme", "Mocha Dark")
        if theme_name not in THEMES:
            theme_name = "Mocha Dark" 
        self.current_theme_settings = THEMES[theme_name]
        theme = self.current_theme_settings

        ctk.set_appearance_mode(theme["ctk_mode"])

        self.configure(fg_color=theme["bg_color"])
        self.top_frame.configure(fg_color=theme["bg_color"])
        self.input_frame.configure(fg_color=theme["bg_color"])

        button_fg = theme.get("btn_color")
        button_hover = theme.get("btn_hover_color")
        button_text = theme.get("btn_text_color", theme.get("text_color"))
        text_color = theme.get("text_color")
        entry_color = theme.get("entry_color")
        status_text_color = theme.get("status_text_color", text_color)

        common_button_args = {"fg_color": button_fg, "hover_color": button_hover, "text_color": button_text}

        self.settings_button.configure(**common_button_args)
        self.always_on_top_button.configure(**common_button_args)
        self.new_chat_button.configure(**common_button_args)
        self.send_button.configure(**common_button_args)
        self.status_label.configure(text_color=status_text_color)

        self.input_entry.configure(fg_color=entry_color, text_color=text_color, border_color=button_fg, scrollbar_button_color=button_fg, scrollbar_button_hover_color=button_hover)

        self.chat_scroll_frame.configure(fg_color=theme.get("text_box_bg"))

        self._configure_chat_display_tags()

        self._reapply_theme_to_chat_widgets()

        self._update_aot_button_state()

    def _reapply_theme_to_chat_widgets(self):
        """Iterates through existing chat widgets and updates their theme colors."""
        if not self.current_theme_settings or not hasattr(self, 'message_widgets'):
            return
        if debug_mode: print("DEBUG: Reapplying theme to existing chat widgets...")

        theme = self.current_theme_settings
        self._configure_chat_display_tags() 

        for widget_info in self.message_widgets:
            widget = widget_info["widget"]
            widget_type = widget_info["type"]
            style_tag = widget_info.get("style_tag", "default_text") 

            try:

                if widget_type == "message_label":
                    config = self.tag_configs.get(style_tag, self.tag_configs["default_text"])
                    content_widget = widget_info.get("content_widget")
                    if content_widget:
                        content_widget.configure(text_color=config.get("text_color"), font=config.get("font"))

                    prefix_widget = widget_info.get("prefix_widget")
                    if prefix_widget:
                        prefix_tag = widget_info.get("prefix_tag", "default_text")
                        prefix_config = self.tag_configs.get(prefix_tag, self.tag_configs["default_text"])
                        prefix_widget.configure(text_color=prefix_config.get("text_color"), font=prefix_config.get("font"))

                elif widget_type == "titled_box":
                    box_frame = widget 
                    title_label = widget_info["title_widget"]
                    content_label = widget_info["content_widget"]

                    box_frame.configure(fg_color=theme.get("text_box_bg"), border_color=theme.get("box_border_color"))
                    title_label.configure(fg_color=theme.get("box_title_bg"), text_color=theme.get("text_color"), font=ctk.CTkFont(weight="bold")) 

                    content_config = self.tag_configs.get(style_tag, self.tag_configs["default_text"])
                    content_label.configure(text_color=content_config.get("text_color"), font=content_config.get("font"))

                elif widget_type == "code_block":
                    code_frame = widget 
                    code_textbox = widget_info["textbox_widget"]

                    code_frame.configure(fg_color=theme.get("code_bg"), border_color=theme.get("code_border"))
                    text_config = self.tag_configs.get("code_text", self.tag_configs["default_text"])
                    code_textbox.configure(
                        fg_color=theme.get("code_bg"), 
                        text_color=text_config.get("text_color"),
                        font=text_config.get("font")
                    )

                    copy_button = widget_info.get("button_widget")
                    if copy_button:
                         copy_button.configure(
                             fg_color=theme.get("code_border"), 
                             text_color=theme.get("code_bg"), 
                             hover_color=theme.get("btn_hover_color") 
                         )

            except Exception as e:
                print(f"ERROR: Failed to reapply theme to widget {widget}: {e}")
                if debug_mode: traceback.print_exc()

        if debug_mode: print("DEBUG: Finished reapplying theme to chat widgets.")

    def toggle_always_on_top(self, event=None, force_state=None):
        """Toggles the window's always-on-top state."""
        if force_state is not None:
            self._always_on_top = force_state
        else:
            self._always_on_top = not self._always_on_top

        self.attributes("-topmost", self._always_on_top)
        self._update_aot_button_state()

        if force_state is None:
            self.settings["always_on_top"] = self._always_on_top
            save_settings(self.settings)

    def _update_aot_button_state(self):
        """Updates the visual state of the always-on-top button."""
        if not hasattr(self, 'current_theme_settings') or not self.current_theme_settings: return 

        theme = self.current_theme_settings
        button_fg = theme.get("btn_color")
        active_color = theme.get("btn_hover_color", "grey") 

        if self._always_on_top:
            self.always_on_top_button.configure(text="📌 On", fg_color=active_color)
        else:
            self.always_on_top_button.configure(text="📌 Off", fg_color=button_fg)

    def open_settings(self):
        """Opens the settings window."""
        if hasattr(self, 'settings_win') and self.settings_win.winfo_exists():
            self.settings_win.focus()
        else:
            self.settings_win = SettingsWindow(self)

    def new_chat(self):
        """Starts a new chat session."""
        self.cancel_rate_limit_timers() 

        self.expecting_response = False 
        if self.is_ai_thinking:
             if debug_mode: print("DEBUG: Cancelling current AI request due to new chat.")
             self.hide_thinking_indicator() 

        self.conversation_history = [] 
        self._gemini_chat_session = None 
        self.conversation_active = False 
        self.waiting_for_user_detail = False
        self.last_tool_invoked = None

        for item in self.message_widgets:

            if "widget" in item and item["widget"] and item["widget"].winfo_exists():
                try:
                    item["widget"].destroy()
                except tk.TclError as e:
                    print(f"Warning: Error destroying widget during new chat: {e}") 
        self.message_widgets = []

        self.clear_status_message() 
        self.input_entry.configure(state="normal")
        self.send_button.configure(state="normal")
        self.input_entry.focus()
        if debug_mode: print("DEBUG: New chat started. History, UI and state cleared.")

    def set_status_message(self, message, duration_ms=None, is_countdown=False):
        """Displays a message in the status bar, optionally auto-clearing or indicating a countdown."""

        self.status_label.configure(text=message)

        if self.status_clear_timer_id: 
             self.after_cancel(self.status_clear_timer_id)
             self.status_clear_timer_id = None

        if duration_ms and duration_ms > 0 and not is_countdown:
            self.status_clear_timer_id = self.after(duration_ms, self.clear_status_message)

    def clear_status_message(self):
        """Clears the status bar message, avoiding countdowns."""
        if self.rate_limit_countdown_timer_id: 
            return

        self.status_label.configure(text="")
        if self.status_clear_timer_id:
            self.after_cancel(self.status_clear_timer_id)
            self.status_clear_timer_id = None

    def _add_widget_to_chat(self, widget, widget_info):
        """Adds a widget to the scrollable frame and tracks it."""
        widget.pack(pady=(5, 5), padx=5, fill="x", expand=False) 
        widget_info["widget"] = widget 
        self.message_widgets.append(widget_info)
        self.update_idletasks() 

        self.after(50, self.chat_scroll_frame._parent_canvas.yview_moveto, 1.0)

    def add_message_to_gui(self, role, message, style_tag="default_text"):
        """Adds a standard text message (user or AI) to the chat display using Labels."""
        if not message: return
        if not self.current_theme_settings: self.apply_theme() 

        prefix = "You: " if role.lower() == "user" else "AI: "
        prefix_tag = "user_prefix" if role.lower() == "user" else "ai_prefix"

        msg_frame = ctk.CTkFrame(self.chat_scroll_frame, fg_color="transparent")
        msg_frame.grid_columnconfigure(1, weight=1) 

        prefix_config = self.tag_configs.get(prefix_tag, self.tag_configs["default_text"])
        prefix_label = ctk.CTkLabel(
            msg_frame,
            text=prefix,
            font=prefix_config.get("font"),
            text_color=prefix_config.get("text_color"),
            anchor="nw"
        )
        prefix_label.grid(row=0, column=0, sticky="nw", padx=(0, 5))

        message_config = self.tag_configs.get(style_tag, self.tag_configs["default_text"])
        message_label = ctk.CTkLabel(
            msg_frame,
            text=message.strip(), 
            font=message_config.get("font"),
            text_color=message_config.get("text_color"),
            justify="left",
            wraplength=self.chat_scroll_frame.winfo_width() - 60 
        )
        message_label.grid(row=0, column=1, sticky="nw")

        msg_frame.bind("<Configure>", lambda e, lbl=message_label, frm=self.chat_scroll_frame: lbl.configure(wraplength=frm.winfo_width() - 60))

        widget_info = {
            "type": "message_label",
            "role": role,
            "style_tag": style_tag,
            "prefix_tag": prefix_tag,
            "prefix_widget": prefix_label,
            "content_widget": message_label 
        }
        self._add_widget_to_chat(msg_frame, widget_info)

    def add_titled_box_to_gui(self, title, content, content_style_tag="default_text"):
        """Adds a framed box with a title, content, and a copy button."""
        if not self.current_theme_settings: self.apply_theme()
        theme = self.current_theme_settings

        box_frame = ctk.CTkFrame(
            self.chat_scroll_frame,
            fg_color=theme.get("text_box_bg"),
            border_color=theme.get("box_border_color"),
            border_width=2,
            corner_radius=5
        )
        box_frame.grid_columnconfigure(0, weight=1) 

        title_label = ctk.CTkLabel(
            box_frame,
            text=title,
            fg_color=theme.get("box_title_bg"),
            text_color=theme.get("text_color"), 
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
            corner_radius=0 
        )
        title_label.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        content_config = self.tag_configs.get(content_style_tag, self.tag_configs["default_text"])
        content_label = ctk.CTkLabel(
            box_frame,
            text=content.strip(),
            font=content_config.get("font"),
            text_color=content_config.get("text_color"),
            justify="left",
            anchor="nw",
            wraplength=self.chat_scroll_frame.winfo_width() - 80 
        )
        content_label.grid(row=1, column=0, sticky="nw", padx=10, pady=10)

        box_frame.bind("<Configure>", lambda e, lbl=content_label, frm=self.chat_scroll_frame: lbl.configure(wraplength=frm.winfo_width() - 80))

        widget_info = {
            "type": "titled_box",
            "style_tag": content_style_tag,
            "title_widget": title_label,
            "content_widget": content_label
        }

        copy_button = ctk.CTkButton(
            box_frame,
            text="📋",  
            width=30,
            height=30,
            command=lambda c=content.strip(): self._copy_to_clipboard(c),
            fg_color=theme.get("box_border_color"),  
            text_color=theme.get("text_box_bg"),  
            hover_color=theme.get("btn_hover_color")  
        )
        copy_button.place(relx=1.0, rely=0.0, x=-5, y=5, anchor="ne")  

        widget_info["button_widget"] = copy_button  
        self._add_widget_to_chat(box_frame, widget_info)

    def add_code_block_to_gui(self, code, lang=None):
        """Adds a code block with a copy button."""
        if not self.current_theme_settings: self.apply_theme()
        theme = self.current_theme_settings

        code_frame = ctk.CTkFrame(
            self.chat_scroll_frame,
            fg_color=theme.get("code_bg"),
            border_color=theme.get("code_border"),
            border_width=1,
            corner_radius=5
        )
        code_frame.grid_columnconfigure(0, weight=1) 
        code_frame.grid_rowconfigure(0, weight=1)    

        text_config = self.tag_configs.get("code_text", self.tag_configs["default_text"])
        code_textbox = ctk.CTkTextbox(
            code_frame,
            wrap="none", 
            fg_color=theme.get("code_bg"), 
            text_color=text_config.get("text_color"),
            font=text_config.get("font"),
            border_width=0,
            activate_scrollbars=True, 

            height=min(300, max(60, len(code.splitlines()) * 15 + 20)) 
        )
        code_textbox.grid(row=0, column=0, sticky="nsew", padx=(5,0), pady=5) 
        code_textbox.insert("1.0", code.strip())
        code_textbox.configure(state="disabled") 

        copy_symbol = "📋" 

        copy_button = ctk.CTkButton(
            code_frame,
            text=copy_symbol, 
            width=30, 
            height=30,
            command=lambda c=code.strip(): self._copy_to_clipboard(c),
            fg_color=theme.get("code_border"), 
            text_color=theme.get("code_bg"), 
            hover_color=theme.get("btn_hover_color") 
        )

        copy_button.place(relx=1.0, rely=0.0, x=-5, y=5, anchor="ne")

        widget_info = {
            "type": "code_block",
            "textbox_widget": code_textbox,
            "button_widget": copy_button
        }
        self._add_widget_to_chat(code_frame, widget_info)

    def _copy_to_clipboard(self, text_to_copy):
        """Copies text to the system clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(text_to_copy)
            self.set_status_message("✅ Copied to clipboard", 2000)
            if debug_mode: print("DEBUG: Copied code to clipboard.")
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            self.set_status_message("❌ Failed to copy", 2000)

    def _extract_tool_call(self, response_content):
        """ Attempts to extract a single top-level tool call from the response.
            Returns (tool_name, inner_content, error_message).
            Error message is set if format is invalid or multiple/no tools found.
        """
        if not response_content:
            return None, None, "AI response was empty."

        response_content = response_content.strip()

        match = re.fullmatch(r'<(\w+)>(.*?)</\1>', response_content, re.DOTALL | re.IGNORECASE)

        if match:
            tool_name = match.group(1)
            inner_content = match.group(2)
            if debug_mode: print(f"DEBUG: Extracted tool: <{tool_name}>")
            return tool_name.lower(), inner_content, None 
        else:

            partial_match = re.search(r'<(\w+)>(.*?)</\1>', response_content, re.DOTALL | re.IGNORECASE)
            if partial_match:
                err = "Invalid format: Found tool call but also content outside the tags."
                if debug_mode: print(f"DEBUG: {err} Content: {response_content[:100]}...")
                return None, None, err
            else:

                if '<' in response_content or '>' in response_content:
                    err = "Invalid format: No valid tool call found, but contains tag-like characters."
                    if debug_mode: print(f"DEBUG: {err} Content: {response_content[:100]}...")
                    return None, None, err
                else:

                    if debug_mode: print(f"DEBUG: No tool tag found, treating as implicit 'final_answer'.")
                    return "final_answer", response_content, None

    def _extract_params(self, inner_content):
        """ Extracts key-value pairs from the inner content of a tool call.
            Returns a dictionary of parameters. Handles multi-line content.
        """
        params = {}

        matches = re.findall(r'<(\w+)>(.*?)</\1>', inner_content, re.DOTALL | re.IGNORECASE)
        for key, value in matches:
            params[key.lower()] = value.strip() 
        if debug_mode: print(f"DEBUG: Extracted params: {params}")
        return params

    def _handle_tool_response(self, tool_name, inner_content):
        """Main dispatcher for handling validated tool responses."""
        self.last_tool_invoked = tool_name 
        params = self._extract_params(inner_content) if tool_name != "final_answer" else {"ans": inner_content}
        success = False 

        try:
            if tool_name == "request_details":
                success = self._handle_request_details(params)

                return 
            elif tool_name == "short_answer":
                success = self._handle_short_answer(params)
            elif tool_name == "long_answer":
                success = self._handle_long_answer(params)
            elif tool_name == "choice_answer":
                success = self._handle_choice_answer(params)
            elif tool_name == "choice_explain":
                success = self._handle_choice_explain(params)
            elif tool_name == "math_work":
                success = self._handle_math_work(params)
            elif tool_name == "math_answer":
                success = self._handle_math_answer(params)
            elif tool_name == "code_answer":
                success = self._handle_code_answer(params)
            elif tool_name == "final_answer": 
                 success = self._handle_final_answer(params)
            elif tool_name == "none_further":
                success = self._handle_none_further(params)

                return 
            else:

                self.add_message_to_gui("AI", f"Error: Received unknown tool '{tool_name}'.", style_tag="error_text")
                success = False 

            self.hide_thinking_indicator()
            self._send_result_to_ai(tool_name, success)

        except Exception as e:
            print(f"ERROR: Exception while handling tool '{tool_name}': {e}")
            if debug_mode: traceback.print_exc()
            self.add_message_to_gui("AI", f"Internal Error processing tool '{tool_name}'.", style_tag="error_text")
            self.hide_thinking_indicator() 

            self._send_result_to_ai(tool_name, False, error_message="Internal processing error")

    def _handle_request_details(self, params):
        msg = params.get("msg")
        if not msg:
            self.add_message_to_gui("AI", "Error: 'request_details' tool called without 'msg' parameter.", style_tag="error_text")
            return False 

        self.add_titled_box_to_gui("Details Requested", msg, content_style_tag="default_text")
        self.waiting_for_user_detail = True
        if debug_mode: print("DEBUG: Waiting for user detail.")
        self.hide_thinking_indicator() 

        return True 

    def _handle_short_answer(self, params):
        ans = params.get("ans")
        if ans is None: 
            self.add_message_to_gui("AI", "Error: 'short_answer' tool called without 'ans' parameter.", style_tag="error_text")
            return False
        self.add_titled_box_to_gui("Short Answer", ans, content_style_tag="answer_text")
        return True

    def _handle_long_answer(self, params):
        ans = params.get("ans")
        if ans is None:
            self.add_message_to_gui("AI", "Error: 'long_answer' tool called without 'ans' parameter.", style_tag="error_text")
            return False
        self.add_titled_box_to_gui("Long Answer", ans, content_style_tag="answer_text")
        return True

    def _handle_choice_answer(self, params):
        ans = params.get("ans")
        if ans is None:
            self.add_message_to_gui("AI", "Error: 'choice_answer' tool called without 'ans' parameter.", style_tag="error_text")
            return False
        self.add_titled_box_to_gui("Multiple Choice Answer", ans, content_style_tag="answer_text")
        return True

    def _handle_choice_explain(self, params):
        ans = params.get("ans")
        if ans is None:
            self.add_message_to_gui("AI", "Error: 'choice_explain' tool called without 'ans' parameter.", style_tag="error_text")
            return False
        self.add_message_to_gui("AI", ans, style_tag="default_text")
        return True

    def _handle_math_work(self, params):
        work = params.get("work")
        if work is None:
            self.add_message_to_gui("AI", "Error: 'math_work' tool called without 'work' parameter.", style_tag="error_text")
            return False

        self.add_message_to_gui("AI", work, style_tag="latex_text")
        return True

    def _handle_math_answer(self, params):
        ans = params.get("ans")
        if ans is None:
            self.add_message_to_gui("AI", "Error: 'math_answer' tool called without 'ans' parameter.", style_tag="error_text")
            return False
        self.add_message_to_gui("AI", ans, style_tag="latex_answer_text")
        return True

    def _handle_code_answer(self, params):
        code = params.get("code")
        lang = params.get("lang") 
        if code is None:
            self.add_message_to_gui("AI", "Error: 'code_answer' tool called without 'code' parameter.", style_tag="error_text")
            return False
        self.add_code_block_to_gui(code, lang)
        return True

    def _handle_final_answer(self, params):
         """Handles plain text response treated as a final answer."""
         ans = params.get("ans") 
         if ans is None:

             self.add_message_to_gui("AI", "Error: 'final_answer' (implicit) called without content.", style_tag="error_text")
             return False
         self.add_message_to_gui("AI", ans, style_tag="default_text") 

         self.conversation_active = False
         self.waiting_for_user_detail = False
         self.hide_thinking_indicator() 

         if debug_mode: print("DEBUG: Received final_answer. Conversation marked inactive.")
         return True 

    def _handle_none_further(self, params):
        self.conversation_active = False
        self.waiting_for_user_detail = False 
        if debug_mode: print("DEBUG: Received none_further. Conversation marked inactive.")
        self.hide_thinking_indicator() 

        return True 

    def show_thinking_indicator(self):
        """Displays an 'AI is thinking...' message and disables input."""
        if self.is_ai_thinking: return
        self.is_ai_thinking = True
        self.send_button.configure(state="disabled")
        self.input_entry.configure(state="disabled")
        self.set_status_message("⏳ AI is thinking...")
        if debug_mode: print("DEBUG: AI Thinking Indicator: ON")

    def hide_thinking_indicator(self):
        """Removes the 'AI is thinking...' message and potentially re-enables input."""
        if not self.is_ai_thinking: return

        should_enable_input = not self.rate_limit_countdown_timer_id

        if self.waiting_for_user_detail:
            should_enable_input = True

        if self.last_tool_invoked in ["none_further", "final_answer"]:
            should_enable_input = True

        if should_enable_input:
            self.send_button.configure(state="normal")
            self.input_entry.configure(state="normal")

            if not self.rate_limit_countdown_timer_id:
                self.clear_status_message()
            if debug_mode: print("DEBUG: AI Thinking Indicator: OFF, Input ENABLED")
        else:

            if not self.rate_limit_countdown_timer_id:
                 self.clear_status_message() 
            if debug_mode: print("DEBUG: AI Thinking Indicator: OFF, Input KEPT DISABLED (Likely Rate Limit)")

        self.is_ai_thinking = False 

    def send_message_event(self, event=None):
        """Handles the send button click or Enter key press in input."""
        user_input = self.input_entry.get("1.0", tk.END).strip()
        if not user_input or self.is_ai_thinking:
            return

        self.cancel_rate_limit_timers() 

        self.input_entry.delete("1.0", tk.END)
        self.add_message_to_gui("User", user_input) 

        is_first_message = not self.conversation_history

        if self.waiting_for_user_detail:

             if debug_mode: print(f"DEBUG: Handling user response after request_details.")

             self.conversation_history.append({"role": "user", "content": user_input})
             self.waiting_for_user_detail = False 

        elif is_first_message:

            if debug_mode: print("DEBUG: Handling first message of a new chat.")

            system_prompt_content = self._format_system_prompt(user_input)
            if not system_prompt_content:
                self.set_status_message("❌ Error formatting system prompt", 5000)
                return

            api_type = self.settings["api_type"]
            use_system_role = self.settings.get("openai_system_prompt_support", True)

            if api_type in ["OpenAI", "Ollama"] and use_system_role:

                 base_system_prompt = self.system_prompt_template.split("{placeholderQuestion}")[0].strip()
                 self.conversation_history.append({"role": "system", "content": base_system_prompt})
                 self.conversation_history.append({"role": "user", "content": user_input})
                 if debug_mode: print(f"DEBUG: Using dedicated system role.")
            else:

                 self.conversation_history.append({"role": "user", "content": system_prompt_content})
                 if debug_mode: print(f"DEBUG: Sending system prompt embedded in first user message.")

        else:

             if debug_mode: print("DEBUG: Handling subsequent user message.")

             formatted_user_input = user_input

             self.conversation_history.append({"role": "user", "content": formatted_user_input})

        self.expecting_response = True 

        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call_time
        required_delay = self.settings.get("rate_limit_seconds", 1)

        if time_since_last_call < required_delay:
            delay_s = required_delay - time_since_last_call
            delay_ms = int(delay_s * 1000)
            if debug_mode: print(f"DEBUG: Rate limiting: delaying API call by {delay_s:.1f}s")
            self.rate_limit_api_call_timer_id = self.after(delay_ms, self.initiate_api_call)
            self.start_rate_limit_countdown(current_time + delay_s)
            self.send_button.configure(state="disabled")
            self.input_entry.configure(state="disabled")
        else:
            self.initiate_api_call()

    def _format_system_prompt(self, user_question):
        """Formats the system prompt, embedding the user's first question."""
        if not self.system_prompt_template: return None

        if "{placeholderQuestion}" not in self.system_prompt_template:
             print("ERROR: '{placeholderQuestion}' not found in SystemPrompt.txt. Cannot embed first question.")

             return self.system_prompt_template
        return self.system_prompt_template.replace("{placeholderQuestion}", user_question)

    def _format_result_prompt(self, tool_name, success, error_message=None):
        """Formats the result prompt string (to be added as a message)."""
        if not self.result_prompt_template: return None
        if success:
             message = "Successful Tool Use"
        elif error_message:

             message = f"Tool Use Failed: {str(error_message)[:200]}" 
        else:
             message = "Tool Use Failed, Please Try Again" 

        formatted = self.result_prompt_template.replace("Result:", message.strip())

        formatted = formatted.replace("[tool]", f"[{tool_name}]")
        return formatted.strip()

    def _format_user_prompt(self, user_response):
         """Formats a subsequent user message using the user prompt template."""

         if not self.user_prompt_template: return None
         placeholder = "{userResponsePlaceholder}"
         if self.user_prompt_template.count(placeholder) == 1:
              return self.user_prompt_template.replace(placeholder, user_response)
         else:
              print(f"ERROR: Placeholder '{placeholder}' not found or found multiple times in UserPrompt.txt")
              return user_response 

    def start_rate_limit_countdown(self, end_time):
        """Starts the visual countdown in the status bar."""
        if self.rate_limit_countdown_timer_id:
            self.after_cancel(self.rate_limit_countdown_timer_id)
        self._update_rate_limit_status(end_time)

    def _update_rate_limit_status(self, end_time):
        """Updates the rate limit status label every ~100ms."""
        remaining_s = end_time - time.time()

        if remaining_s <= 0:
            self.rate_limit_countdown_timer_id = None
            self.clear_status_message() 

            if not self.is_ai_thinking: 

                 self.hide_thinking_indicator() 
        else:
            self.set_status_message(f"⏳ Rate limit: {remaining_s:.1f}s", is_countdown=True)
            self.rate_limit_countdown_timer_id = self.after(100, lambda: self._update_rate_limit_status(end_time))

    def cancel_rate_limit_timers(self):
        """Cancels both the API call delay timer and the countdown status timer."""
        was_countdown_active = bool(self.rate_limit_countdown_timer_id)

        if self.rate_limit_api_call_timer_id:
            self.after_cancel(self.rate_limit_api_call_timer_id)
            self.rate_limit_api_call_timer_id = None
            if debug_mode: print("DEBUG: Cancelled pending rate-limited API call.")

        if self.rate_limit_countdown_timer_id:
            self.after_cancel(self.rate_limit_countdown_timer_id)
            self.rate_limit_countdown_timer_id = None

            if debug_mode: print("DEBUG: Cancelled rate limit countdown display.")

        if was_countdown_active and not self.is_ai_thinking:

             self.hide_thinking_indicator()

    def initiate_api_call(self):
        """Starts the background thread for the API call using self.conversation_history."""
        self.rate_limit_api_call_timer_id = None
        self.rate_limit_countdown_timer_id = None 
        self.clear_status_message() 

        self.show_thinking_indicator() 

        if not self.conversation_history:
             print("ERROR: Initiate API call requested but conversation_history is empty!")
             self.hide_thinking_indicator() 
             self.set_status_message("❌ Internal Error: No history", 5000)
             return

        self.expecting_response = True

        history_copy = copy.deepcopy(self.conversation_history)

        if debug_mode:
             print("\n--- INITIATING API CALL ---")
             print(f"History Length: {len(history_copy)}")

             for msg in history_copy[-5:]:
                 print(f" - Role: {msg.get('role')}, Content: {str(msg.get('content'))[:100]}{'...' if len(str(msg.get('content')))>100 else ''}")
             print("---------------------------\n")

        if self.current_api_thread and self.current_api_thread.is_alive():
             if debug_mode: print("DEBUG: Previous API thread still running, attempting to ignore its result (new request supersedes).")

        self.current_api_thread = threading.Thread(target=self._get_ai_response_thread, args=(history_copy,), daemon=True)
        self.current_api_thread.start()

    def _send_result_to_ai(self, tool_name, success, error_message=None):
         """ Formats a Result Prompt, adds it to history, and initiates the next API call """
         result_payload_string = self._format_result_prompt(tool_name, success, error_message)
         if not result_payload_string:
              print("ERROR: Failed to format result prompt.")
              self.set_status_message("❌ Error sending result", 5000)
              self.conversation_active = False 
              self.hide_thinking_indicator() 
              return

         self.conversation_history.append({"role": "user", "content": result_payload_string})
         if debug_mode:
              print(f"DEBUG: Appended result message to history (as user): {result_payload_string[:100]}...")

         self.expecting_response = True

         current_time = time.time()
         time_since_last_call = current_time - self.last_api_call_time
         required_delay = self.settings.get("rate_limit_seconds", 1)

         if time_since_last_call < required_delay:
             delay_s = required_delay - time_since_last_call
             delay_ms = int(delay_s * 1000)
             if debug_mode: print(f"DEBUG: Rate limiting result send: delaying API call by {delay_s:.1f}s")
             self.rate_limit_api_call_timer_id = self.after(delay_ms, self.initiate_api_call)
             self.start_rate_limit_countdown(current_time + delay_s)
             self.send_button.configure(state="disabled") 
             self.input_entry.configure(state="disabled")
         else:
             self.initiate_api_call()

    def _get_ai_response_thread(self, current_history):
        """Worker thread function to call the appropriate API with the conversation history."""
        response = None
        raw_response_for_debug = None
        error_message = None
        api_type = self.settings.get("api_type")
        api_key = self.settings.get("api_key")
        model = self.settings.get("model")

        try:
            start_time = time.time()
            if debug_mode: print(f"DEBUG [Thread]: Calling API '{api_type}' with model '{model}'...")

            if api_type == "OpenAI":
                if not OpenAI: raise ImportError("OpenAI library not installed.")
                response, raw_response_for_debug = self._get_openai_response(current_history, api_key, model, self.settings.get("openai_endpoint_url"))
            elif api_type == "Gemini":
                if not genai: raise ImportError("Google Generative AI library not installed.")
                response, raw_response_for_debug = self._get_gemini_response(current_history, api_key, model)
            elif api_type == "Ollama":
                 if not requests: raise ImportError("Requests library not installed.")
                 response, raw_response_for_debug = self._get_ollama_response(current_history, model, self.settings.get("ollama_endpoint_url"))
            else:
                error_message = f"Unsupported API type: {api_type}"

            end_time = time.time()

            if not self.expecting_response:
                 if debug_mode: print(f"DEBUG [Thread]: API call ({api_type}) completed ({end_time - start_time:.2f}s), but response no longer expected. Discarding.")

                 if threading.current_thread() == self.current_api_thread:
                      self.after(0, self.hide_thinking_indicator)
                 return 

            if debug_mode: print(f"DEBUG [Thread]: API call ({api_type}) took {end_time - start_time:.2f} seconds.")

            if debug_mode and (response is not None or raw_response_for_debug is not None):
                 print("\n--- RAW AI RESPONSE ---")
                 print(f"API Type: {api_type}")
                 print(f"Response Content Variable Type: {type(response)}")
                 print(f"Response Content Value:\n{response}")
                 if raw_response_for_debug:
                      print("\n--- RAW API OBJECT/DATA ---")
                      try:

                           if hasattr(raw_response_for_debug, 'model_dump_json'): print(raw_response_for_debug.model_dump_json(indent=2))
                           elif hasattr(raw_response_for_debug, 'to_dict'): print(json.dumps(raw_response_for_debug.to_dict(), indent=2)) 
                           elif hasattr(raw_response_for_debug, 'model_dump'): print(json.dumps(raw_response_for_debug.model_dump(), indent=2))
                           elif isinstance(raw_response_for_debug, dict) or isinstance(raw_response_for_debug, list): print(json.dumps(raw_response_for_debug, indent=2))
                           else: print(raw_response_for_debug)
                      except Exception as dump_err:
                          print(f"(Error during debug dump: {dump_err})")
                          print(raw_response_for_debug) 
                 print("-----------------------\n")

        except ImportError as e:
             error_message = f"Missing library: {e}. Please install it."
             if debug_mode: print(f"\n--- API THREAD IMPORT ERROR ---\n{error_message}\n-----------------------------\n")
        except (APIError, RateLimitError) as e: 
            error_message = f"API Error ({api_type}): {e}"
            if debug_mode: print(f"\n--- API THREAD ERROR ---\n{error_message}\n{traceback.format_exc()}---------------------\n")
        except Exception as e:
            error_message = f"API Error ({api_type}): {e}"
            if debug_mode:
                print(f"\n--- API THREAD ERROR ({api_type}) ---")
                print(f"Error Message: {error_message}")
                traceback.print_exc()
                print("------------------------\n")

        if self.expecting_response and threading.current_thread() == self.current_api_thread:
             self.after(0, self._update_gui_with_response, response, error_message)
        elif self.expecting_response:
             if debug_mode: print("DEBUG [Thread]: API response received, but a newer request is active. Discarding.")
        else:
             if debug_mode: print("DEBUG [Thread]: API response received, but not expecting one. Discarding.")

             if threading.current_thread() == self.current_api_thread:
                  self.after(0, self.hide_thinking_indicator)

        if threading.current_thread() == self.current_api_thread:
             self.current_api_thread = None

    def _update_gui_with_response(self, response_content, error_message):
        """Updates the GUI with the AI response or error (runs in main thread)."""
        if not self.expecting_response:
             if debug_mode: print("DEBUG: Ignoring update GUI request (not expecting).")
             if self.is_ai_thinking: self.hide_thinking_indicator()
             return

        self.last_api_call_time = time.time() 

        original_response_for_debug = response_content 
        if response_content:

             cleaned_response_content = re.sub(r'<thinking>.*?</thinking>', '', response_content, flags=re.DOTALL | re.IGNORECASE).strip()
             if debug_mode and cleaned_response_content != response_content:
                  print(f"DEBUG: Stripped <thinking> tags. Original length: {len(response_content)}, Cleaned length: {len(cleaned_response_content)}")
             response_content = cleaned_response_content 

        if error_message:

            self.hide_thinking_indicator() 
            self.add_message_to_gui("AI", f"API Error: {error_message}", style_tag="error_text")
            self.set_status_message("❌ API Error", 5000)

        elif response_content:

            self.conversation_history.append({"role": "assistant", "content": response_content})
            if debug_mode: print(f"DEBUG: Appended AI response to history: {response_content[:100]}...")

            tool_name, inner_content, format_error = self._extract_tool_call(response_content)

            if format_error:

                 if debug_mode:
                     print(f"DEBUG: AI Response Format Error (after stripping <thinking>): {format_error}")
                     print(f"DEBUG: Cleaned response evaluated: {response_content[:200]}...")

                 self.add_message_to_gui("AI", f"Format Error: AI response was invalid. ({format_error})", style_tag="error_text")
                 self.set_status_message("⏳ AI Format Error, Retrying...", is_countdown=False) 

                 failed_tool_name = self.last_tool_invoked or "format_error"
                 self._send_result_to_ai(failed_tool_name, False, error_message=format_error)

            elif tool_name:

                 if debug_mode: print(f"DEBUG: Handling valid tool/response: {tool_name}")
                 self._handle_tool_response(tool_name, inner_content)
            else:

                 print("ERROR: Unexpected condition in _update_gui_with_response after tool extraction.")
                 self.hide_thinking_indicator()
                 self.add_message_to_gui("AI", "Internal Error: Unexpected response state.", style_tag="error_text")

        else:

             self.hide_thinking_indicator()
             err_msg = "Error: Received an empty response from the API (after removing <thinking> tags)."
             self.add_message_to_gui("AI", err_msg, style_tag="error_text")
             self.set_status_message("⚠️ Empty Response", 5000)
             if debug_mode: print(f"DEBUG: {err_msg} Original response might have only contained <thinking> tags.")

             self.conversation_history.append({"role": "assistant", "content": ""})

    def _get_openai_response(self, messages, api_key, model, base_url=None):
        """Gets response from OpenAI API using conversation history."""
        if not api_key: raise ValueError("OpenAI API Key is missing.")
        if not model: raise ValueError("OpenAI Model name is missing.")
        if not messages: raise ValueError("Messages list cannot be empty.")

        client_args = {"api_key": api_key}
        if base_url: client_args["base_url"] = base_url

        client = OpenAI(**client_args)
        try:

            completion = client.chat.completions.create(model=model, messages=messages)
            content = None
            raw_debug_data = completion 

            if completion.choices and completion.choices[0].message:
                content = completion.choices[0].message.content

            return content, raw_debug_data if debug_mode else None 
        except (APIError, RateLimitError) as e: raise e
        except Exception as e: raise RuntimeError(f"OpenAI request failed: {e}")

    def _convert_to_gemini_history(self, messages):
        """Converts standard message history to Gemini's format."""
        gemini_history = []
        allowed_roles = {"user", "model"} 
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if not content: continue 

            if role == "assistant":
                role = "model"
            elif role == "system":

                 if debug_mode: print("DEBUG (Gemini History): Skipping 'system' role message.")
                 continue
            elif role == "tool":

                 if debug_mode: print("DEBUG (Gemini History): Treating 'tool' role message as 'user'.")
                 role = "user"
            elif role != "user":
                if debug_mode: print(f"DEBUG (Gemini History): Skipping unknown role '{role}'.")
                continue 

            if role in allowed_roles:
                 gemini_history.append({"role": role, "parts": [content]})
            elif role == "user": 
                 gemini_history.append({"role": "user", "parts": [content]})

        return gemini_history

    def _get_gemini_response(self, messages, api_key, model):
         """Gets response from Google Gemini API using conversation history."""
         if not api_key: raise ValueError("Gemini API Key is missing.")
         if not model: raise ValueError("Gemini Model name is missing.")
         if not messages: raise ValueError("Messages list cannot be empty.")

         try: genai.configure(api_key=api_key)
         except Exception as e: raise RuntimeError(f"Failed to configure Gemini API: {e}")

         system_instruction = None
         if messages and messages[0].get("role") == "system":
              system_instruction = messages[0].get("content")

              messages_for_chat = messages[1:]
              if debug_mode: print(f"DEBUG (Gemini): Using system instruction: {system_instruction[:100]}...")
         else:
              messages_for_chat = messages

         gemini_model = genai.GenerativeModel(model_name=model, system_instruction=system_instruction)

         gemini_history = self._convert_to_gemini_history(messages_for_chat[:-1])
         last_user_message = messages_for_chat[-1].get("content")

         if not last_user_message:
              raise ValueError("Last message in history for Gemini call is empty or missing content.")

         try:

             if self._gemini_chat_session is None or self._gemini_chat_session.model != gemini_model:
                 if debug_mode: print("DEBUG (Gemini): Starting new chat session.")
                 self._gemini_chat_session = gemini_model.start_chat(history=gemini_history)
             else:

                  if debug_mode: print("DEBUG (Gemini): Reusing existing chat session.")

             if debug_mode: print(f"DEBUG (Gemini): Sending message: {last_user_message[:100]}...")
             response = self._gemini_chat_session.send_message(last_user_message)

             content = None
             raw_debug_data = response

             if hasattr(response, 'text'): content = response.text
             elif hasattr(response, 'parts'): content = "".join(part.text for part in response.parts if hasattr(part, 'text'))

             return content, raw_debug_data if debug_mode else None
         except Exception as e:
             self._gemini_chat_session = None 
             err_detail = str(e)

             response_obj_for_error = locals().get('response') or getattr(e, 'response', None)
             if response_obj_for_error:
                  try:
                      if hasattr(response_obj_for_error, 'prompt_feedback'):
                           feedback = getattr(response_obj_for_error, 'prompt_feedback', 'N/A')
                           err_detail += f"\nPrompt Feedback: {feedback}"
                      if hasattr(response_obj_for_error, 'candidates') and response_obj_for_error.candidates:
                           finish_reason = getattr(response_obj_for_error.candidates[0], 'finish_reason', 'N/A')
                           err_detail += f"\nFinish Reason: {finish_reason}"
                  except Exception as e_inner:
                      err_detail += f"\n(Could not extract extra error details: {e_inner})"
             raise RuntimeError(f"Gemini API request failed: {err_detail}")

    def _get_ollama_response(self, messages, model, base_url):
        """Gets response from local Ollama API using conversation history."""
        if not model: raise ValueError("Ollama Model name is missing.")
        if not base_url: raise ValueError("Ollama Endpoint URL is missing.")
        if not requests: raise ImportError("Requests library not installed.")
        if not messages: raise ValueError("Messages list cannot be empty.")

        api_url = f"{base_url.rstrip('/')}/api/chat"

        ollama_messages = []
        for msg in messages:
             role = msg.get("role")
             content = msg.get("content")
             if not content and role != "assistant": continue 

             if role == "tool":
                  role = "user" 
                  if debug_mode: print("DEBUG (Ollama): Mapping 'tool' role to 'user'.")

             if role in ["user", "assistant", "system"]:
                  ollama_messages.append({"role": role, "content": content})
             else:
                   if debug_mode: print(f"DEBUG (Ollama): Skipping unknown role '{role}'.")

        payload = {"model": model, "messages": ollama_messages, "stream": False}

        response = None
        try:
            response = requests.post(api_url, json=payload, timeout=120) 
            response.raise_for_status() 
            response_data = response.json()
            raw_debug_data = response_data

            if isinstance(response_data, dict) and response_data.get("message") and \
               isinstance(response_data["message"], dict) and "content" in response_data["message"]:
                content = response_data["message"]["content"]
                return content, raw_debug_data if debug_mode else None
            elif "error" in response_data:

                 raise RuntimeError(f"Ollama API Error: {response_data['error']}")
            else:

                raise RuntimeError(f"Ollama returned an unexpected response format: {str(response_data)[:500]}")

        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Could not connect to Ollama at {api_url}. Is Ollama running?") from e
        except requests.exceptions.Timeout:
             raise RuntimeError(f"Request to Ollama at {api_url} timed out.") from None
        except requests.exceptions.RequestException as e:

            err_msg = f"Ollama request failed: {e}"
            raw_resp_text = ""
            if e.response is not None:
                err_msg += f"\nStatus Code: {e.response.status_code}"
                try:
                    raw_resp_text = e.response.text
                    err_msg += f"\nResponse Body: {raw_resp_text[:500]}"
                    if len(raw_resp_text) > 500: err_msg += "..."
                except Exception: err_msg += "\nResponse Body: <Could not decode>"
            if debug_mode and raw_resp_text: print(f"\n--- OLLAMA FAILED RAW RESPONSE ---\n{raw_resp_text}\n----")
            raise RuntimeError(err_msg) from e
        except json.JSONDecodeError as e:

             err_txt = response.text[:500] if response else "<No Response Object>"
             status = response.status_code if response else 'N/A'
             if debug_mode and response: print(f"\n--- OLLAMA JSON DECODE ERROR (Status: {status}) ---\n{response.text}\n----")
             raise RuntimeError(f"Failed to decode JSON from Ollama. Status: {status}. Text: {err_txt}") from e

    def on_closing(self):
        """Handles window close event."""
        if debug_mode: print("DEBUG: Window closing...")
        self.expecting_response = False 
        self.cancel_rate_limit_timers()

        self.destroy()

if __name__ == "__main__":

    missing_essential = []
    try: import customtkinter
    except ImportError: missing_essential.append("customtkinter")
    try: from PIL import Image, ImageTk
    except ImportError: missing_essential.append("Pillow")

    if missing_essential:
        error_message = f"Could not start AnswerBot.\nMissing essential libraries: {', '.join(missing_essential)}\nPlease install them (e.g., 'pip install customtkinter Pillow') and try again."
        print(f"ERROR: {error_message}")
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Missing Libraries", error_message); root.destroy()
        except Exception as e: print(f"(Could not show graphical error: {e})")
        exit(1)

    missing_prompts = []
    if not os.path.exists(SYSTEM_PROMPT_FILE): missing_prompts.append(SYSTEM_PROMPT_FILE)
    if not os.path.exists(RESULT_PROMPT_FILE): missing_prompts.append(RESULT_PROMPT_FILE)
    if not os.path.exists(USER_PROMPT_FILE): missing_prompts.append(USER_PROMPT_FILE)

    if missing_prompts:
        error_message = f"Could not start AnswerBot.\nMissing prompt files: {', '.join(missing_prompts)}\nPlease ensure they exist in the same directory as the script."
        print(f"ERROR: {error_message}")
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Missing Files", error_message); root.destroy()
        except Exception as e: print(f"(Could not show graphical error: {e})")
        exit(1)

    if not genai: print("INFO: 'google-generativeai' not installed. Gemini API unavailable.")
    if not OpenAI: print("INFO: 'openai' not installed. OpenAI API unavailable.")
    if not requests: print("INFO: 'requests' not installed. Ollama API unavailable.")

    app = AnswerBotApp()
    if app.winfo_exists(): 
        app.mainloop()