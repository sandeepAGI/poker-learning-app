# backend/utils/errors.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

class PokerAppError(Exception):
    """Base exception for Poker App"""
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class GameNotFoundError(PokerAppError):
    """Game not found error"""
    def __init__(self, game_id: str):
        super().__init__(
            code="GAME_NOT_FOUND",
            message=f"Game session {game_id} not found",
            status_code=404
        )

class PlayerNotFoundError(PokerAppError):
    """Player not found error"""
    def __init__(self, player_id: str):
        super().__init__(
            code="PLAYER_NOT_FOUND",
            message=f"Player {player_id} not found",
            status_code=404
        )

class InvalidActionError(PokerAppError):
    """Invalid action error"""
    def __init__(self, message: str):
        super().__init__(
            code="INVALID_ACTION",
            message=message,
            status_code=400
        )

class NotYourTurnError(PokerAppError):
    """Not player's turn error"""
    def __init__(self, player_id: str):
        super().__init__(
            code="NOT_YOUR_TURN",
            message=f"It's not player {player_id}'s turn to act",
            status_code=403
        )

class InsufficientFundsError(PokerAppError):
    """Insufficient funds error"""
    def __init__(self, player_id: str, required: int, available: int):
        super().__init__(
            code="INSUFFICIENT_FUNDS",
            message=f"Player {player_id} has insufficient funds",
            status_code=400,
            details={
                "required": required,
                "available": available
            }
        )

class InvalidAmountError(PokerAppError):
    """Invalid bet amount error"""
    def __init__(self, message: str):
        super().__init__(
            code="INVALID_AMOUNT",
            message=message,
            status_code=400
        )

# Exception handlers
async def poker_app_exception_handler(request: Request, exc: PokerAppError):
    """Handler for PokerApp exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "code": "VALIDATION_ERROR",
            "message": "Validation error in request data",
            "details": exc.errors()
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handler for generic exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "code": "SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {"exception": str(exc)}
        }
    )