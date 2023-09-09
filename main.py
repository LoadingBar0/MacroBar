from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.dropdown import DropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from pynput import mouse, keyboard

import pydirectinput

from os import environ, path, getcwd


# Set the window size and prevent resizing
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'fullscreen', '0')
environ["KIVY_NO_ENV_CONFIG"] = "1"

class EditPopup(Popup):
    def __init__(self, initial_text, **kwargs):
        super().__init__(title="File Editor", **kwargs)
        self.initial_text = initial_text
        self.text_input = TextInput(text=initial_text, multiline=True)

        content_layout = BoxLayout(orientation='vertical')
        content_layout.add_widget(self.text_input)

        self.save_button = Button(text="Save", size_hint_y=None, height=30)
        self.save_button.bind(on_release=self.save_text)

        content_layout.add_widget(self.save_button)

        self.content = content_layout

    def save_text(self, instance):
        edited_text = self.text_input.text
        self.dismiss()
        if hasattr(self, 'callback'):
            self.callback(edited_text)

class ReaderPopup(Popup):
    def __init__(self, initial_text, **kwargs):
        super().__init__(title="FIle Reader", **kwargs)
        self.initial_text = initial_text
        self.text_input = TextInput(text=initial_text, multiline=True, readonly=True)

        content_layout = BoxLayout(orientation='vertical')
        content_layout.add_widget(self.text_input)

        self.close_button = Button(text="close", size_hint_y=None, height=30)
        self.close_button.bind(on_release=self.dismiss)

        content_layout.add_widget(self.close_button)

        self.content = content_layout

