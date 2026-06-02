"""TrajectoryDetector Module - Handles recoil vector calculation and pattern generation"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import sys
sys.path.insert(0, ".")
from engine.image_analyzer import PointData

@dataclass  
class TrajectorySegment:
    """Represents a recoil segment between two movement points"""
    start_point: PointData
    end_point: PointData
    vector_x: float
    vector_y: float
    duration_ms: int
    compensation_vector_x: float
    compensation_vector_y: float
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to weapon_data.py tuple format (x, y, duration)"""
        return (self.compensation_vector_x, self.compensation_vector_y, 0.1)

class TrajectoryDetector:
    """
    Analyzes trajectory data from ImageAnalyzer and extracts recoil compensation patterns
    
    Calculates movement vectors between consecutive frames and determines optimal
    anti-recoil compensation for each segment.
    """
    
    def __init__(self):
        self.segments = []
        self.min_segment_duration = 20    # Minimum duration between points (ms)
        self.noise_threshold = 0.2        # Ignore movements smaller than this (relative units)
        
    def detect_trajectory(self, trajectory_points: List[PointData], fps: int = 30):
        """
        Main detection method - processes trajectory points and extracts segments
        
        Args:
            trajectory_points: List of PointData from ImageAnalyzer
            fps: Frames per second for timing calculation
            
        Returns:
            List of TrajectorySegment objects representing recoil segments
        """
        if not trajectory_points:
            print("No trajectory points to analyze")
            return []
            
        self.segments = []
        
        # 1. Group points by frame and pick the "best" representative for each frame
        frame_map = {}
        for p in trajectory_points:
            if p.frame_number not in frame_map or p.confidence > frame_map[p.frame_number].confidence:
                frame_map[p.frame_number] = p
        
        # 2. Sort representative points by frame number
        sorted_points = [frame_map[f] for f in sorted(frame_map.keys())]
        
        print(f"Consolidated into {len(sorted_points)} representative frame points.")
        
        # Calculate duration per frame in milliseconds
        duration_per_frame = 1000 / fps
        
        # 3. Calculate vectors between representative points
        i = 0
        while i < len(sorted_points):
            current_point = sorted_points[i]
            
            # Look for next point that satisfies the movement threshold
            j = i + 1
            found_next = False
            
            while j < len(sorted_points):
                time_diff = (sorted_points[j].frame_number - current_point.frame_number) * duration_per_frame
                
                # Allow gaps up to 1.5 seconds if frame stepping is high
                if time_diff > 1500:
                    break
                    
                next_point = sorted_points[j]
                dx = next_point.x - current_point.x
                dy = next_point.y - current_point.y
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance >= self.noise_threshold:
                    segment = self._create_segment(current_point, next_point, time_diff, dx, dy)
                    self.segments.append(segment)
                    i = j
                    found_next = True
                    break
                j += 1
            
            if not found_next:
                i += 1
            
        print(f"Detected {len(self.segments)} recoil segments")
        
        return self.segments
    
    def _create_segment(self, start: PointData, end: PointData, 
                       duration: int, dx: float, dy: float):
        """Create a TrajectorySegment from two points"""
        
        # Calculate compensation vector (opposite of movement)
        comp_x = -dx * 0.85  # 85% compensation
        comp_y = -dy * 0.92  # 92% compensation for vertical recoil
        
        return TrajectorySegment(
            start_point=start,
            end_point=end,
            vector_x=dx,
            vector_y=dy,
            duration_ms=duration,
            compensation_vector_x=comp_x,
            compensation_vector_y=comp_y
        )
    
    def get_compensation_points(self) -> List[Tuple[float, float]]:
        """Get just the compensation vectors as tuples for weapon_data.py"""
        points = []
        
        for segment in self.segments:
            # Round to 1 decimal place for cleaner output
            x_rounded = round(segment.compensation_vector_x, 1)
            y_rounded = round(segment.compensation_vector_y, 1)
            
            points.append((x_rounded, y_rounded, 0.1))
        
        return points
    
    def get_segments_summary(self) -> Dict:
        """Get summary of detected segments"""
        if not self.segments:
            return {}
            
        total_segments = len(self.segments)
        avg_comp_x = np.mean([seg.compensation_vector_x for seg in self.segments])
        avg_comp_y = np.mean([seg.compensation_vector_y for seg in self.segments])
        
        return {
            "total_segments": total_segments,
            "average_comp_x": round(avg_comp_x, 2),
            "average_comp_y": round(avg_comp_y, 2),
            "max_horizontal_movement": max(abs(seg.vector_x) for seg in self.segments),
            "max_vertical_movement": max(abs(seg.vector_y) for seg in self.segments)
        }


__all__ = ["TrajectoryDetector", "TrajectorySegment"]
