from fastapi import APIRouter
router = APIRouter(tags=["system"])
# TODO: migrate system endpoints (/healthz, /api/system/*, /api/cron/*)