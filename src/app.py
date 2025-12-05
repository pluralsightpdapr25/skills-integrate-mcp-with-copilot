"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import json
import threading

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory (static lives under `src/static`)
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# Data file for persistent activities (repository root `data/activities.json`)
DATA_FILE = current_dir.parent / "data" / "activities.json"
_lock = threading.Lock()


def load_activities():
    """Load activities from the JSON data file. Returns dict."""
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # If file is corrupted, return empty dict so server still runs
            return {}
    return {}


def save_activities(data: dict):
    """Persist activities to the JSON data file."""
    # Ensure parent dir exists
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        with DATA_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# Load activities at startup from the data file
activities = load_activities()



@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    # Persist change
    try:
        save_activities(activities)
    except Exception:
        # If saving fails, still return success but log would be ideal
        pass
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    # Persist change
    try:
        save_activities(activities)
    except Exception:
        pass
    return {"message": f"Unregistered {email} from {activity_name}"}
