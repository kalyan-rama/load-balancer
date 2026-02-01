import numpy as np
from typing import List, Dict, Tuple
from scipy.optimize import minimize

class PhysicsEngine:
    """
    Physics engine for calculating center of gravity, stability, and torque
    """
    
    @staticmethod
    def calculate_center_of_gravity(placements: List[Dict], cargo_data: List[Dict]) -> Dict[str, float]:
        """
        Calculate the center of gravity for all cargo items
        
        Args:
            placements: List of cargo placements with position data
            cargo_data: List of cargo items with weight and dimensions
            
        Returns:
            Dictionary with x, y, z coordinates of center of gravity
        """
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        weighted_z = 0
        
        cargo_dict = {c['cargo_id']: c for c in cargo_data}
        
        for placement in placements:
            cargo = cargo_dict.get(placement['cargo_id'])
            if not cargo:
                continue
                
            weight = cargo['weight']
            # Calculate center of each cargo item
            center_x = placement['position_x'] + cargo['length'] / 2
            center_y = placement['position_y'] + cargo['width'] / 2
            center_z = placement['position_z'] + cargo['height'] / 2
            
            weighted_x += center_x * weight
            weighted_y += center_y * weight
            weighted_z += center_z * weight
            total_weight += weight
        
        if total_weight == 0:
            return {'x': 0, 'y': 0, 'z': 0}
        
        return {
            'x': weighted_x / total_weight,
            'y': weighted_y / total_weight,
            'z': weighted_z / total_weight
        }
    
    @staticmethod
    def calculate_stability_score(cog: Dict[str, float], vehicle: Dict) -> float:
        """
        Calculate stability score based on center of gravity position
        
        Score: 0-100 where 100 is most stable
        
        Args:
            cog: Center of gravity coordinates
            vehicle: Vehicle dimensions
            
        Returns:
            Stability score (0-100)
        """
        # Ideal center of gravity is at the geometric center
        ideal_x = vehicle['length'] / 2
        ideal_y = vehicle['width'] / 2
        ideal_z = vehicle['height'] / 2
        
        # Calculate deviations from ideal
        dev_x = abs(cog['x'] - ideal_x) / ideal_x if ideal_x > 0 else 0
        dev_y = abs(cog['y'] - ideal_y) / ideal_y if ideal_y > 0 else 0
        dev_z = abs(cog['z'] - ideal_z) / ideal_z if ideal_z > 0 else 0
        
        # Weight deviations (lateral and vertical are more critical)
        weighted_deviation = (dev_x * 0.3 + dev_y * 0.5 + dev_z * 0.2)
        
        # Convert to score (lower deviation = higher score)
        score = max(0, 100 - (weighted_deviation * 100))
        
        return round(score, 2)
    
    @staticmethod
    def calculate_torque(placements: List[Dict], cargo_data: List[Dict], 
                        cog: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate torque around the center of gravity
        
        Args:
            placements: List of cargo placements
            cargo_data: List of cargo items
            cog: Center of gravity
            
        Returns:
            Dictionary with torque values for each axis
        """
        cargo_dict = {c['cargo_id']: c for c in cargo_data}
        
        torque_x = 0
        torque_y = 0
        torque_z = 0
        
        for placement in placements:
            cargo = cargo_dict.get(placement['cargo_id'])
            if not cargo:
                continue
            
            weight = cargo['weight']
            
            # Position of cargo center
            pos_x = placement['position_x'] + cargo['length'] / 2
            pos_y = placement['position_y'] + cargo['width'] / 2
            pos_z = placement['position_z'] + cargo['height'] / 2
            
            # Distance from COG
            r_x = pos_x - cog['x']
            r_y = pos_y - cog['y']
            r_z = pos_z - cog['z']
            
            # Torque = r × F (simplified for vertical force)
            torque_x += r_y * weight  # Pitch
            torque_y += r_x * weight  # Roll
            torque_z += (r_x * r_y) * weight  # Yaw (simplified)
        
        return {
            'pitch': abs(torque_x),
            'roll': abs(torque_y),
            'yaw': abs(torque_z)
        }
    
    @staticmethod
    def generate_warnings(cog: Dict[str, float], stability_score: float, 
                         torque: Dict[str, float], vehicle: Dict,
                         total_weight: float) -> List[str]:
        """
        Generate safety warnings based on physics analysis
        
        Args:
            cog: Center of gravity
            stability_score: Calculated stability score
            torque: Torque analysis
            vehicle: Vehicle data
            total_weight: Total cargo weight
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Weight warning
        if total_weight > vehicle['max_load']:
            warnings.append(f"CRITICAL: Total weight ({total_weight:.2f} kg) exceeds vehicle capacity ({vehicle['max_load']:.2f} kg)")
        elif total_weight > vehicle['max_load'] * 0.9:
            warnings.append(f"WARNING: Load is at {(total_weight/vehicle['max_load']*100):.1f}% of capacity")
        
        # Stability warning
        if stability_score < 50:
            warnings.append("CRITICAL: Poor stability - load is dangerously unbalanced")
        elif stability_score < 70:
            warnings.append("WARNING: Suboptimal stability - consider redistributing load")
        
        # Lateral balance warning (most critical)
        vehicle_center_y = vehicle['width'] / 2
        lateral_deviation = abs(cog['y'] - vehicle_center_y)
        if lateral_deviation > vehicle['width'] * 0.15:
            warnings.append("CRITICAL: Significant lateral imbalance detected - risk of tipping")
        
        # Longitudinal balance
        vehicle_center_x = vehicle['length'] / 2
        longitudinal_deviation = abs(cog['x'] - vehicle_center_x)
        if longitudinal_deviation > vehicle['length'] * 0.2:
            warnings.append("WARNING: Load is too far forward or backward")
        
        # Height warning
        if cog['z'] > vehicle['height'] * 0.6:
            warnings.append("WARNING: High center of gravity - reduced stability")
        
        # Torque warnings
        max_acceptable_torque = total_weight * vehicle['width'] * 0.1
        if torque['roll'] > max_acceptable_torque:
            warnings.append("WARNING: Excessive rolling torque detected")
        if torque['pitch'] > max_acceptable_torque:
            warnings.append("WARNING: Excessive pitching torque detected")
        
        return warnings
    
    @staticmethod
    def optimize_placement(cargo_items: List[Dict], vehicle: Dict) -> List[Dict]:
        """
        Optimize cargo placement using a greedy algorithm
        
        Args:
            cargo_items: List of cargo to place
            vehicle: Vehicle specifications
            
        Returns:
            List of optimized placements
        """
        # Sort cargo by weight (heaviest first)
        sorted_cargo = sorted(cargo_items, key=lambda x: x['weight'], reverse=True)
        
        placements = []
        
        # Start placing from the bottom center
        current_x = 0
        current_y = 0
        current_z = 0
        max_row_height = 0
        
        vehicle_center_y = vehicle['width'] / 2
        
        for cargo in sorted_cargo:
            # Try to place near the center laterally
            target_y = vehicle_center_y - cargo['width'] / 2
            
            # Check if it fits in current row
            if current_x + cargo['length'] <= vehicle['length']:
                # Place in current row
                placements.append({
                    'cargo_id': cargo['cargo_id'],
                    'position_x': current_x,
                    'position_y': max(0, min(target_y, vehicle['width'] - cargo['width'])),
                    'position_z': current_z,
                    'rotation': 0
                })
                current_x += cargo['length']
                max_row_height = max(max_row_height, cargo['height'])
            else:
                # Start new row
                current_x = 0
                current_z += max_row_height
                max_row_height = cargo['height']
                
                placements.append({
                    'cargo_id': cargo['cargo_id'],
                    'position_x': current_x,
                    'position_y': max(0, min(target_y, vehicle['width'] - cargo['width'])),
                    'position_z': current_z,
                    'rotation': 0
                })
                current_x += cargo['length']
        
        return placements
    
    @staticmethod
    def analyze_load(placements: List[Dict], cargo_data: List[Dict], vehicle: Dict) -> Dict:
        """
        Complete load analysis
        
        Args:
            placements: Cargo placements
            cargo_data: Cargo specifications
            vehicle: Vehicle specifications
            
        Returns:
            Complete physics analysis
        """
        cog = PhysicsEngine.calculate_center_of_gravity(placements, cargo_data)
        stability_score = PhysicsEngine.calculate_stability_score(cog, vehicle)
        torque = PhysicsEngine.calculate_torque(placements, cargo_data, cog)
        
        total_weight = sum(c['weight'] for c in cargo_data)
        warnings = PhysicsEngine.generate_warnings(cog, stability_score, torque, vehicle, total_weight)
        
        is_safe = stability_score >= 70 and total_weight <= vehicle['max_load']
        
        return {
            'center_of_gravity': cog,
            'stability_score': stability_score,
            'torque_analysis': torque,
            'warnings': warnings,
            'is_safe': is_safe,
            'total_weight': total_weight
        }
