import sys
import threading
import time
import json
import os
import webview
from transcriber_engine import TranscriberEngine
from gemini_api import GeminiAPI
from config import GEMINI_API_KEY

class Api:
    def __init__(self):
        self.engine = None
        self.is_recording = False
        self._window = None
        
        # Use key from config
        self.api_key = GEMINI_API_KEY
        try:
            self.gemini = GeminiAPI(self.api_key)
            print("Gemini API initialized from config")
        except Exception as e:
            print(f"Gemini init error: {e}")
            self.gemini = None
        
        # Buffers
        # Buffers
        self.full_transcript = []
        self.last_transcript_index = 0
        self.current_summary_text = ""
        self.summary_timer = None
        self.has_received_audio = False

    def set_window(self, window):
        self._window = window

    def update_api_key(self, key):
        self.api_key = key
        self.gemini = GeminiAPI(key)
        return True

    def start_capture(self, model_size, audio_source='system'):
        if self.is_recording:
            return {"ok": False, "error": "Already recording"}

        print(f"Starting capture with model: {model_size}, source: {audio_source}")
        
        # Reset Logic for new session
        # Reset Logic for new session
        self.full_transcript = []
        self.last_transcript_index = 0
        self.current_summary_text = ""
        self.has_received_audio = False
        
        # Init engine (using backup logic)
        self.stop_capture() # Ensure clean state

        self.engine = TranscriberEngine(
            model_size=model_size,
            audio_source=audio_source, # 'system' or 'microphone'
            callback=self.on_transcription_result
        )

        try:
            success = self.engine.start_recording()
            if success:
                self.is_recording = True
                # 🔥 Start Auto-Summary Timer will be triggered on first text packet
                # self.start_summary_timer() 
                return {"ok": True}
            else:
                return {"ok": False, "error": "Failed to start engine (check audio device)"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def stop_capture(self):
        # Stop Timer
        if self.summary_timer:
            self.summary_timer.cancel()
            self.summary_timer = None

        if self.engine:
            self.engine.stop_recording()
            self.engine = None
        self.is_recording = False
        return {"ok": True}

    def start_summary_timer(self):
        # Schedule next summary in 180 seconds (3 mins)
        if self.summary_timer: self.summary_timer.cancel()
        self.summary_timer = threading.Timer(180.0, self.auto_summary_task)
        self.summary_timer.start()
        
        # Tell UI to start countdown
        if self._window:
            self._window.evaluate_js("startCountdown(180)")
            self._window.evaluate_js("updateStatus('listening')")

    def auto_summary_task(self):
        if not self.is_recording: return
        
        print("🤖 Auto-Generating Summary (Incremental)...")
        if self._window: self._window.evaluate_js("updateStatus('processing')")

        # Get ONLY new items since last check ("Sliding Window")
        new_items = self.full_transcript[self.last_transcript_index:]
        new_text = "\n".join(new_items)
        
        # If nothing new, just reschedule
        if not new_text.strip():
            if self.is_recording: self.start_summary_timer()
            return

        if self.gemini:
            try:
                # Call Incremental Update
                # Pass existing summary as context
                update_part = self.gemini.update_summary(new_text, previous_context=self.current_summary_text)
                
                # Check for error string
                if update_part and "Oshibka" in update_part:
                     print(f"API Error: {update_part}")
                     # Append error to UI? Or just log? Let's append so user sees it.
                
                if update_part:
                    # Append new part
                    if self.current_summary_text:
                        self.current_summary_text += "\n\n" + update_part
                    else:
                        self.current_summary_text = update_part
                        
                    # Update Index so we don't process this text again
                    self.last_transcript_index = len(self.full_transcript)

                    # Update UI with FULL summary
                    safe_sum = json.dumps(self.current_summary_text)
                    if self._window:
                        self._window.evaluate_js(f"updateSummary({safe_sum})")
            except Exception as e:
                print(f"Auto-summary failed: {e}")
        
        # Re-schedule
        if self.is_recording:
            self.start_summary_timer()

    def on_transcription_result(self, timestamp, text):
        # Start timer on FIRST packet
        if not self.has_received_audio:
            self.has_received_audio = True
            self.start_summary_timer()
            print("🎤 First audio received -> Timer Started")

        # Store for log
        self.full_transcript.append(f"[{timestamp}] {text}")
        
        # Send to JS
        if self._window:
            safe_text = json.dumps(text)
            script = f"addLogItem('{timestamp}', {safe_text})"
            try:
                self._window.evaluate_js(script)
            except:
                pass

    def finalize_current_summary(self):
        if not self.gemini or not self.current_summary_text:
            return {"ok": False, "error": "Нет текста для обработки"}
            
        print("✨ Finalizing Summary ('Prichyosat')...")
        if self._window: self._window.evaluate_js("updateStatus('processing')")
        
        try:
            # Send current text for polishing
            final_text = self.gemini.finalize_summary(self.current_summary_text)
            
            if final_text:
                if "Oshibka" in final_text:
                     if self._window: self._window.evaluate_js("updateStatus('listening')")
                     return {"ok": False, "error": final_text}

                self.current_summary_text = final_text
                # Update UI
                safe_sum = json.dumps(final_text)
                if self._window: 
                    self._window.evaluate_js(f"updateSummary({safe_sum})")
                    self._window.evaluate_js("updateStatus('listening')") # Reset status
                return {"ok": True}
            else:
                if self._window: self._window.evaluate_js("updateStatus('listening')")
                return {"ok": False, "error": "Empty response"}
        except Exception as e:
            if self._window: self._window.evaluate_js("updateStatus('listening')")
            return {"ok": False, "error": str(e)}

    def generate_summary(self, text_content=None):
        # Manual Trigger
        
        if not self.gemini: 
            return {"ok": False, "error": "API Key not set"}
        
        if self._window: self._window.evaluate_js("updateStatus('processing')")

        if self.is_recording:
            # Incremental Update logic (Manual Trigger)
            new_items = self.full_transcript[self.last_transcript_index:]
            new_text = "\n".join(new_items)
            
            if new_text.strip():
                try:
                    update_part = self.gemini.update_summary(new_text, previous_context=self.current_summary_text)
                    if update_part:
                        if "Oshibka" in update_part:
                             if self._window: self._window.evaluate_js("updateStatus('listening')")
                             return {"ok": False, "error": update_part}

                        if self.current_summary_text:
                            self.current_summary_text += "\n\n" + update_part
                        else:
                            self.current_summary_text = update_part
                        self.last_transcript_index = len(self.full_transcript)
                except Exception as e:
                    return {"ok": False, "error": str(e)}
            
            # Reset timer
            self.start_summary_timer()
            # Update UI
            if self._window:
                 safe_sum = json.dumps(self.current_summary_text)
                 self._window.evaluate_js(f"updateSummary({safe_sum})")

            return {"ok": True, "summary": self.current_summary_text}
            
        else:
            # Full summary (Classic)
            print("Generating manual summary (Full/Classic)...")
            text = text_content if text_content else "\n".join(self.full_transcript)
            try:
                summary = self.gemini.create_summary(text) 
                if summary:
                    if "Oshibka" in summary:
                        if self._window: self._window.evaluate_js("updateStatus('listening')")
                        return {"ok": False, "error": summary}
                    
                    self.current_summary_text = summary
                    return {"ok": True, "summary": summary}
                else: 
                     return {"ok": False, "error": "Empty response"}
            except Exception as e:
                if self._window: self._window.evaluate_js("updateStatus('listening')")
                return {"ok": False, "error": str(e)}

    def clear_state(self):
        """Полная очистка состояния"""
        self.full_transcript = []
        self.last_transcript_index = 0
        self.current_summary_text = ""
        self.has_received_audio = False
        
        if self.summary_timer:
            self.summary_timer.cancel()
            self.summary_timer = None
            
        print("🗑️ State Cleared")
        return {"ok": True}

    def export_html(self, summary_html):
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Create hidden root window
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True) # Bring to front
            
            # Generate smart filename
            initial_name = "Cera_Summary"
            if self.gemini and self.current_summary_text:
                print("Generating filename...")
                initial_name = self.gemini.generate_filename_title(self.current_summary_text)

            filename = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
                initialfile=initial_name,
                title="Экспорт конспекта"
            )
            
            root.destroy()
            
            if filename:
                full_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Cera Summary</title>
                    <style>
                        body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
                        h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                        .timestamp {{ color: #888; font-size: 0.8em; }}
                        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }}
                    </style>
                </head>
                <body>
                    <h1>📄 Cera Summary</h1>
                    <div class="content">
                        {summary_html}
                    </div>
                    <hr>
                    <p class="timestamp">Generated by Cera on {time.strftime("%Y-%m-%d %H:%M")}</p>
                </body>
                </html>
                """
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                return {"ok": True}
            return {"ok": False, "cancel": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_state(self):
        return {
            "isRecording": self.is_recording
        }

def main():
    api = Api()
    
    window = webview.create_window(
        'Цера — Десктоп', 
        'index.html',
        width=450,
        height=850,
        resizable=True,
        js_api=api
    )
    
    api.set_window(window)
    webview.start(debug=False)

if __name__ == '__main__':
    main()
