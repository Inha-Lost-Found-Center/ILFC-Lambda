from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    "http://localhost:5173", # React 개발 서버 주소
    "https://jong-sul-indol.vercel.app/" # 분실물센터 Web 배포 주소
    "https://main.d2uqv8vbmzw3om.amplifyapp.com" # 관리자 Web 배포 주소
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
