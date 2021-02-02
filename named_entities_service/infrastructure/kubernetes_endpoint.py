from fastapi import APIRouter

router = APIRouter()


@router.get('/healthz', status_code=200)
async def health_check():
    return {"status": "UP"}


@router.get('/ready', status_code=200)
async def ready_check():
    return {"ready": True}


@router.get('/info', status_code=200)
async def info_endpoint():
    return {'app': {'name': 'named--entities-service', 'version': '0.1.0.dev85'}}
