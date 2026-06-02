"""
ImageAnalyzer Module - Handles GIF/Image parsing and feature detection
Extracts movement points from animated GIFs by detecting visual patterns (dots, crosses)
"""

import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import json


@dataclass
class PointData:
    """Represents a single movement point in the recoil pattern"""
    x: float          # Horizontal movement value (screen pixels or relative)
    y: float          # Vertical movement value
    frame_number: int = 0       # Frame where this point was detected
    timestamp_ms: int = 0       # Timestamp from GIF timing
    confidence: float = 1.0     # Detection confidence score (0.0 - 1.0)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to (x, y, duration) tuple for weapon_data.py"""
        # Default duration based on frame timing
        return (self.x, self.y, 100)


class ImageAnalyzer:
    """
    Analyzes GIFs and images to detect visual patterns for recoil compensation
    
    Detects features like:
    - Bullet impact dots (round markers)
    - Crosshair positions
    - Muzzle flash locations
    - Movement trajectory between frames
    """
    
    def __init__(self, fps: int = 30):
        """
        Initialize ImageAnalyzer
        
        Args:
            fps: Frames per second for timing calculations (default: 30)
        """
        self.fps = fps
        self.frame_count = 0
        self.trajectory_points: List[PointData] = []
        
    def analyze_file(self, file_path: str, start_frame: int = 0, 
                     end_frame: int = -1, frame_step: int = 1) -> List[PointData]:
        """
        Main analysis entry point - processes entire GIF or single image
        
        Args:
            file_path: Path to GIF or image file
            start_frame: Index of frame to start analysis
            end_frame: Index of frame to stop (-1 for end)
            frame_step: Process every Nth frame
        Returns:
            List of PointData objects representing detected movement points
        """
        self.frame_count = 0
        self.trajectory_points = []
        
        is_gif = file_path.lower().endswith('.gif')
        
        try:
            if is_gif:
                # Process animated GIF frame by frame
                self.trajectory_points = self._analyze_gif(file_path, start_frame, end_frame, frame_step)
            else:
                # Single static image - treat as first frame
                points = self._process_single_frame(file_path)
                self.trajectory_points.extend(points)
                
        except Exception as e:
            print(f"Analysis error: {e}")
            return []
            
        return self.trajectory_points
    
    def _analyze_gif(self, file_path: str, start_frame: int = 0, 
                     end_frame: int = -1, frame_step: int = 1) -> List[PointData]:
        """
        Process animated GIF frame by frame
        
        Args:
            file_path: Path to GIF file
            start_frame: Index of frame to start analysis
            end_frame: Index of frame to stop (-1 for end)
            frame_step: Process every Nth frame
        Returns:
            List of movement points detected across all frames
        """
        # Use PIL for reliable GIF handling
        with Image.open(file_path) as img:
            # Get basic info
            width, height = img.size
            duration_info = getattr(img, 'info', {}).get('duration', 100)
            
            print(f"Processing GIF: {width}x{height}, Duration: {duration_info}/100ms")
            
            # Loop through frames
            n_frames = getattr(img, 'n_frames', 1)
            print(f"Total frames to process: {n_frames}")
            
            # Calculate frame bounds
            actual_start = max(0, start_frame)
            actual_end = n_frames if end_frame == -1 else min(end_frame + 1, n_frames)
            actual_step = max(1, frame_step)

            for i in range(actual_start, actual_end, actual_step):
                try:
                    img.seek(i)
                    
                    # Extract frame and convert to numpy array for OpenCV
                    frame_array = np.array(img.convert('RGB'))
                    
                    # Detect features in this frame
                    points = self._detect_features(frame_array, i)
                    
                    if points:
                        for point in points:
                            point.frame_number = i
                            point.timestamp_ms = duration_info  # Store frame duration
                            
                            # Convert screen coordinates to relative movement values
                            point.x = self._convert_to_relative(point.x, width)
                            point.y = self._convert_to_relative(point.y, height)
                        
                        self.trajectory_points.extend(points)
                    
                except Exception as e:
                    print(f"Frame {i} error: {e}")
                    continue
            
            print(f"Processed {len(range(actual_start, actual_end, actual_step))} frames, found {len(self.trajectory_points)} points")
        
        return self.trajectory_points

    def detect_shooting_window(self, file_path: str) -> Tuple[int, int, int]:
        """
        Scans the GIF to find the suggested start and end frames based on activity.
        
        Returns:
            Tuple of (total_frames, suggested_start, suggested_end)
        """
        if not file_path.lower().endswith('.gif'):
            return (1, 0, 0)

        try:
            with Image.open(file_path) as img:
                n_frames = getattr(img, 'n_frames', 1)
                first_activity = -1
                last_activity = -1

                # Scan every 2nd frame for speed to find visual triggers
                for i in range(0, n_frames, 2):
                    img.seek(i)
                    frame_array = np.array(img.convert('RGB'))
                    gray = cv2.cvtColor(frame_array, cv2.COLOR_RGB2GRAY)
                    
                    # Check for muzzle flash (bright spots) or impact dots
                    has_flash = len(self._detect_muzzle_flash(gray)) > 0
                    has_dots = len(self._detect_impact_dots(gray)) > 0

                    if has_flash or has_dots:
                        if first_activity == -1:
                            first_activity = i
                        last_activity = i

                # Fallbacks if no activity detected
                if first_activity == -1:
                    first_activity = 0
                if last_activity == -1:
                    last_activity = n_frames - 1
                
                # Add a small buffer (start 1 frame early, end 1 frame late)
                suggested_start = max(0, first_activity - 1)
                suggested_end = min(n_frames - 1, last_activity + 1)

                return (n_frames, suggested_start, suggested_end)

        except Exception as e:
            print(f"Scanning error: {e}")
            return (0, 0, 0)
    
    def _process_single_frame(self, file_path: str) -> List[PointData]:
        """
        Process single static image
        
        Args:
            file_path: Path to image file
            
        Returns:
            Single movement point or empty list if no features found
        """
        with Image.open(file_path) as img:
            width, height = img.size
            frame_array = np.array(img.convert('RGB'))
            
            # Detect initial state from static image
            points = self._detect_features(frame_array, 0)
            
            return points
    
    def _detect_features(self, frame_array: np.ndarray, 
                        frame_number: int) -> List[PointData]:
        """
        Detect visual features in a single frame
        
        Args:
            frame_array: Numpy array of RGB image
            frame_number: Current frame index
            
        Returns:
            List of PointData objects found in this frame
        """
        points = []
        
        # Convert to grayscale for feature detection
        gray = cv2.cvtColor(frame_array, cv2.COLOR_RGB2GRAY)
        
        # 1. Detect impact dots (bullet hit markers)
        dot_points = self._detect_impact_dots(gray)
        
        # 2. Detect crosshair position if visible
        crosshair_pos = self._detect_crosshair_position(frame_array)
        
        # 3. Detect muzzle flash area
        flash_areas = self._detect_muzzle_flash(gray)
        
        # Collect all detected features
        for point_data in dot_points:
            points.append(point_data)
            
        if crosshair_pos:
            # Create a reference point for crosshair position
            points.append(PointData(
                x=0,  # Will be calculated relative to trajectory
                y=0,
                frame_number=frame_number,
                confidence=0.85
            ))
            
        return points
    
    def _detect_impact_dots(self, gray: np.ndarray) -> List[PointData]:
        """
        Detect bullet impact dots (usually circular markers)
        
        Uses blob detection and contour analysis
        
        Args:
            gray: Grayscale image array
            
        Returns:
            List of PointData for each detected dot
        """
        points = []
        
        try:
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Use Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Filter by area (ignore noise and large regions)
                area = cv2.contourArea(contour)
                if 30 < area < 2000:  # Tightened area range
                    # Calculate circularity: 4*pi*Area / Perimeter^2
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter == 0: continue
                    circularity = 4 * np.pi * (area / (perimeter * perimeter))
                    
                    # We only want dots (high circularity)
                    if circularity < 0.3:
                        continue

                    x, y, w, h = cv2.boundingRect(contour)
                    cx, cy = x + w // 2, y + h // 2
                    
                    # Aspect ratio check (dots should be square-ish)
                    aspect_ratio = float(w) / h
                    if not (0.5 < aspect_ratio < 2.0):
                        continue

                    points.append(PointData(
                        x=cx,
                        y=cy,
                        frame_number=0,  # Will be updated later
                        confidence=min(0.95, 0.7 + (area / 10000))  # Higher area = higher confidence
                    ))
                    
        except Exception as e:
            print(f"Dot detection error: {e}")
        
        return points
    
    def _detect_crosshair_position(self, frame_array: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect crosshair position from the image
        
        Args:
            frame_array: RGB image array
            
        Returns:
            Tuple of (x, y) coordinates or None if not found
        """
        try:
            # Convert to HSV for color-based detection
            hsv = cv2.cvtColor(frame_array, cv2.COLOR_RGB2HSV)
            
            # Crosshairs are typically red, white, or bright colors
            lower_red = np.array([0, 100, 100])
            upper_red = np.array([10, 255, 255])
            
            mask = cv2.inRange(hsv, lower_red, upper_red)
            
            # Apply morphological operations to clean up noise
            kernel = np.ones((5, 5), np.uint8)
            mask_eroded = cv2.erode(mask, kernel, iterations=2)
            mask_dilated = cv2.dilate(mask_eroded, kernel, iterations=5)
            
            # Find contours in the mask
            contours, _ = cv2.findContours(mask_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
                
            # Get the largest contour (crosshair center)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if 100 < area < 5000:  # Filter by reasonable size
                x, y, w, h = cv2.boundingRect(largest_contour)
                cx, cy = x + w // 2, y + h // 2
                
                return (cx, cy)
                
        except Exception as e:
            print(f"Crosshair detection error: {e}")
            
        return None
    
    def _detect_muzzle_flash(self, gray: np.ndarray) -> List[Tuple[int, int, float]]:
        """
        Detect muzzle flash area (bright regions in image)
        
        Args:
            gray: Grayscale image array
            
        Returns:
            List of (x, y, intensity) tuples for each flash region
        """
        flash_areas = []
        
        try:
            # Threshold to find bright areas
            _, threshold = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            
            # Find contours in thresholded image
            contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by reasonable flash size
                if 1000 < area < 50000:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        
                        # Calculate average intensity in region
                        mask = np.zeros(gray.shape, np.uint8)
                        cv2.drawContours(mask, [contour], -1, 255, -1)
                        mean_val = cv2.mean(gray, mask=mask)[0]
                        
                        flash_areas.append((cX, cY, mean_val))
                        
        except Exception as e:
            print(f"Muzzle flash detection error: {e}")
        
        return flash_areas
    
    def _convert_to_relative(self, screen_coord: int, image_size: int) -> float:
        """
        Convert absolute screen coordinate to relative movement value
        
        Args:
            screen_coord: Absolute coordinate from image (pixels from top-left)
            image_size: Image dimension
            
        Returns:
            Relative movement value suitable for recoil pattern
        """
        # Normalize to reasonable recoil compensation range (-50 to +50)
        normalized = (screen_coord / max(image_size, 1)) * 50
        
        # Clamp to realistic range
        return max(-50, min(50, normalized))
    
    def get_trajectory_summary(self) -> Dict:
        """
        Get summary statistics of detected trajectory points
        
        Returns:
            Dictionary with analysis statistics
        """
        if not self.trajectory_points:
            return {}
            
        total_points = len(self.trajectory_points)
        frames_covered = max(p.frame_number for p in self.trajectory_points) + 1
        
        # Calculate overall movement vectors
        x_values = [p.x for p in self.trajectory_points]
        y_values = [p.y for p in self.trajectory_points]
        
        return {
            "total_points": total_points,
            "frames_analyzed": frames_covered,
            "fps": self.fps,
            "x_range": (min(x_values), max(x_values)),
            "y_range": (min(y_values), max(y_values)),
            "average_confidence": np.mean([p.confidence for p in self.trajectory_points])
        }


# Export classes for module usage
__all__ = ['ImageAnalyzer', 'PointData']