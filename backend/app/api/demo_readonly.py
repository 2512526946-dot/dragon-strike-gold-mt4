from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.demo_readonly_diagnostics import (
    DemoReadonlyDiagnosticsResponse,
    demo_readonly_diagnostics_internal_error_response,
    demo_readonly_diagnostics_response,
)
from app.services.demo_readonly_docs_fixture_validation_summary import (
    summarize_demo_readonly_docs_fixture_validation,
)


router = APIRouter(prefix="/api/demo-readonly", tags=["demo-readonly"])


@router.get("/diagnostics", response_model=DemoReadonlyDiagnosticsResponse)
def get_demo_readonly_diagnostics() -> (
    DemoReadonlyDiagnosticsResponse | JSONResponse
):
    try:
        summary = summarize_demo_readonly_docs_fixture_validation()
    except Exception:
        safe_response = demo_readonly_diagnostics_internal_error_response()
        return JSONResponse(
            status_code=500,
            content=safe_response.model_dump(),
        )

    return demo_readonly_diagnostics_response(summary)
