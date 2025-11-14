import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.utils import set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    모든 요청에 대해 고유한 request_id를 생성하고 
    Request.state와 logging context에 저장하는 미들웨어
    Spring의 MDC처럼 동작하여 모든 로그에 자동으로 request_id가 포함됨
    """
    
    async def dispatch(self, request: Request, call_next):
        # UUID 기반 고유한 request_id 생성
        request_id = str(uuid.uuid4())
        
        # Request.state에 저장 (모든 엔드포인트에서 접근 가능)
        request.state.request_id = request_id
        
        # ContextVar에 저장 (모든 로그에 자동으로 포함됨, MDC처럼 동작)
        set_request_id(request_id)
        
        # 응답 헤더에 request_id 추가
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response

