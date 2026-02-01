from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import timedelta
import os

from models import (
    UserLogin, UserCreate, User, Token,
    VehicleCreate, Vehicle,
    CargoCreate, Cargo,
    LoadPlanCreate, LoadPlanAnalyze, LoadPlan, LoadPlanDetail,
    PhysicsResult, CargoPlacement, CargoPlacementResponse
)
from database import db
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, security, ACCESS_TOKEN_EXPIRE_MINUTES
)
from physics_engine import PhysicsEngine

app = FastAPI(
    title="Load Planning System API",
    description="Center-of-Gravity–Aware Load Planning System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

physics_engine = PhysicsEngine()

# ==================== AUTH ENDPOINTS ====================

@app.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Authenticate user and return JWT token"""
    with db.get_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (user_login.email,)
        )
        user = cursor.fetchone()
        
        if not user or not verify_password(user_login.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(user['user_id']),
                "email": user['email'],
                "role": user['role']
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user['user_id'],
                "name": user['name'],
                "email": user['email'],
                "role": user['role'],
                "created_at": user['created_at']
            }
        }

@app.post("/auth/register", response_model=User)
async def register(user_create: UserCreate):
    """Register a new user"""
    with db.get_cursor() as cursor:
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_create.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        password_hash = get_password_hash(user_create.password)
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id, name, email, role, created_at
            """,
            (user_create.name, user_create.email, password_hash, user_create.role)
        )
        new_user = cursor.fetchone()
        
        return new_user

@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    with db.get_cursor() as cursor:
        cursor.execute(
            "SELECT user_id, name, email, role, created_at FROM users WHERE user_id = %s",
            (int(current_user['sub']),)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user

# ==================== VEHICLE ENDPOINTS ====================

@app.get("/vehicles", response_model=List[Vehicle])
async def get_vehicles(current_user: dict = Depends(get_current_user)):
    """Get all vehicles"""
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM vehicles ORDER BY created_at DESC")
        vehicles = cursor.fetchall()
        return vehicles

@app.get("/vehicles/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific vehicle"""
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
        vehicle = cursor.fetchone()
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return vehicle

@app.post("/vehicles", response_model=Vehicle)
async def create_vehicle(vehicle: VehicleCreate, current_user: dict = Depends(get_current_user)):
    """Create a new vehicle"""
    with db.get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO vehicles (vehicle_type, max_load, length, width, height)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (vehicle.vehicle_type, vehicle.max_load, vehicle.length, vehicle.width, vehicle.height)
        )
        new_vehicle = cursor.fetchone()
        return new_vehicle

@app.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a vehicle"""
    with db.get_cursor() as cursor:
        cursor.execute("DELETE FROM vehicles WHERE vehicle_id = %s RETURNING vehicle_id", (vehicle_id,))
        deleted = cursor.fetchone()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return {"message": "Vehicle deleted successfully"}

# ==================== CARGO ENDPOINTS ====================

@app.get("/cargo", response_model=List[Cargo])
async def get_cargo(current_user: dict = Depends(get_current_user)):
    """Get all cargo items"""
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM cargo ORDER BY created_at DESC")
        cargo_items = cursor.fetchall()
        return cargo_items

@app.get("/cargo/{cargo_id}", response_model=Cargo)
async def get_cargo_item(cargo_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific cargo item"""
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM cargo WHERE cargo_id = %s", (cargo_id,))
        cargo = cursor.fetchone()
        
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo not found")
        
        return cargo

@app.post("/cargo", response_model=Cargo)
async def create_cargo(cargo: CargoCreate, current_user: dict = Depends(get_current_user)):
    """Create a new cargo item"""
    with db.get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO cargo (name, weight, length, width, height)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (cargo.name, cargo.weight, cargo.length, cargo.width, cargo.height)
        )
        new_cargo = cursor.fetchone()
        return new_cargo

