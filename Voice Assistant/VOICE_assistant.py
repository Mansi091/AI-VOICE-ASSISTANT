import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import wikipedia
import webbrowser
import time
import re
import math
from pygame import mixer
import tkinter as tk
from tkinter import scrolledtext, ttk, PhotoImage, font
import threading
import os
from bs4 import BeautifulSoup
import requests
import urllib.parse
from PIL import Image, ImageTk, ImageDraw
import io
import base64
import json
from datetime import datetime

Gemini_Api_key = "your-api-key"  
genai.configure(api_key=Gemini_Api_key)

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 190)

voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
# Initialize pygame mixer for music playback
mixer.init()

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg='#1a1a2e', width=200, height=100, radius=20, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self._bg = bg
        self._radius = radius
        self.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        self.create_rounded_rect()

    def create_rounded_rect(self):
        self.delete('all')
        width = self.winfo_width()
        height = self.winfo_height()
        self.create_rounded_rectangle(0, 0, width, height, self._radius, fill=self._bg)

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

class ModernButton(tk.Canvas):
    def __init__(self, parent, text="", command=None, width=120, height=40, bg='#4CAF50', fg='white', font=None):
        super().__init__(parent, width=width, height=height, bg='#1a1a2e', highlightthickness=0)
        self._bg = bg
        self._fg = fg
        self._command = command
        self._text = text
        self._font = font or ('Helvetica', 11)
        self._width = width
        self._height = height
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<ButtonRelease-1>', self._on_release)
        
        self._draw()

    def _draw(self, state='normal'):
        self.delete('all')
        colors = {
            'normal': self._bg,
            'hover': self._lighten_color(self._bg, 0.1),
            'pressed': self._darken_color(self._bg, 0.1)
        }
        bg_color = colors[state]
        
        # Create rounded rectangle
        self.create_rounded_rectangle(2, 2, self._width-2, self._height-2, 10, fill=bg_color)
        
        # Add text
        self.create_text(self._width/2, self._height/2, text=self._text, fill=self._fg, font=self._font)

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _lighten_color(self, color, factor=0.1):
        # Convert hex to RGB
        rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        # Lighten
        rgb = tuple(min(255, int(c * (1 + factor))) for c in rgb)
        # Convert back to hex
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def _darken_color(self, color, factor=0.1):
        # Convert hex to RGB
        rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        # Darken
        rgb = tuple(max(0, int(c * (1 - factor))) for c in rgb)
        # Convert back to hex
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def _on_enter(self, e):
        self._draw('hover')

    def _on_leave(self, e):
        self._draw('normal')

    def _on_click(self, e):
        self._draw('pressed')

    def _on_release(self, e):
        self._draw('normal')
        if self._command:
            self._command()

class ModernAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Voice Assistant")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Configure full screen
        self.root.state('zoomed')
        self.root.configure(bg='#0a0a1a')
        
        # container size 
        container_width = int(screen_width * 0.98)
        container_height = int(screen_height * 0.95)
        
        # Configure custom fonts
        self.title_font = font.Font(family="Helvetica", size=36, weight="bold")
        self.text_font = font.Font(family="Helvetica", size=14)
        self.button_font = font.Font(family="Helvetica", size=14, weight="bold")
        
        # Color scheme
        self.colors = {
            'bg_dark': '#0a0a1a',
            'bg_light': '#1a1a2e',
            'accent_primary': '#4CAF50',
            'accent_secondary': '#2196F3',
            'text_primary': '#ffffff',
            'text_secondary': '#b3b3b3',
            'error': '#f44336',
            'success': '#4CAF50',
            'warning': '#FFA500'
        }
        
        # main container with padding
        self.main_container = RoundedFrame(self.root, bg=self.colors['bg_light'], width=container_width, height=container_height)
        self.main_container.place(relx=0.5, rely=0.5, anchor='center')
        
        # content frame
        self.content_frame = tk.Frame(self.main_container, bg=self.colors['bg_light'])
        self.content_frame.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)
        
        # UI elements
        self.create_header()
        self.create_chat_area()
        self.create_control_panel()
        
        # state
        self.is_running = False
        self.assistant_thread = None
        self.is_activated = False
        
        # weather API
        self.weather_api_key = "2276ffde0dfcf8905d1bb4a28d5ccafc"
        self.default_city = "Pune"

    def create_header(self):
        header_frame = tk.Frame(self.content_frame, bg=self.colors['bg_light'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_canvas = tk.Canvas(header_frame, height=120, bg=self.colors['bg_light'], highlightthickness=0)
        title_canvas.pack(fill=tk.X)
        
        # Create gradient background
        for i in range(120):
            color = '#{:02x}{:02x}{:02x}'.format(
                10 + int(i/120 * 20),
                10 + int(i/120 * 20),
                26 + int(i/120 * 20)
            )
            title_canvas.create_line(0, i, title_canvas.winfo_width(), i, fill=color)
        
        # Add animated robot emoji
        self.robot_emoji = title_canvas.create_text(40, 60, text="🤖", font=('Helvetica', 54), fill=self.colors['accent_primary'], anchor='w')
        self.animate_robot(title_canvas)
        
        # Create main title with gradient effect
        title_text = "AI VOICE ASSISTANT"
        title_canvas.create_text(
            135, 
            60, 
            text=title_text, 
            font=('Helvetica', 42, 'bold'), 
            fill=self.colors['accent_primary'], 
            anchor='w'
        )
        
        # Add decorative line with gradient
        for i in range(100):
            color = '#{:02x}{:02x}{:02x}'.format(
                33 + int(i/100 * 150),
                150 + int(i/100 * 105),
                243 + int(i/100 * 12)
            )
            title_canvas.create_line(
                40 + i, 100, 40 + i, 100,
                fill=color,
                width=2
            )

    def animate_robot(self, canvas):
        def update_animation():
            current_text = canvas.itemcget(self.robot_emoji, 'text')
            if current_text == "🤖":
                canvas.itemconfig(self.robot_emoji, text="🤖")
            else:
                canvas.itemconfig(self.robot_emoji, text="🤖")
            self.root.after(1000, update_animation)
        
        update_animation()

    def create_chat_area(self):
        # Create chat frame with rounded corners and gradient
        chat_frame = RoundedFrame(self.content_frame, bg=self.colors['bg_dark'])
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create chat display with custom styling
        self.output_area = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('Helvetica', 14),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.colors['accent_secondary'],
            selectbackground=self.colors['accent_secondary'],
            selectforeground=self.colors['text_primary'],
            padx=20,
            pady=20
        )
        self.output_area.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)
        
        # Configure tags for different message types with custom styling
        self.output_area.tag_configure('assistant', 
            foreground=self.colors['accent_primary'], 
            font=('Helvetica', 14),
            spacing1=10,
            spacing3=10
        )
        self.output_area.tag_configure('user', 
            foreground=self.colors['accent_secondary'], 
            font=('Helvetica', 14),
            spacing1=10,
            spacing3=10
        )
        self.output_area.tag_configure('system', 
            foreground=self.colors['warning'], 
            font=('Helvetica', 14),
            spacing1=10,
            spacing3=10
        )

    def create_control_panel(self):
        # Create bottom panel for controls with gradient
        control_panel = tk.Frame(self.content_frame, bg=self.colors['bg_light'])
        control_panel.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        # Create status bar with modern styling
        self.status_label = tk.Label(
            control_panel,
            text="Status: Ready",
            font=('Helvetica', 14, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['accent_primary'],
            pady=10
        )
        self.status_label.pack(pady=(0, 20))
        
        # Create button frame
        button_frame = tk.Frame(control_panel, bg=self.colors['bg_light'])
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create modern buttons with hover effects
        self.start_button = ModernButton(
            button_frame,
            text="🎤 Start Listening",
            command=self.start_assistant,
            bg=self.colors['accent_primary'],
            fg=self.colors['text_primary'],
            width=300,
            height=60,
            font=('Helvetica', 14, 'bold')
        )
        self.start_button.pack(side=tk.LEFT, padx=20, expand=True)
        
        self.stop_button = ModernButton(
            button_frame,
            text="⏹ Stop",
            command=self.stop_assistant,
            bg=self.colors['error'],
            fg=self.colors['text_primary'],
            width=300,
            height=60,
            font=('Helvetica', 14, 'bold')
        )
        self.stop_button.pack(side=tk.LEFT, padx=20, expand=True)
        
        self.clear_button = ModernButton(
            button_frame,
            text="🗑 Clear Chat",
            command=self.clear_output,
            bg=self.colors['accent_secondary'],
            fg=self.colors['text_primary'],
            width=300,
            height=60,
            font=('Helvetica', 14, 'bold')
        )
        self.clear_button.pack(side=tk.LEFT, padx=20, expand=True)

        # Create input area with modern styling
        input_frame = RoundedFrame(control_panel, bg=self.colors['bg_dark'], height=80)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create text input with modern styling
        self.text_input = tk.Entry(
            input_frame,
            font=('Helvetica', 16),
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            borderwidth=1,
            highlightthickness=2,
            highlightbackground=self.colors['accent_secondary'],
            highlightcolor=self.colors['accent_secondary'],
            relief='flat'
        )
        self.text_input.place(relx=0.02, rely=0.5, relwidth=0.85, relheight=0.7, anchor='w')
        
        # Add placeholder text with modern styling
        self.text_input.insert(0, "Type your message here or use voice commands")
        self.text_input.config(fg=self.colors['text_secondary'])
        
        # Bind focus events
        self.text_input.bind("<FocusIn>", self.on_entry_click)
        self.text_input.bind("<FocusOut>", self.on_focus_out)
        
        # Create send button with modern styling
        self.send_button = ModernButton(
            input_frame,
            text="📤 Send",
            command=self.handle_text_input,
            bg=self.colors['accent_primary'],
            fg=self.colors['text_primary'],
            width=150,
            height=50,
            font=('Helvetica', 14, 'bold')
        )
        self.send_button.place(relx=0.98, rely=0.5, anchor='e')
        
        # Bind Enter key
        self.text_input.bind("<Return>", lambda e: self.handle_text_input())

    def write_to_output(self, text, tag='system'):
        timestamp = time.strftime("%H:%M:%S")
        self.output_area.insert(tk.END, f"[{timestamp}] ", 'system')
        self.output_area.insert(tk.END, f"{text}\n", tag)
        self.output_area.see(tk.END)
        
        # Add subtle animation when new message appears
        self.output_area.after(10, lambda: self.output_area.yview_moveto(1.0))
        
    def update_status(self, text, is_listening=False):
        color = self.colors['accent_primary'] if is_listening else self.colors['warning']
        self.status_label.configure(foreground=color, text=f"Status: {text}")
        
        # Add subtle animation to status update
        self.status_label.configure(font=('Helvetica', 14, 'bold'))
        self.root.after(100, lambda: self.status_label.configure(font=('Helvetica', 14)))

    def clear_output(self):
        self.output_area.delete(1.0, tk.END)
        self.write_to_output("Chat cleared. Ready to start new conversation.", 'system')

    def on_entry_click(self, event):
        if self.text_input.get() == "Type your message here or use voice commands":
            self.text_input.delete(0, tk.END)
            self.text_input.config(fg='#ffffff')

    def on_focus_out(self, event):
        if self.text_input.get() == '':
            self.text_input.insert(0, "Type your message here or use voice commands")
            self.text_input.config(fg='#888888')

    def handle_text_input(self):
        text = self.text_input.get().strip()
        if not text or text == "Type your message here or use voice commands":
            self.write_to_output("❌ Please enter a valid command.", 'system')
            return
            
        self.write_to_output(f"You: {text}", 'user')
        self.text_input.delete(0, tk.END)
        
        # Process the command
        if not self.handle_command(text) and not self.is_activated:
            self.write_to_output("Tip: Say 'Hey Assistant' first to activate me.", 'system')

    def start_assistant(self):
        if not self.is_running:
            self.is_running = True
            self.assistant_thread = threading.Thread(target=self.run_assistant)
            self.assistant_thread.daemon = True
            self.assistant_thread.start()
            self.update_status("Listening", True)

    def stop_assistant(self):
        self.is_running = False
        self.is_activated = False  # Reset activation state when stopping
        self.update_status("Stopped")

    def run_assistant(self):
        self.gui_speak("Hey! I'm your voice assistant. Say 'Hey Assistant' to activate me.")
        
        while self.is_running:
            command = self.listen()
            if command:
                if "hey assistant" in command:
                    self.activate_assistant()
                    while self.is_running and self.is_activated:
                        command = self.listen()
                        if command:
                            if "stop" in command:
                                self.deactivate_assistant()
                                break
                            self.handle_command(command)
                        else:
                            self.gui_speak("I didn't catch that. Try again.")

    def activate_assistant(self):
        self.is_activated = True
        self.gui_speak("Yes, how can I help?")
        # Cancel previous timer if exists
        if hasattr(self, '_deactivate_timer'):
            self.root.after_cancel(self._deactivate_timer)
        # Set new 60-second timer
        self._deactivate_timer = self.root.after(60000, self.deactivate_assistant)
    
    def deactivate_assistant(self):
        self.is_activated = False
        self.gui_speak("I'm going to sleep now. Say 'Hey Assistant' when you need me.")

    def gui_speak(self, text):
        self.write_to_output(f"Assistant: {text}", 'assistant')
        engine.say(text)
        engine.runAndWait()

    def listen(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise with a shorter duration
                self.write_to_output("🎤 Adjusting for ambient noise...", 'system')
                recognizer.adjust_for_ambient_noise(source, duration=0.2)  # Reduced to 0.2 seconds
                
                # Set dynamic energy threshold with lower sensitivity
                recognizer.dynamic_energy_threshold = True
                recognizer.energy_threshold = 2500  # Reduced to 2500 for better sensitivity
                
                self.update_status("Listening for command...", True)
                self.write_to_output("🎤 Listening...", 'system')
                
                try:
                    # Adjust timeouts for better responsiveness
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=2)  # Reduced to 2 seconds
                    self.write_to_output("🎤 Processing speech...", 'system')
                    
                    # Try multiple recognition services with better error handling
                    try:
                        user_input = recognizer.recognize_google(audio, language="en-US").lower()
                    except sr.UnknownValueError:
                        try:
                            user_input = recognizer.recognize_sphinx(audio).lower()
                        except:
                            self.write_to_output("❌ Could not understand audio.", 'system')
                            self.update_status("Ready")
                            return ""
                    
                    if user_input.strip():  # Only return if we got actual text
                        self.write_to_output(f"You: {user_input}", 'user')
                        return user_input
                    else:
                        self.write_to_output("❌ No speech detected.", 'system')
                        self.update_status("Ready")
                        return ""
                    
                except sr.WaitTimeoutError:
                    self.write_to_output("❌ No speech detected within timeout period.", 'system')
                    self.update_status("Ready")
                    return ""
                    
                except sr.RequestError as e:
                    self.write_to_output(f"❌ Could not request results from speech recognition service: {str(e)}", 'system')
                    self.update_status("Error")
                    return ""
                    
        except Exception as e:
            self.write_to_output(f"❌ Error accessing microphone: {str(e)}", 'system')
            self.update_status("Error")
            return ""

    def handle_command(self, command):
        command = command.lower().strip()
        
        if any(word in command for word in ["stop", "exit", "bye", "goodbye", "quit"]):
            self.gui_speak("Goodbye! Have a great day!")
            self.stop_assistant()
            return True
            
        # First check for activation phrase
        if "hey assistant" in command:
            self.activate_assistant()
            return True
            
        # Check if assistant is activated
        if not self.is_activated:
            self.gui_speak("Please say 'Hey Assistant' to activate me.")
            return False
            
        # Then process other commands
        if any(word in command for word in ["map", "maps", "direction", "directions", "navigate", "location", "where is"]):
            self.handle_maps_command(command)
            return True
            
        elif "time" in command:
            self.gui_speak("The current time is " + time.strftime("%I:%M %p"))
            return True
            
        elif "date" in command or "today" in command or "day is it" in command:
            today = datetime.now().strftime("%A, %B %d, %Y")
            self.gui_speak(f"Today's date is {today}")
            return True
            
        elif any(phrase in command for phrase in ["play", "open"]) and "youtube" in command:
            query = command.lower()
            query = query.replace("play", "").replace("open", "").replace("on youtube", "").replace("youtube", "").replace("from", "")
            query = query.strip()
            
            if query:
                self.gui_speak(f"Opening YouTube video: {query}")
                self.play_youtube_video(query)
            else:
                self.gui_speak("Opening YouTube homepage.")
                webbrowser.open("https://www.youtube.com")
            return True

        elif "search wikipedia for" in command or "wikipedia for" in command:
            query = command.replace("search wikipedia for", "").replace("wikipedia for", "").strip()
            if query:
                try:
                    self.gui_speak(f"Searching Wikipedia for {query}...")
                    result = wikipedia.summary(query, sentences=2)
                    self.gui_speak(result)
                except wikipedia.exceptions.DisambiguationError as e:
                    self.gui_speak(f"Found multiple results for {query}. Please be more specific.")
                except wikipedia.exceptions.PageError:
                    self.gui_speak(f"Sorry, couldn't find any Wikipedia article about {query}")
                except Exception as e:
                    self.gui_speak(f"Sorry, there was an error searching Wikipedia: {str(e)}")
            else:
                self.gui_speak("What would you like to search for on Wikipedia?")
            return True

        elif any(phrase in command for phrase in ["cricket score", "live score", "ipl score"]):
            try:
                self.gui_speak("Let me check the live cricket scores...")
                webbrowser.open("https://www.cricbuzz.com/cricket-match/live-scores")
                self.gui_speak("I've opened Cricbuzz with live cricket scores for you.")
            except Exception as e:
                self.gui_speak(f"Sorry, I couldn't fetch the cricket scores. Error: {str(e)}")
            return True

        elif "google" in command:
            query = command.replace("google", "").replace("search", "").replace("for", "").strip()
            if query:
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                webbrowser.open(search_url)
                self.gui_speak(f"Here are the Google search results for {query}")
            else:
                webbrowser.open("https://www.google.com")
                self.gui_speak("Opening Google homepage")
            return True

        elif "stop" in command or "exit" in command or "bye" in command:
            self.gui_speak("Goodbye! Have a great day!")
            self.stop_assistant()
            return False

        elif "weather" in command:
            city = None
            # Clean up the command to extract city name
            command = command.replace("weather", "").replace("forecast", "").strip()
            
            # Try different ways to extract city name
            if "in" in command:
                city = command.split("in")[-1].strip()
            elif "for" in command:
                city = command.split("for")[-1].strip()
            elif "at" in command:
                city = command.split("at")[-1].strip()
            else:
                # If no preposition found, take the last part of the command
                city = command.split()[-1].strip()
            
            # Remove common words that might be mistaken for city names
            city = city.replace("now", "").replace("today", "").replace("tomorrow", "").strip()
            
            if not city:
                city = self.default_city
            
            self.write_to_output(f"Fetching weather for {city}...", 'system')
                
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": self.weather_api_key,
                "units": "metric"
            }
            
            try:
                response = requests.get(base_url, params=params)
                
                if response.status_code == 401:
                    error_msg = "API key validation failed. Please check your OpenWeatherMap API key."
                    self.write_to_output(f"Error: {error_msg}", 'system')
                    self.gui_speak(error_msg)
                    return
                    
                elif response.status_code == 404:
                    error_msg = f"City '{city}' not found. Please check the city name and try again."
                    self.write_to_output(f"Error: {error_msg}", 'system')
                    self.gui_speak(error_msg)
                    return
                    
                elif response.status_code != 200:
                    error_msg = f"API Error: Status code {response.status_code}"
                    self.write_to_output(f"Error: {error_msg}", 'system')
                    self.gui_speak("Sorry, I couldn't fetch the weather information at the moment.")
                    return
                
                data = response.json()
                
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                pressure = data["main"]["pressure"]
                desc = data["weather"][0]["description"]
                wind_speed = data["wind"]["speed"]
                wind_direction = data["wind"]["deg"]
                clouds = data["clouds"]["all"]
                
                sunrise = datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%I:%M %p")
                sunset = datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%I:%M %p")
                
                def get_wind_direction(degrees):
                    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
                    index = round(degrees / (360 / len(directions))) % len(directions)
                    return directions[index]
                
                wind_cardinal = get_wind_direction(wind_direction)
                
                lat, lon = data["coord"]["lat"], data["coord"]["lon"]
                air_quality_url = "http://api.openweathermap.org/data/2.5/air_pollution"
                air_params = {
                    "lat": lat,
                    "lon": lon,
                    "appid": self.weather_api_key
                }
                
                air_response = requests.get(air_quality_url, params=air_params)
                air_quality = "Unknown"
                if air_response.status_code == 200:
                    aqi_data = air_response.json()
                    aqi = aqi_data["list"][0]["main"]["aqi"]
                    aqi_labels = {
                        1: "Good",
                        2: "Fair",
                        3: "Moderate",
                        4: "Poor",
                        5: "Very Poor"
                    }
                    air_quality = aqi_labels.get(aqi, "Unknown")
                
                forecast_url = "http://api.openweathermap.org/data/2.5/forecast"
                forecast_params = {
                    "q": city,
                    "appid": self.weather_api_key,
                    "units": "metric",
                    "cnt": 3
                }
                
                forecast_response = requests.get(forecast_url, params=forecast_params)
                forecast_info = "\n\nUpcoming Weather:"
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                    for item in forecast_data["list"]:
                        forecast_time = datetime.fromtimestamp(item["dt"]).strftime("%I:%M %p")
                        temp_forecast = item["main"]["temp"]
                        desc_forecast = item["weather"][0]["description"]
                        forecast_info += f"\n{forecast_time}: {temp_forecast:.1f}°C, {desc_forecast.capitalize()}"
                
                weather_info = (
                    f"📍 Weather in {city.title()}:\n"
                    f"🌡 Temperature: {temp:.1f}°C (Feels like: {feels_like:.1f}°C)\n"
                    f"💧 Humidity: {humidity}%\n"
                    f"🌪 Wind: {wind_speed} m/s {wind_cardinal}\n"
                    f"☁ Cloud Cover: {clouds}%\n"
                    f"🌅 Sunrise: {sunrise}\n"
                    f"🌇 Sunset: {sunset}\n"
                    f"🌍 Air Quality: {air_quality}\n"
                    f"🌡 Pressure: {pressure} hPa\n"
                    f"🌤 Conditions: {desc.capitalize()}"
                    f"{forecast_info}"
                )
                
                self.write_to_output(f"Assistant: {weather_info}", 'assistant')
                self.gui_speak(f"Here's the weather in {city}. Temperature is {temp:.1f}°C with {desc}. Air quality is {air_quality}.")
                
            except requests.exceptions.RequestException as e:
                error_msg = "Network error: Please check your internet connection."
                self.write_to_output(f"Error: {error_msg} ({str(e)})", 'system')
                self.gui_speak(error_msg)
                
            except KeyError as e:
                error_msg = f"Data parsing error: Unexpected API response format. Missing key: {str(e)}"
                self.write_to_output(f"Error: {error_msg}", 'system')
                self.gui_speak("Sorry, there was an error processing the weather data.")
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.write_to_output(f"Error: {error_msg}", 'system')
                self.gui_speak("Sorry, there was an unexpected error getting the weather information.")

        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(command)
            if response.text:
                self.gui_speak(response.text)
                return True
        except Exception as e:
            self.write_to_output(f"Error getting AI response: {str(e)}", 'system')
            self.gui_speak("I'm sorry, I encountered an error while processing your request.")
            return False
        
        self.gui_speak("I'm not sure how to help with that.")
        return False

    def handle_maps_command(self, command):
        try:
            trigger_words = ["map", "maps", "direction", "directions", "navigate", "location", "where is", "to", "from"]
            query = command
            for word in trigger_words:
                query = query.replace(word, "").strip()

            if not query:
                self.gui_speak("Please specify a location or destination.")
                return

            if "direction" in command or "directions" in command or "navigate" in command:
                if " to " in command:
                    parts = command.split(" to ")
                    if len(parts) >= 2:
                        source = parts[0].strip()
                        for word in trigger_words:
                            source = source.replace(word, "").strip()
                        destination = parts[1].strip()
                        url = f"https://www.google.com/maps/dir/{urllib.parse.quote(source)}/{urllib.parse.quote(destination)}"
                        self.write_to_output(f"Opening directions from {source} to {destination}", 'system')
                        self.gui_speak(f"Opening directions from {source} to {destination}")
                    else:
                        url = f"https://www.google.com/maps/dir//{urllib.parse.quote(query)}"
                        self.write_to_output(f"Opening directions to {query}", 'system')
                        self.gui_speak(f"Opening directions to {query}")
                else:
                    url = f"https://www.google.com/maps/dir//{urllib.parse.quote(query)}"
                    self.write_to_output(f"Opening directions to {query}", 'system')
                    self.gui_speak(f"Opening directions to {query}")
            else:
                url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
                self.write_to_output(f"Showing location: {query}", 'system')
                self.gui_speak(f"Showing {query} on Google Maps")

            webbrowser.open(url)

        except Exception as e:
            error_msg = f"Sorry, I couldn't process the maps request: {str(e)}"
            self.write_to_output(f"Error: {error_msg}", 'system')
            self.gui_speak("Sorry, I couldn't process the maps request.")

    def play_youtube_video(self, query=None):
        try:
            if query:
                words = query.split()
                unique_words = []
                for word in words:
                    if word not in unique_words:
                        unique_words.append(word)
                clean_query = ' '.join(unique_words)
                
                search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_query)}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(search_url, headers=headers)
                
                video_id_pattern = r"watch\?v=(\S{11})"
                matches = re.findall(video_id_pattern, response.text)
                
                if matches:
                    video_id = matches[0]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    self.write_to_output(f"Playing: {clean_query}", 'system')
                    webbrowser.open(video_url)
                else:
                    self.write_to_output("Couldn't find the exact video, opening search results", 'system')
                    webbrowser.open(search_url)
            else:
                webbrowser.open("https://www.youtube.com")
                
        except Exception as e:
            self.write_to_output(f"Error playing video: {str(e)}", 'system')
            if query:
                clean_query = query.strip().replace(" ", "+")
                url = f"https://www.youtube.com/results?search_query={clean_query}"
                webbrowser.open(url)

if __name__ == "__main__":
    try:
        app = ModernAssistantGUI()
        app.root.mainloop()
    except Exception as e:

        print(f"Error starting application: {str(e)}")
