import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from gtts import gTTS
import os
import tempfile
import threading
from datetime import datetime
import asyncio

try:
    from googletrans import Translator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

try:
    import pygame
    PLAYER_ENGINE = "pygame"
    pygame.mixer.init()
except ImportError:
    PLAYER_ENGINE = "os"

class TextToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Text-to-Speech Converter")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Set theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Initialize translator if available
        self.translator = Translator() if TRANSLATION_AVAILABLE else None
        
        # Variables
        self.input_text = tk.StringVar()
        self.output_language = tk.StringVar(value="en")
        self.translate_first = tk.BooleanVar(value=False)
        self.translation_language = tk.StringVar(value="en")
        self.current_audio_file = None
        
        # Language options
        self.languages = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Italian': 'it',
            'Japanese': 'ja',
            'Korean': 'ko',
            'Chinese': 'zh-CN',
            'Russian': 'ru',
            'Portuguese': 'pt',
            'Hindi': 'hi',
            'Arabic': 'ar'
        }
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Text-to-Speech Converter", font=("Helvetica", 18, "bold"))
        title_label.pack(pady=10)
        
        # Text input area
        text_frame = ttk.LabelFrame(main_frame, text="Enter Text")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.text_input = tk.Text(text_frame, height=8, width=50, wrap=tk.WORD)
        self.text_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Translation options
        translation_frame = ttk.LabelFrame(main_frame, text="Translation Options")
        translation_frame.pack(fill=tk.X, pady=10)
        
        translate_check = ttk.Checkbutton(
            translation_frame, 
            text="Translate text before converting to speech",
            variable=self.translate_first,
            command=self.toggle_translation_options
        )
        translate_check.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        ttk.Label(translation_frame, text="Translate to:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.translation_combo = ttk.Combobox(
            translation_frame,
            textvariable=self.translation_language,
            values=list(self.languages.keys()),
            state="readonly"
        )
        self.translation_combo.grid(row=1, column=1, sticky="we", padx=10, pady=5)
        self.translation_combo.set("English")
        self.translation_combo.config(state="disabled")
        
        # TTS options
        tts_frame = ttk.LabelFrame(main_frame, text="Text-to-Speech Options")
        tts_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(tts_frame, text="Output Voice Language:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.voice_combo = ttk.Combobox(
            tts_frame,
            textvariable=self.output_language,
            values=list(self.languages.keys()),
            state="readonly"
        )
        self.voice_combo.grid(row=0, column=1, sticky="we", padx=10, pady=5)
        self.voice_combo.set("English")
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.play_button = ttk.Button(buttons_frame, text="Preview", command=self.preview_speech)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(buttons_frame, text="Save as MP3", command=self.save_as_mp3)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="Stop", command=self.stop_audio, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(buttons_frame, text="Clear", command=self.clear_text)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def toggle_translation_options(self):
        if self.translate_first.get():
            self.translation_combo.config(state="readonly")
        else:
            self.translation_combo.config(state="disabled")
    
    def get_language_code(self, language_name):
        return self.languages.get(language_name, 'en')
    
    def get_text_content(self):
        return self.text_input.get("1.0", tk.END).strip()
    
    async def translate_text_async(self, text, target_language):
        if not TRANSLATION_AVAILABLE:
            messagebox.showerror("Error", "Translation feature is not available. Please install googletrans library.")
            return text
            
        try:
            self.status_var.set("Translating...")
            self.root.update()
            translated = await self.translator.translate(text, dest=target_language)
            self.status_var.set("Translation complete")
            return translated.text
        except Exception as e:
            messagebox.showerror("Translation Error", f"Failed to translate text: {str(e)}")
            self.status_var.set("Translation failed")
            return text

    def translate_text(self, text, target_language):
        return asyncio.run(self.translate_text_async(text, target_language))
    
    def text_to_speech(self, text, language, output_file=None):
        try:
            self.status_var.set("Converting to speech...")
            self.root.update()
            
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to file
            tts.save(output_file)
            
            self.status_var.set(f"Audio saved to: {output_file}")
            return True
        except Exception as e:
            messagebox.showerror("TTS Error", f"Failed to convert text to speech: {str(e)}")
            self.status_var.set("Failed to convert")
            return False
    
    def preview_speech(self):
        text = self.get_text_content()
        if not text:
            messagebox.showinfo("Info", "Please enter some text to convert to speech.")
            return
        
        # Translate if needed
        if self.translate_first.get():
            target_lang = self.get_language_code(self.translation_combo.get())
            text = self.translate_text(text, target_lang)
        
        # Set language for speech
        language = self.get_language_code(self.voice_combo.get())
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        # Convert to speech
        if self.text_to_speech(text, language, temp_file.name):
            self.current_audio_file = temp_file.name
            
            # Play the audio in a separate thread to avoid freezing the GUI
            threading.Thread(target=self.play_audio, args=(temp_file.name,), daemon=True).start()
            
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set("Playing audio...")
    
    def play_audio(self, audio_file):
        if PLAYER_ENGINE == "pygame":
            try:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pass
                self.root.after(0, self.reset_after_playback)
            except Exception as e:
                messagebox.showerror("Playback Error", f"Failed to play audio: {str(e)}")
                self.status_var.set("Playback failed")
        else:
            os.system(f"start {audio_file}" if os.name == "nt" else f"open {audio_file}")
            self.root.after(3000, self.reset_after_playback)  # Approximate timing
    
    def stop_audio(self):
        if PLAYER_ENGINE == "pygame" and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.reset_after_playback()
    
    def reset_after_playback(self):
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Ready")
        
        # Clean up temporary file
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.unlink(self.current_audio_file)
                self.current_audio_file = None
            except:
                pass
    
    def save_as_mp3(self):
        text = self.get_text_content()
        if not text:
            messagebox.showinfo("Info", "Please enter some text to convert to speech.")
            return
        
        # Translate if needed
        if self.translate_first.get():
            target_lang = self.get_language_code(self.translation_combo.get())
            text = self.translate_text(text, target_lang)
        
        # Set language for speech
        language = self.get_language_code(self.voice_combo.get())
        
        # Get a filename from the user
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"speech_{timestamp}.mp3"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if not file_path:
            return  # User cancelled
        
        # Convert and save
        if self.text_to_speech(text, language, file_path):
            result = messagebox.askyesno("Success", f"Audio saved to {file_path}. Would you like to play it now?")
            if result:
                # Play the saved audio
                threading.Thread(target=self.play_audio, args=(file_path,), daemon=True).start()
                self.stop_button.config(state=tk.NORMAL)
    
    def clear_text(self):
        self.text_input.delete("1.0", tk.END)
        self.status_var.set("Ready")

if __name__ == "__main__":
    root = tk.Tk()
    app = TextToSpeechApp(root)
    root.mainloop()