@app.delete("/cargo/{cargo_id}")
async def delete_cargo(cargo_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a cargo item"""
    with db.get_cursor() as cursor:
        cursor.execute("DELETE FROM cargo WHERE cargo_id = %s RETURNING cargo_id", (cargo_id,))
        deleted = cursor.fetchone()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Cargo not found")
        
        return {"message": "Cargo deleted successfully"}

# ==================== LOAD PLAN ENDPOINTS ====================

@app.post("/load-plan/generate", response_model=LoadPlanDetail)
async def generate_load_plan(plan_create: LoadPlanCreate, current_user: dict = Depends(get_current_user)):
    """Generate an optimized load plan"""
    with db.get_cursor() as cursor:
        # Get vehicle
        cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (plan_create.vehicle_id,))
        vehicle = cursor.fetchone()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Get cargo items
        if not plan_create.cargo_items:
            raise HTTPException(status_code=400, detail="No cargo items provided")
        
        cursor.execute(
            "SELECT * FROM cargo WHERE cargo_id = ANY(%s)",
            (plan_create.cargo_items,)
        )
        cargo_items = cursor.fetchall()
        
        if len(cargo_items) != len(plan_create.cargo_items):
            raise HTTPException(status_code=404, detail="Some cargo items not found")
        
        # Optimize placement
        placements = physics_engine.optimize_placement(cargo_items, vehicle)
        
        # Analyze load
        analysis = physics_engine.analyze_load(placements, cargo_items, vehicle)
        
        # Create load plan
        cursor.execute(
            """
            INSERT INTO load_plans (user_id, vehicle_id, stability_score, 
                                   center_of_gravity_x, center_of_gravity_y, center_of_gravity_z, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                int(current_user['sub']),
                plan_create.vehicle_id,
                analysis['stability_score'],
                analysis['center_of_gravity']['x'],
                analysis['center_of_gravity']['y'],
                analysis['center_of_gravity']['z'],
                'approved' if analysis['is_safe'] else 'draft'
            )
        )
        load_plan = cursor.fetchone()
        
        # Insert placements
        placement_results = []
        for placement in placements:
            cursor.execute(
                """
                INSERT INTO cargo_placements (plan_id, cargo_id, position_x, position_y, position_z, rotation)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    load_plan['plan_id'],
                    placement['cargo_id'],
                    placement['position_x'],
                    placement['position_y'],
                    placement['position_z'],
                    placement.get('rotation', 0)
                )
            )
            placement_result = cursor.fetchone()
            
            # Get cargo details
            cargo = next((c for c in cargo_items if c['cargo_id'] == placement['cargo_id']), None)
            placement_result['cargo'] = cargo
            placement_results.append(placement_result)
        
        return {
            **load_plan,
            'vehicle': vehicle,
            'placements': placement_results
        }

@app.post("/load-plan/analyze", response_model=PhysicsResult)
async def analyze_load_plan(plan_analyze: LoadPlanAnalyze, current_user: dict = Depends(get_current_user)):
    """Analyze an existing or custom load configuration"""
    with db.get_cursor() as cursor:
        # Get vehicle
        cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (plan_analyze.vehicle_id,))
        vehicle = cursor.fetchone()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Get cargo items
        cargo_ids = [p.cargo_id for p in plan_analyze.placements]
        cursor.execute("SELECT * FROM cargo WHERE cargo_id = ANY(%s)", (cargo_ids,))
        cargo_items = cursor.fetchall()
        
        # Convert placements to dict format
        placements = [p.dict() for p in plan_analyze.placements]
        
        # Analyze
        analysis = physics_engine.analyze_load(placements, cargo_items, vehicle)
        
        return analysis

@app.get("/load-plan", response_model=List[LoadPlan])
async def get_load_plans(current_user: dict = Depends(get_current_user)):
    """Get all load plans for current user"""
    with db.get_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM load_plans WHERE user_id = %s ORDER BY created_at DESC",
            (int(current_user['sub']),)
        )
        plans = cursor.fetchall()
        return plans

@app.get("/load-plan/{plan_id}", response_model=LoadPlanDetail)
async def get_load_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific load plan with details"""
    with db.get_cursor() as cursor:
        # Get plan
        cursor.execute("SELECT * FROM load_plans WHERE plan_id = %s", (plan_id,))
        plan = cursor.fetchone()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Load plan not found")
        
        # Get vehicle
        cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (plan['vehicle_id'],))
        vehicle = cursor.fetchone()
        
        # Get placements with cargo details
        cursor.execute(
            """
            SELECT cp.*, c.*
            FROM cargo_placements cp
            JOIN cargo c ON cp.cargo_id = c.cargo_id
            WHERE cp.plan_id = %s
            """,
            (plan_id,)
        )
        placements = cursor.fetchall()
        
        # Format placements
        formatted_placements = []
        for p in placements:
            formatted_placements.append({
                'placement_id': p['placement_id'],
                'cargo_id': p['cargo_id'],
                'position_x': p['position_x'],
                'position_y': p['position_y'],
                'position_z': p['position_z'],
                'rotation': p['rotation'],
                'cargo': {
                    'cargo_id': p['cargo_id'],
                    'name': p['name'],
                    'weight': p['weight'],
                    'length': p['length'],
                    'width': p['width'],
                    'height': p['height'],
                    'created_at': p['created_at']
                }
            })
        
        return {
            **plan,
            'vehicle': vehicle,
            'placements': formatted_placements
        }

@app.delete("/load-plan/{plan_id}")
async def delete_load_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a load plan"""
    with db.get_cursor() as cursor:
        cursor.execute(
            "DELETE FROM load_plans WHERE plan_id = %s AND user_id = %s RETURNING plan_id",
            (plan_id, int(current_user['sub']))
        )
        deleted = cursor.fetchone()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Load plan not found")
        
        return {"message": "Load plan deleted successfully"}

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Load Planning System"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
