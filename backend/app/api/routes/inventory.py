from fastapi import APIRouter

from app.api.deps import AdminUser, InventoryServiceDep

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("")
def inventory(_: AdminUser, svc: InventoryServiceDep):
    return svc.summary()


@router.get("/low-stock")
def low_stock(_: AdminUser, svc: InventoryServiceDep):
    return svc.low_stock()
