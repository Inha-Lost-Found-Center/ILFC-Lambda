from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app.controller import items as items_router
from app.controller import users as users_router
from app.controller import tags as tags_router
from app.controller import kiosks as kiosks_router

app = FastAPI(
    title="Inha LostFound API",
    version="0.1.0",
    openapi_prefix="/main",
    openapi_url="/openapi.json"
)

origins = [
    "http://localhost:5173",             # React 개발 서버 주소
    "https://jong-sul-indol.vercel.app/", # 분실물센터 Web 배포 주소
    "https://main.d2uqv8vbmzw3om.amplifyapp.com" # 관리자 Web 배포 주소
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTPException이 발생했을 때,
    CORS 헤더를 포함하여 응답을 반환하는 커스텀 핸들러
    """
    origin = request.headers.get('origin')

    # 기본 에러 응답 생성
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

    # 요청한 origin이 허용된 origins 리스트에 있다면,
    # 해당 origin을 Access-Control-Allow-Origin 헤더에 추가
    if origin in origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'

    return response

# 헬스 체크용 엔드포인트
@app.get("/health_check")
def read_root():
    return {"message": "Welcome to the LostFoundAPI"}


# 컨트롤러(라우터) 포함
app.include_router(items_router.router, prefix="/items", tags=["Items"])
app.include_router(users_router.router, prefix="/users", tags=["Users"])
app.include_router(tags_router.router, prefix="/tags", tags=["Tags"])
app.include_router(kiosks_router.router, prefix="/kiosk", tags=["Kiosk"])

handler = Mangum(app)
