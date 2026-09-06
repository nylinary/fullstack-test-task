"""HTTP endpoints for the alert feed."""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.application.use_cases.manage_files import ListAlertsUseCase
from src.presentation.http.dependencies import PageDep, provide_list_alerts
from src.presentation.http.schemas import AlertItem

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertItem])
async def list_alerts(
    page: PageDep,
    use_case: Annotated[ListAlertsUseCase, Depends(provide_list_alerts)],
) -> list[AlertItem]:
    alerts = await use_case.execute(page)
    return [AlertItem.model_validate(alert) for alert in alerts]
