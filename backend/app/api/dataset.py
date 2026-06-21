from fastapi import APIRouter

from backend.app.services.dataset_service import dataset_artifact_summary

router = APIRouter()


@router.get("")
def read_dataset_summary() -> dict[str, object]:
    return dataset_artifact_summary()
