from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"ok": True, "service": "eldoctor-fastapi"}


@router.get("/docs-link")
def docs_link():
    return {"openapi": "/docs"}
