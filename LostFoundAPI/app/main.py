from fastapi import FastAPI
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
