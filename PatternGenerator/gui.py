"""
Pattern Generator - Standalone Recoil Pattern Analysis Tool
Generates anti-recoil patterns from GIFs/images for AimSync integration

Usage:
    python gui.py --input patterns/ak47_spray.gif --output weapon_data_ak47.py
"""

import sys
import os
from datetime import datetime  # Fixed missing import
import pathlib

# Add pattern generator module paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from customtkinter import CTk, CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkProgressBar, CTkCheckBox, CTkOptionMenu, CTkComboBox , CTkTextbox, CTkSlider, CTkImage
from tkinter import filedialog, messagebox
import json
import cv2
import numpy as np
from PIL import Image, ImageTk

# Import our analysis modules
try:
    from engine.image_analyzer import ImageAnalyzer, PointData
    from engine.trajectory_detector import TrajectoryDetector
    from engine.pattern_calculator import PatternCalculator
except ImportError:
    from .engine.image_analyzer import ImageAnalyzer, PointData
    from .engine.trajectory_detector import TrajectoryDetector
    from .engine.pattern_calculator import PatternCalculator


class PatternGeneratorApp(CTk):
    """Main Pattern Generator Application Window"""
    
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Pattern Generator - AimSync Recoil Analyzer")
        self.geometry("1400x800")
        self.minsize(1200, 600)
        self.preview_frames = []

        # Create grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top panel with controls
        self.top_panel = CTkFrame(master=self, fg_color="#2b2d42", corner_radius=10)
        self.top_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Left side controls
        left_frame = CTkFrame(master=self.top_panel, fg_color="#373a50", corner_radius=8)
        left_frame.grid(row=0, column=0, padx=(0, 20), sticky="ns")
        left_frame.grid_columnconfigure(1, weight=1)

        # Input file selection
        self.input_label = CTkLabel(master=left_frame, text="📁 Input File:", font=("Arial", 12))
        self.input_label.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="ew")
        
        self.input_path_entry = CTkEntry(master=left_frame, 
                                 fg_color="#2b2d42", text_color="#ffffff", corner_radius=6)
        self.input_path_entry.grid(row=1, column=0, padx=(15, 5), pady=5, sticky="ew")

        self.select_btn = CTkButton(master=left_frame, text="📂 Select GIF/Image", command=self.select_input_file, 
                                    fg_color="#4a4e69", corner_radius=6)
        self.select_btn.grid(row=2, column=0, padx=(15, 5), pady=5)

        CTkLabel(master=left_frame, text="OR Drag & drop file here", font=("Arial", 10), text_color="#7f8fa6").grid(
            row=3, column=0, padx=(15, 5), pady=5)

        # Output configuration
        CTkLabel(master=left_frame, text="⚙️ Configuration:", font=("Arial", 12), fg_color="#4a4e69").grid(row=4, 
                                                                                                   column=0, padx=(15, 5), pady=10)
        
        self.output_name = CTkEntry(master=left_frame, 
                                 fg_color="#2b2d42", text_color="#ffffff", corner_radius=6)
        self.output_name.grid(row=5, column=1, padx=(0, 15), pady=5, sticky="ew")

        # Analysis settings
        CTkLabel(master=left_frame, text="⚡ Analysis Settings:", font=("Arial", 12), fg_color="#4a4e69").grid(row=6, 
                                                                                                           column=0, padx=(15, 5), pady=5)

        self.fps_label = CTkLabel(master=left_frame, text="FPS: Detect Automatically", font=("Arial", 10))
        self.fps_label.grid(row=7, column=0, padx=(15, 5), pady=2)

        # Frame Selection Settings
        frame_settings = CTkFrame(master=left_frame, fg_color="transparent")
        frame_settings.grid(row=8, column=0, columnspan=2, padx=15, pady=5, sticky="ew")
        
        CTkLabel(master=frame_settings, text="Start Frame:", font=("Arial", 10)).grid(row=0, column=0, padx=2)
        self.start_frame_entry = CTkEntry(master=frame_settings, width=45)
        self.start_frame_entry.insert(0, "0")
        self.start_frame_entry.grid(row=0, column=1, padx=2)

        CTkLabel(master=frame_settings, text="End:", font=("Arial", 10)).grid(row=0, column=2, padx=2)
        self.end_frame_entry = CTkEntry(master=frame_settings, width=45)
        self.end_frame_entry.insert(0, "-1")
        self.end_frame_entry.grid(row=0, column=3, padx=2)

        CTkLabel(master=frame_settings, text="Step:", font=("Arial", 10)).grid(row=0, column=4, padx=2)
        self.frame_step_entry = CTkEntry(master=frame_settings, width=45)
        self.frame_step_entry.insert(0, "1")
        self.frame_step_entry.grid(row=0, column=5, padx=2)

        # Analysis button
        self.analyze_btn = CTkButton(master=left_frame, text="🔍 Analyze & Generate Pattern", command=self.start_analysis, 
                                     fg_color="#6f7498", corner_radius=6)
        self.analyze_btn.grid(row=9, column=0, padx=(15, 5), pady=10)

        # Right side - Preview panel
        right_frame = CTkFrame(master=self.top_panel, fg_color="#2b2d42", corner_radius=8)
        right_frame.grid(row=0, column=1, sticky="ns")
        right_frame.grid_columnconfigure(0, weight=1)

        self.preview_label = CTkLabel(master=right_frame, text="📷 Frame Preview:\n(Click 'Analyze' to load)", 
                                      font=("Arial", 14), text_color="#7f8fa6")
        self.preview_label.pack(side="top", pady=10)

        self.frame_image = CTkLabel(master=right_frame, text="No preview available\n(yet!)")
        self.frame_image.pack(expand=True, fill="both")

        self.preview_slider = CTkSlider(master=right_frame, from_=0, to=1, number_of_steps=1, command=self._on_slider_move)
        self.preview_slider.pack(side="bottom", fill="x", padx=20, pady=10)
        self.preview_slider.set(0)

        # Bottom section - Status and logs
        bottom_panel = CTkFrame(master=self, fg_color="#2b2d42", corner_radius=10)
        bottom_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        # Status bar
        self.status_label = CTkLabel(master=bottom_panel, text="Ready. Select a GIF/image to begin analysis.", 
                                     font=("Arial", 11), text_color="#7f8fa6")
        self.status_label.pack(fill="x", pady=5)

        # Progress bar for analysis
        self.progress_frame = CTkFrame(master=bottom_panel, fg_color="#2b2d42", corner_radius=8)
        self.progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_label = CTkLabel(master=self.progress_frame, text="", font=("Arial", 11))
        self.progress_label.pack(pady=5)

        self.progress_bar = CTkProgressBar(master=self.progress_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=5)

        # Log console (shows analysis steps and results)
        log_height = 100
        self.log_frame = CTkFrame(master=bottom_panel, fg_color="#2b2d42", corner_radius=8)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_textbox = CTkTextbox(master=self.log_frame, font=("Consolas", 9), 
                                       height=log_height, fg_color="#373a50")
        self.log_textbox.pack(fill="both", expand=True)

        # Bind to output directory for file drop support
        self.output_directory = pathlib.Path(__file__).parent / "patterns"

    def log_message(self, message: str, level="info"):
        """Add message to log console"""
        current_time = datetime.now().strftime("%H:%M:%S")

        if level == "error":
            msg = f"\n{'='*40}\n[{current_time}] [ERROR] {message}\n"
        elif level == "success":
            msg = f"\n{'='*40}\n[{current_time}] [SUCCESS] {message}\n"
        else:
            msg = f"[{current_time}] {message}\n"

        self.log_textbox.insert("end", msg)
        self.log_textbox.see("end")

    def select_input_file(self):
        """Open file dialog to select GIF or image"""
        filetypes = [("GIF Images", "*.gif"), ("PNG Images", "*.png"), 
                     ("JPEG Images", "*.jpg *.jpeg"), ("All Files", "*.*")]
        file_path = filedialog.askopenfilename(filetypes=filetypes, initialdir=str(self.output_directory))

        if file_path:
            self.input_path_entry.delete(0, "end")
            self.input_path_entry.insert(0, file_path)
            self.log_message(f"Selected file: {os.path.basename(file_path)}", level="info")
            
            # Update preview label with file info
            try:
                # Load all frames for the slider preview
                self.preview_frames = []
                with Image.open(file_path) as img:
                    width, height = img.size
                    n_frames = getattr(img, 'n_frames', 1)
                    
                    for i in range(n_frames):
                        img.seek(i)
                        self.preview_frames.append(img.convert("RGB"))

                # Perform a silent pre-scan to suggest frames
                analyzer = ImageAnalyzer()
                total_f, start_f, end_f = analyzer.detect_shooting_window(file_path)
                
                # Update the Entry fields automatically
                self.start_frame_entry.delete(0, "end")
                self.start_frame_entry.insert(0, str(start_f))
                self.end_frame_entry.delete(0, "end")
                self.end_frame_entry.insert(0, str(end_f))

                # Update slider range
                if len(self.preview_frames) > 1:
                    self.preview_slider.configure(from_=0, to=len(self.preview_frames) - 1, number_of_steps=len(self.preview_frames) - 1)
                else:
                    self.preview_slider.configure(from_=0, to=0, number_of_steps=1)
                
                self.preview_slider.set(0)
                self.show_frame(0)

                fps = self._detect_gif_fps(file_path)
                self.log_message(f"File loaded: {width}x{height}, {total_f} frames. Suggested shooting window: {start_f}-{end_f}")
                
            except Exception as e:
                self.log_message(f"Error previewing file: {e}", level="error")

    def show_frame(self, index):
        """Update the preview label with the frame at the given index"""
        if not self.preview_frames:
            return
            
        idx = int(index)
        if 0 <= idx < len(self.preview_frames):
            # Update the frame counter text
            self.preview_label.configure(text=f"📷 Frame Preview: {idx} / {len(self.preview_frames)-1}")

            pil_img = self.preview_frames[idx]
            
            # Calculate aspect ratio to fit within 400x400 area
            w, h = pil_img.size
            aspect = w / h
            max_size = 400
            
            new_w = max_size if aspect > 1 else int(max_size * aspect)
            new_h = max_size if aspect <= 1 else int(max_size / aspect)
                
            ctk_img = CTkImage(light_image=pil_img, dark_image=pil_img, size=(new_w, new_h))
            self.frame_image.configure(image=ctk_img, text="")
            self.frame_image._image = ctk_img # Keep reference to prevent garbage collection

    def _on_slider_move(self, value):
        """Callback for slider movement"""
        self.show_frame(value)

    def on_drag_drop(self, event):
        """Handle drag and drop of files"""
        if hasattr(event.widget, "get"):
            file_path = event.widget.get()
            if os.path.isfile(file_path):
                self.input_path_entry.delete(0, "end")
                self.input_path_entry.insert(0, file_path)
                self.log_message(f"File dropped: {os.path.basename(file_path)}", level="info")

    def start_analysis(self):
        """Start pattern analysis process"""
        input_path = self.input_path_entry.get().strip()
        output_name = self.output_name.get().strip()

        if not input_path or not os.path.isfile(input_path):
            messagebox.showerror("Error", "Please select a valid GIF/image file first!")
            return

        if not output_name:
            messagebox.showwarning("Warning", "Please enter an output pattern name!")
            return

        try:
            # Initialize analysis engine
            self.log_message(f"Starting analysis of {os.path.basename(input_path)}")
            self.progress_bar.start()

            # Detect FPS for GIF
            fps = self._detect_gif_fps(input_path)
            self.fps_label.configure(text=f"FPS: {fps}")

            # Get frame selection parameters
            try:
                start_f = int(self.start_frame_entry.get())
                end_f = int(self.end_frame_entry.get())
                step_f = int(self.frame_step_entry.get())
            except ValueError:
                start_f, end_f, step_f = 0, -1, 1

            # Analyze frames and extract trajectory
            analyzer = ImageAnalyzer(fps=fps)
            points = analyzer.analyze_file(input_path, start_frame=start_f, end_frame=end_f, frame_step=step_f)

            if points:
                self.log_message(f"Extracted {len(points)} movement points")

                # Track trajectory and compute segments
                detector = TrajectoryDetector()
                segments = detector.detect_trajectory(points, fps=fps)
                
                if segments:
                    self.log_message(f"Detected {len(segments)} recoil segments")

                    # Calculate final recoil pattern
                    calculator = PatternCalculator()
                    calculated_pattern = calculator.calculate_pattern(segments, weapon_type="assault_rifle")

                    # Export results to JSON
                    json_path = self.output_directory / f"{output_name}_generated.json"
                    calculator.export_to_json(calculated_pattern, str(json_path))

                    self.log_message("Pattern calculation complete!", level="success")
                    self.log_message(f"Pattern saved to: {json_path}", level="success")
                else:
                    self.log_message("No movement segments could be derived from points.", level="error")
            else:
                self.log_message("No points detected in file.", level="error")

        except Exception as e:
            self.log_message(f"Analysis failed: {str(e)}", level="error")
            messagebox.showerror("Analysis Error", f"An error occurred during analysis:\n\n{e}")
        finally:
            self.progress_bar.stop()

    def _detect_gif_fps(self, file_path):
        """Detect frames per second from GIF header"""
        try:
            img = Image.open(file_path)
            # Get timing info from GIF
            if hasattr(img, 'info') and 'duration' in img.info:
                duration = img.info['duration']  # Duration in hundredths of a second
                if duration > 0:
                    return round(100 / duration)
                return 30  # Default fallback for GIFs
            return 30
        except Exception as e:
            self.log_message(f"FPS detection error: {e}", level="error")
            return 30


if __name__ == "__main__":
    app = PatternGeneratorApp()
    app.mainloop()
