from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "operator"

class User(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    created_at: datetime

# Vehicle models
class VehicleCreate(BaseModel):
    vehicle_type: str
    max_load: float = Field(gt=0)
    length: float = Field(gt=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)

class Vehicle(BaseModel):
    vehicle_id: int
    vehicle_type: str
    max_load: float
    length: float
    width: float
    height: float
    created_at: datetime

# Cargo models
class CargoCreate(BaseModel):
    name: Optional[str] = None
    weight: float = Field(gt=0)
    length: float = Field(gt=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)

class Cargo(BaseModel):
    cargo_id: int
    name: Optional[str]
    weight: float
    length: float
    width: float
    height: float
    created_at: datetime

# Cargo placement models
class CargoPlacement(BaseModel):
    cargo_id: int
    position_x: float
    position_y: float
    position_z: float
    rotation: int = 0

class CargoPlacementResponse(CargoPlacement):
    placement_id: int
    cargo: Optional[Cargo] = None

# Load plan models
class LoadPlanCreate(BaseModel):
    vehicle_id: int
    cargo_items: List[int]  # List of cargo IDs

class LoadPlanAnalyze(BaseModel):
    vehicle_id: int
    placements: List[CargoPlacement]

class LoadPlan(BaseModel):
    plan_id: int
    user_id: int
    vehicle_id: int
    stability_score: Optional[float]
    center_of_gravity_x: Optional[float]
    center_of_gravity_y: Optional[float]
    center_of_gravity_z: Optional[float]
    status: str
    created_at: datetime

class LoadPlanDetail(LoadPlan):
    vehicle: Optional[Vehicle] = None
    placements: List[CargoPlacementResponse] = []

# Physics calculation result
class PhysicsResult(BaseModel):
    center_of_gravity: dict
    stability_score: float
    warnings: List[str]
    is_safe: bool
    torque_analysis: dict

# Token response
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