class WhiteWindow(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas:
            # Set the background color to white
            Color(1, 1, 1, 1)  # RGBA values (1, 1, 1, 1) represent white
            self.rect = Rectangle(pos=self.pos, size=self.size)

        # Keep track of pressed keys
        self.pressed_keys = set()

        self.is_waiting_to_start_recording = False  # Track if waiting for the delay
        self.delayed_start_event = None

        # Update the background when the widget's size changes
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Add a label with "Macro Bar" in the lower middle
        self.label = Label(text="Macro Bar", font_size='120sp', color=(0, 0, 0, 1))
        self.add_widget(self.label)  # Add the label to the widget's layout
        
        # Add a "record button" below the label
        self.record_button = Button(text="Start Recording", size_hint=(None, None), size=(200, 50),
                             pos=(self.width / 2 - 100, 400))
        self.add_widget(self.record_button)  # Add the button to the widget's layout

        self.recorded_events_input = TextInput(size_hint=(1, None), height=300, multiline=True, readonly=True,
                                               pos=(0, 0), background_color=(1, 1, 1, 1))
        self.add_widget(self.recorded_events_input)
        
        # Add a "Replay Inputs" button next to the Start button
        self.replay_button = Button(text="Replay Inputs", size_hint=(None, None), size=(200, 50),
                                    pos=(self.width / 2 + 100, 400))
        self.add_widget(self.replay_button)  # Add the replay button to the widget's layout

        # Add a "Clear" button below the "Replay Inputs" button
        self.clear_button = Button(text="Clear", size_hint=(None, None), size=(200, 50),
                                   pos=(self.width / 2 + 350, 400))  # Adjusted Y position
        self.add_widget(self.clear_button)  # Add the clear button to the widget's layout
        self.clear_button.bind(on_press=self.clear_recorded_events)
        
        # Create a TextInput for recorded events
        self.recorded_events_input = TextInput(size_hint=(1, None), height=300, multiline=True, readonly=True,
                                               pos=(0, 0), background_color=(1, 1, 1, 1))
        self.add_widget(self.recorded_events_input)

        # Load recorded events from file
        self.load_recorded_events()

        # Create a horizontal layout for the menu bar
        self.menu_bar = BoxLayout(orientation="horizontal", size_hint=(1, None), height=30)

        # Create menu buttons and add them to the menu bar
        self.file_button = Button(text="File", size_hint_x=None, width=100)
        self.help_button = Button(text="Help", size_hint_x=None, width=100)
        
        self.menu_bar.add_widget(self.file_button)
        self.menu_bar.add_widget(self.help_button)

        # Bind menu button clicks to their respective actions
        self.file_button.bind(on_release=self.show_file_menu)
        self.help_button.bind(on_release=self.show_help_menu)
        
        # Position the menu layout at the top
        self.menu_bar.pos = (0, 720)

        self.add_widget(self.menu_bar)

        self.keyboard_listener = None
        self.mouse_listener = None
        self.is_recording = False
        self.is_initial_click = True  # Flag to track the initial button click
        self.last_event_time = None  # For tracking time between inputs

        self.record_button.bind(on_press=self.toggle_recording)
        self.replay_button.bind(on_press=self.replay_events)

    def show_file_menu(self, instance):
        # Create a drop-down for the File menu
        dropdown = DropDown()

        # Create menu items and add them to the drop-down
        edit_file = Button(text="Edit File", size_hint_y=None, height=30, on_release=self.open_edit_popup)
        new_item = Button(text="New", size_hint_y=None, height=30)
        open_item = Button(text="Open", size_hint_y=None, height=30)
        save_item = Button(text="Save", size_hint_y=None, height=30)
        save_as_item = Button(text="Save As", size_hint_y=None, height=30)

        dropdown.add_widget(edit_file)
        dropdown.add_widget(new_item)
        dropdown.add_widget(open_item)
        dropdown.add_widget(save_item)
        dropdown.add_widget(save_as_item)

        # Open the drop-down below the "File" button
        dropdown.open(self.file_button) 

    def show_help_menu(self, instance):
        # Create a drop-down for the File menu
        dropdown = DropDown()

        # Create menu items and add them to the drop-down
        about_item = Button(text="About", size_hint_y=None, height=30, on_release=self.open_readme)
        help_item = Button(text="Help", size_hint_y=None, height=30)

        dropdown.add_widget(about_item)
        dropdown.add_widget(help_item)

        # Open the drop-down below the "Help" button
        dropdown.open(self.help_button)

    def open_readme(self, instance):
        readme_file = "README.txt"
        # try:
        with open(readme_file, "r") as file:
            readme_popup_text = file.read()
            readme_popup = ReaderPopup(readme_popup_text)
            readme_popup.open()
        # except Exception as e:
            # print("Readme file not found")
    
    def open_edit_popup(self, instance):
        edit_popup = EditPopup(self.recorded_events_input.text)
        edit_popup.callback = self.save_edited_text  # Assign the callback
        edit_popup.open()
    
    def save_edited_text(self, edited_text):
        self.recorded_events_input.text = edited_text
        self.save_recorded_events()  # Save the edited text to file

    def load_recorded_events(self):
        try:
            with open("Recording.txt", "r") as file:
                self.recorded_events_input.text = file.read()
        except Exception as e:
            pass

    def toggle_recording(self, instance):
        if self.is_recording:
            self.is_recording = False
            self.keyboard_listener.stop()
            self.mouse_listener.stop()
            self.record_button.text = "Start Recording"
            self.save_recorded_events()
        else:
            self.is_recording = True
            if self.is_initial_click:
                self.recorded_events_input.text = ""  # Clear recorded events on new recording
                self.is_initial_click = False  # Set the flag to False
            self.record_button.text = "Stop Recording"
            self.start_listening()

    def save_recorded_events(self):
        try:
            with open("Recording.txt", "w") as file:
                self.clear_saved_recorded_events()
                file.write(self.recorded_events_input.text)
        except Exception as e:
            self.recorded_events_input.text += f"\nError saving to Recording.txt: {str(e)}\n"

    def clear_saved_recorded_events(self):
        if path.exists("Recording.txt"):
            with open("Recording.txt", "w") as file:
                file.write("")

    def clear_recorded_events(self, instance):
        self.clear_saved_recorded_events()
        self.recorded_events_input.text = ""

    def start_listening(self):
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.keyboard_listener.start()

        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_event)
        self.mouse_listener.start()

    def on_keyboard_event(self, key, is_press):
        if self.is_recording:
            current_time = Clock.get_time()
            if self.last_event_time is not None:
                time_difference = (current_time - self.last_event_time) * 100
                time_message = f"Delay: {time_difference:.2f} ms\n"
                Clock.schedule_once(lambda dt: self.update_recorded_events(time_message))
            self.last_event_time = current_time

            action = "pressed" if is_press else "released"
            Clock.schedule_once(lambda dt: self.update_recorded_events(f"Key {action}: {key}\n"))

    def on_key_press(self, key):
        if key not in self.pressed_keys:
            self.pressed_keys.add(key)
            self.on_keyboard_event(key, True)

    def on_key_release(self, key):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
            self.on_keyboard_event(key, False)

    def on_mouse_event(self, x, y, button, pressed):
        if self.is_recording and not self.is_initial_click:
            current_time = Clock.get_time()
            if self.last_event_time is not None:
                time_difference = (current_time - self.last_event_time) * 100
                time_message = f"Delay: {time_difference:.2f} ms\n"
                Clock.schedule_once(lambda dt: self.update_recorded_events(time_message))
            self.last_event_time = current_time

            action = "pressed" if pressed else "released"
            Clock.schedule_once(lambda dt: self.update_recorded_events(f"Mouse {action}: {button} at ({x}, {y})\n"))

    def update_recorded_events(self, event_text):
        self.recorded_events_input.text += event_text

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.label.pos = (self.width / 2 - self.label.texture_size[0] / 2 - 50, 500)  # Adjust the X or Y
        self.record_button.pos = (self.width / 2 - 300, 400)  # Adjust the X or Y position of the button
        self.replay_button.pos = (self.width / 2 + 100, 400)  # Adjust the X or Y position of the replay button
        self.recorded_events_input.size = (self.width, 300)
        self.recorded_events_input.pos = (0, 0)
            
    def map_mouse_button(self, button_name):
        if button_name == "Button.left":
            return "left"
        elif button_name == "Button.middle":
            return "middle"
        elif button_name == "Button.right":
            return "right"
        else:
            # Handle unrecognized button names here
            return None
    
    def replay_events(self, instance):
        events = self.recorded_events_input.text.splitlines()

        def replay_next_event(dt):
            if events:
                event = events.pop(0)
                parts = event.split(":")
                if len(parts) >= 2:  # Make sure there are enough parts
                    action, key_name = parts[0].strip(), parts[1].strip()
                    if action == "Delay":
                        delay_time = float(parts[1].split()[0]) / 100  # Extract delay time
                        Clock.schedule_once(replay_next_event, delay_time)  # Schedule the next event with the recorded delay
                    if "Key pressed" in event or "Key released" in event:
                        if "pressed" in action:
                            pydirectinput.keyDown(key_name)
                        elif "released" in action:
                            pydirectinput.keyUp(key_name)
                    elif "Mouse pressed" in event or "Mouse released" in event:
                        action, rest = event.split(":", 1)  # Split at the first colon
                        button_name, coordinates = rest.split("at")
                        if "pressed" in action:
                            button = self.map_mouse_button(button_name.strip())
                            if button:
                                x, y = [int(coord.strip()) for coord in coordinates.split("(")[-1].split(")")[0].split(",")]
                                pydirectinput.moveTo(x, y)
                                pydirectinput.mouseDown(button=button)
                        elif "released" in action:
                            button = self.map_mouse_button(button_name.strip())
                            if button:
                                x, y = [int(coord.strip()) for coord in coordinates.split("(")[-1].split(")")[0].split(",")]
                                pydirectinput.moveTo(x, y)
                                pydirectinput.mouseUp(button=button)
                Clock.schedule_once(replay_next_event, 0.1)  # Schedule the next event with a delay

        if events:
            replay_next_event(0)  # Start replaying events

class MyApp(App):
    def build(self):
        self.title = 'Macro Bar'  # Set the title of the window
        return WhiteWindow()


if __name__ == '__main__':
    MyApp().run()
