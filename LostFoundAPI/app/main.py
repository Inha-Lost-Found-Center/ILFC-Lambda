from fastapi import FastAPI
from mangum import Mangum

from app.controller import items as items_router
from app.controller import users as users_router
from app.controller import tags as tags_router

app = FastAPI(
    title="Inha LostFound API",
    version="0.1.0",
    root_path="/web"
)

# 2. (임시) 루트 경로에 헬스 체크용 엔드포인트 추가
@app.get("/")
def read_root():
    return {"message": "Welcome to the LostFoundAPI"}


# 3. (향후 확장) 컨트롤러(라우터) 포함
# 예시: app.include_router(items_router, prefix="/items", tags=["Items"])
app.include_router(items_router.router, prefix="/items", tags=["Items"])
app.include_router(users_router.router, prefix="/users", tags=["Users"])
app.include_router(tags_router.router, prefix="/tags", tags=["Tags"])

# 4. (매우 중요) Mangum 핸들러 생성
# AWS Lambda가 'handler'라는 이름의 이 객체를 호출하여
# FastAPI 앱으로 요청을 전달합니다.
handler = Mangum(app)
