from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List
from datetime import timedelta
import os

from models import (
    UserLogin, UserCreate, User, Token,
    VehicleCreate, Vehicle,
    CargoCreate, Cargo,
    LoadPlanCreate, LoadPlanDetail,
)
from database import db
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from physics_engine import PhysicsEngine

app = FastAPI(
    title="Load Planning System API",
    description="Center-of-Gravity–Aware Load Planning System",
    version="1.0.0"
)

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

physics_engine = PhysicsEngine()

# ================= WEBSITE =================

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Load Balance AI</title>
        <style>
            body { font-family: Arial; background:#0f172a; color:white; text-align:center; }
            .card { background:#111827; padding:30px; margin:50px auto; width:500px; border-radius:12px; }
            a { color:#38bdf8; text-decoration:none; font-size:18px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚚 Load Balance AI</h1>
            <p>Center-of-Gravity Aware Load Planning System</p>
            <p><a href="/docs">📘 API Documentation</a></p>
            <p><a href="/health">🟢 Health Check</a></p>
        </div>
    </body>
    </html>
    """

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return {}

# ================= AUTH =================

@app.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email=%s", (user_login.email,))
        user = cursor.fetchone()

        if not user or not verify_password(user_login.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        access_token = create_access_token(
            data={"sub": str(user["user_id"]), "email": user["email"], "role": user["role"]},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.post("/auth/register", response_model=User)
async def register(user_create: UserCreate):
    with db.get_cursor() as cursor:
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (user_create.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        password_hash = get_password_hash(user_create.password)
        cursor.execute(
            """
            INSERT INTO users (name,email,password_hash,role)
            VALUES (%s,%s,%s,%s)
            RETURNING user_id,name,email,role,created_at
            """,
            (user_create.name, user_create.email, password_hash, user_create.role)
        )
        return cursor.fetchone()


@app.get("/auth/me", response_model=User)
async def me(current_user: dict = Depends(get_current_user)):
    with db.get_cursor() as cursor:
        cursor.execute(
            "SELECT user_id,name,email,role,created_at FROM users WHERE user_id=%s",
            (int(current_user["sub"]),)
        )
        return cursor.fetchone()

# ================= VEHICLES =================

@app.get("/vehicles", response_model=List[Vehicle])
async def get_vehicles(current_user: dict = Depends(get_current_user)):
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM vehicles ORDER BY created_at DESC")
        return cursor.fetchall()


@app.post("/vehicles", response_model=Vehicle)
async def create_vehicle(vehicle: VehicleCreate, current_user: dict = Depends(get_current_user)):
    with db.get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO vehicles (vehicle_type,max_load,length,width,height)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING *
            """,
            (vehicle.vehicle_type, vehicle.max_load, vehicle.length, vehicle.width, vehicle.height)
        )
        return cursor.fetchone()

# ================= CARGO =================

@app.get("/cargo", response_model=List[Cargo])
async def get_cargo(current_user: dict = Depends(get_current_user)):
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM cargo ORDER BY created_at DESC")
        return cursor.fetchall()


@app.post("/cargo", response_model=Cargo)
async def create_cargo(cargo: CargoCreate, current_user: dict = Depends(get_current_user)):
    with db.get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO cargo (name,weight,length,width,height)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING *
            """,
            (cargo.name, cargo.weight, cargo.length, cargo.width, cargo.height)
        )
        return cursor.fetchone()

# ================= LOAD PLAN =================

@app.post("/load-plan/generate", response_model=LoadPlanDetail)
async def generate_plan(plan: LoadPlanCreate, current_user: dict = Depends(get_current_user)):
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM vehicles WHERE vehicle_id=%s", (plan.vehicle_id,))
        vehicle = cursor.fetchone()

        cursor.execute("SELECT * FROM cargo WHERE cargo_id = ANY(%s)", (plan.cargo_items,))
        cargo_items = cursor.fetchall()

        placements = physics_engine.optimize_placement(cargo_items, vehicle)
        analysis = physics_engine.analyze_load(placements, cargo_items, vehicle)

        cursor.execute(
            """
            INSERT INTO load_plans (user_id,vehicle_id,stability_score,
            center_of_gravity_x,center_of_gravity_y,center_of_gravity_z,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
            """,
            (
                int(current_user["sub"]),
                plan.vehicle_id,
                analysis["stability_score"],
                analysis["center_of_gravity"]["x"],
                analysis["center_of_gravity"]["y"],
                analysis["center_of_gravity"]["z"],
                "approved" if analysis["is_safe"] else "draft",
            )
        )
        return cursor.fetchone()

# ================= HEALTH =================

@app.get("/health")
async def health():
    return {"status": "healthy"}

# ================= START =================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
