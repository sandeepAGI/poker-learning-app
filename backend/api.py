# backend/api.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import uvicorn

# Import routers
from routers import games, players, learning

# Import error handlers
from utils.errors import (
    PokerAppError, 
    poker_app_exception_handler, 
    validation_exception_handler,
    generic_exception_handler
)

# Create FastAPI app instance
app = FastAPI(
    title="Poker Learning App API",
    description="API for the Poker Learning App",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(PokerAppError, poker_app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(games.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(learning.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Poker Learning App API"}

# Run the application
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)