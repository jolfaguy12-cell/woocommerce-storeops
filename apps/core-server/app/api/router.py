from fastapi import APIRouter

from app.modules.auth.routes import router as auth_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.inventory.routes import router as inventory_router
from app.modules.notifications.routes import router as notifications_router
from app.modules.reports.routes import router as reports_router
from app.modules.users.routes import router as users_router
from app.modules.sync.routes import router as sync_router
from app.modules.products.routes import router as products_router
from app.modules.logs.routes import router as logs_router
from app.integrations.wordpress.routes import router as wordpress_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(sync_router, prefix="/sync", tags=["sync"])
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(logs_router, prefix="/logs", tags=["logs"])
api_router.include_router(wordpress_router, prefix="/wordpress", tags=["wordpress"])
