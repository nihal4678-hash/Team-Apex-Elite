from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class EcoMindException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ResourceNotFoundException(EcoMindException):
    def __init__(self, resource_name: str, resource_id: str):
        super().__init__(
            message=f"{resource_name} with ID '{resource_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationException(EcoMindException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(EcoMindException)
    async def ecomind_exception_handler(request: Request, exc: EcoMindException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "message": exc.message,
                    "status_code": exc.status_code,
                    "path": request.url.path,
                }
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "message": "An unexpected internal server error occurred.",
                    "detail": str(exc),
                    "status_code": 500,
                    "path": request.url.path,
                }
            }
        )
