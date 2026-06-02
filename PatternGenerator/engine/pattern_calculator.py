"""PatternCalculator Module - Handles pattern export and code generation"""

import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import sys
sys.path.insert(0, ".")
from engine.trajectory_detector import TrajectorySegment, TrajectoryDetector

@dataclass  
class PatternResult:
    """Complete pattern with metadata"""
    name: str
    weapon_type: str
    points: List[tuple]
    metadata: Dict[str, any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            "name": self.name,
            "weapon": self.weapon_type,
            "points": self.points,
            "metadata": self.metadata
        }

class PatternCalculator:
    """
    Handles final pattern calculation, validation, and export
    
    Responsible for:
    - Validating segment data
    - Generating Python code blocks
    - Exporting to JSON with metadata
    - Creating summary reports
    """
    
    def __init__(self):
        self.current_pattern = None
        self.validation_errors = []
        
    def calculate_pattern(self, segments: List[TrajectorySegment], 
                         weapon_type: str = "assault_rifle") -> PatternResult:
        """
        Calculate final pattern from detected segments
        
        Args:
            segments: List of TrajectorySegment objects
            weapon_type: Weapon type string (e.g., "assault_rifle", "m4a1s")
            
        Returns:
            PatternResult with all pattern data and metadata
        """
        print(f"Calculating pattern for weapon type: {weapon_type}")
        
        # Extract compensation points from segments
        points = []
        for segment in segments:
            # Add to points list
            point = (round(segment.compensation_vector_x, 1), 
                     round(segment.compensation_vector_y, 1),
                     0.1)  # Duration multiplier
            points.append(point)
        
        print(f"Total points generated: {len(points)}")
        
        # Validate pattern structure
        self._validate_pattern(points)
        
        # Create metadata dictionary
        metadata = {
            "source_type": "detected",
            "weapon_profile": weapon_type,
            "validation_status": len(self.validation_errors) == 0,
            "points_count": len(points),
            "average_movement": self._calculate_average_movement(points),
            "structure_score": self._calculate_structure_score(points)
        }
        
        # Generate unique name
        name = f"{weapon_type}_spray_generated"
        
        self.current_pattern = PatternResult(
            name=name,
            weapon_type=weapon_type,
            points=points,
            metadata=metadata
        )
        
        return self.current_pattern
    
    def _validate_pattern(self, points: List[tuple]):
        """Validate pattern structure and flag issues"""
        self.validation_errors = []
        
        if not points:
            self.validation_errors.append("Pattern is empty - no points detected")
            return
            
        # Check for extreme movements
        for i, point in enumerate(points):
            x, y = abs(point[0]), abs(point[1])
            if x > 150 or y > 100:
                self.validation_errors.append(f"Point {i} has extreme movement values")
                
        # Check minimum points required for useful pattern
        if len(points) < 5:
            self.validation_errors.append("Pattern has fewer than 5 points - may be incomplete")
        
        print(f"Validation errors (if any): {len(self.validation_errors)}")
    
    def _calculate_average_movement(self, points: List[tuple]) -> float:
        """Calculate average movement magnitude across all points"""
        if not points:
            return 0.0
            
        total_magnitude = sum(
            abs(point[0])**2 + abs(point[1])**2 
            for point in points
        ) ** 0.5
        return round(total_magnitude / len(points), 2)
    
    def _calculate_structure_score(self, points: List[tuple]) -> float:
        """Calculate structure score (how well pattern looks overall)"""
        if not points:
            return 0.0
        
        # Count horizontal and vertical movements
        horizontal_count = sum(1 for p in points if abs(p[0]) > 10)
        vertical_count = sum(1 for p in points if abs(p[1]) > 10)
        
        # Score based on pattern variety
        variety_score = min(horizontal_count * 0.3, vertical_count * 0.3, 1.0)
        return round(variety_score, 2)
    
    def export_to_json(self, pattern: PatternResult, output_path: str):
        """Export pattern to JSON file with proper formatting"""
        try:
            pattern_dict = pattern.to_dict()
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(pattern_dict, f, indent=2)
                
            print(f"Pattern saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return False
    
    def export_to_python(self, pattern: PatternResult, output_path: str, 
                        weapon_class_name: str = "self") -> str:
        """Export pattern as Python code block ready for weapon_data.py"""
        try:
            lines = [
                f"# Auto-generated anti-recoil pattern for {pattern.name}",
                f"# Format: (x_movement, y_movement, duration_multiplier)",
                "",
                f"{weapon_class_name}.{pattern.weapon_type} = ["
            ]
            
            for i, point in enumerate(pattern.points):
                lines.append(f"    ({point[0]}, {point[1]}, 0.1),")
            
            lines.append("]")
            
            # Write to file if path provided
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\\n".join(lines))
                
                print(f"Python code saved to: {output_path}")
            
            return "\\n".join(lines)
            
        except Exception as e:
            print(f"Error saving Python code: {e}")
            return ""
    
    def get_summary_report(self, pattern: PatternResult) -> Dict:
        """Generate detailed summary report for the pattern"""
        if not pattern or not pattern.points:
            return {}
            
        points = pattern.points
        
        # Calculate statistics
        x_values = [p[0] for p in points]
        y_values = [p[1] for p in points]
        
        stats = {
            "pattern_name": pattern.name,
            "weapon_type": pattern.weapon_type,
            "total_points": len(points),
            "structure_score": pattern.metadata.get("structure_score", 0),
            "average_movement_x": round(sum(x_values) / len(x_values), 2),
            "average_movement_y": round(sum(y_values) / len(y_values), 2),
            "max_horizontal": max(abs(x) for x in x_values),
            "max_vertical": max(abs(y) for y in y_values),
            "validation_passed": not pattern.metadata.get("validation_errors", [])
        }
        
        return stats
    
    def validate_pattern(self, pattern: PatternResult) -> bool:
        """Validate that pattern meets minimum requirements"""
        if not pattern:
            return False
        
        errors = pattern.metadata.get("validation_errors", [])
        return len(errors) == 0 and pattern.points is not None


__all__ = ["PatternCalculator", "PatternResult"]
