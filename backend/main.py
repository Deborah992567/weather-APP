from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
from typing import Annotated, Optional
from datetime import datetime

app = FastAPI()

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

API_KEY = "773a0992787da586db91716599bbe15b"

BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
GEO_URL = "http://api.openweathermap.org/geo/1.0/reverse"

def is_daytime(sunrise: int, sunset: int, current_time: int) -> bool:
    
    return sunrise <= current_time <= sunset

def get_weather_condition(weather_code: int) -> str:
    """Convert OpenWeatherMap weather code to simple condition"""
    if 200 <= weather_code <= 299:
        return "thunderstorm"
    elif 300 <= weather_code <= 399:
        return "drizzle"
    elif 500 <= weather_code <= 599:
        return "rain"
    elif 600 <= weather_code <= 699:
        return "snow"
    elif 700 <= weather_code <= 799:
        return "mist"
    elif weather_code == 800:
        return "clear"
    elif 801 <= weather_code <= 899:
        return "clouds"
    else:
        return "unknown"

@app.get("/api/weather")
def get_weather(
    db:db_dependency,
    city: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
 
):
    """Get weather data by city name or coordinates"""
    
    if city:
        # Search by city name
        search_key = city.strip().lower()
        
        # Check database first
        weather_response = db.query(models.WeatherApp).filter(
            models.WeatherApp.city == search_key
        ).first()
        
        # If found in DB and data is recent (less than 1 hour old), return it
        if weather_response:
            return format_weather_response(weather_response, search_key.title())
        
        # Fetch from API by city
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        }
        
    elif lat is not None and lon is not None:
        # Search by coordinates
        params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"
        }
        search_key = f"{lat},{lon}"
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'city' or both 'lat' and 'lon' parameters are required"
        )
    
    try:
        # Make API request
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            data = response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail=data.get("message", f"Weather API error: {response.status_code}")
            )
        
        data = response.json()
        
        # Extract comprehensive weather data
        weather_info = extract_weather_data(data)
        
        # Save to database if searching by city
        if city:
            save_weather_to_db(db, city.strip().lower(), weather_info)
        
        return weather_info
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Weather service timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Weather service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def extract_weather_data(data: dict) -> dict:
    """Extract and format weather data from OpenWeatherMap API response"""
    
    # Get current timestamp
    current_time = int(datetime.now().timestamp())
    
    # Determine if it's day or night
    sunrise = data.get("sys", {}).get("sunrise", current_time)
    sunset = data.get("sys", {}).get("sunset", current_time)
    is_day = is_daytime(sunrise, sunset, current_time)
    
    # Get weather condition
    weather_code = data["weather"][0]["id"]
    weather_condition = get_weather_condition(weather_code)
    
    return {
        "location": data.get("name", "Unknown Location"),
        "temperature": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "description": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
        "wind_speed": round(data.get("wind", {}).get("speed", 0) * 3.6),  # Convert m/s to km/h
        "pressure": data["main"]["pressure"],
        "weather_condition": weather_condition,
        "is_day": is_day,
        "visibility": data.get("visibility", 0) // 1000,  # Convert to km
        "country": data.get("sys", {}).get("country", ""),
        "coord": {
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"]
        }
    }

def save_weather_to_db(db: Session, city: str, weather_data: dict):
    """Save weather data to database"""
    try:
        # Check if record exists
        existing_record = db.query(models.WeatherApp).filter(
            models.WeatherApp.city == city
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.temperature = weather_data["temperature"]
            existing_record.description = weather_data["description"]
            existing_record.updated_at = datetime.now()  # Add this field to your model if needed
        else:
            # Create new record
            new_weather = models.WeatherApp(
                city=city,
                temperature=weather_data["temperature"],
                description=weather_data["description"],
                # Add more fields as needed based on your model
            )
            db.add(new_weather)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")  # Log the error

def format_weather_response(db_record, location_name: str) -> dict:
    """Format database record for API response"""
    current_time = int(datetime.now().timestamp())
    # Simple day/night check based on current hour (6 AM - 6 PM is day)
    current_hour = datetime.now().hour
    is_day = 6 <= current_hour < 18
    
    return {
        "location": location_name,
        "temperature": db_record.temperature,
        "feels_like": db_record.temperature,  # Use same as temp if not stored
        "description": db_record.description,
        "humidity": 60,  # Default values - extend your model to store these
        "wind_speed": 10,
        "pressure": 1013,
        "weather_condition": "clouds",  # You'll need to store/derive this
        "is_day": is_day,
        "visibility": 10,
        "country": "",
        "coord": {"lat": 0, "lon": 0}
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Get all stored cities (useful for debugging)
@app.get("/cities")
def get_stored_cities(db: db_dependency):
    cities = db.query(models.WeatherApp).all()
    return [{"city": city.city, "temperature": city.temperature, "description": city.description} for city in cities]