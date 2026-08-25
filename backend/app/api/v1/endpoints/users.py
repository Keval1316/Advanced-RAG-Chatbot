from fastapi import APIRouter, Depends, status
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.common import APIResponse
from backend.app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve profile of the currently logged-in user"
)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> APIResponse[UserResponse]:
    return APIResponse(
        success=True,
        message="Current user profile retrieved successfully.",
        data=UserResponse.model_validate(current_user)
    )
