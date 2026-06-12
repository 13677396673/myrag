"""数据集路由 — CRUD

/datasets/*
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import Container, get_container, get_current_user_id
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.dataset import (
    DatasetCreateRequest,
    DatasetUpdateRequest,
)
from app.services.dataset_service import (
    DatasetNotFound,
    DatasetPermissionDenied,
)

router = APIRouter(prefix="/datasets", tags=["数据集"])


@router.get("", response_model=ApiResponse)
async def list_datasets(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取数据集列表（分页）"""
    items, total = await container.dataset_service.list_datasets(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    paginated = PaginatedResponse.build(
        items=[item.model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(code=200, message="success", data=paginated.model_dump())


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    request: DatasetCreateRequest,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """创建数据集"""
    dataset = await container.dataset_service.create(
        request, user_id=user_id
    )
    return ApiResponse(
        code=201, message="数据集创建成功", data=dataset.model_dump()
    )


@router.get("/{dataset_id}", response_model=ApiResponse)
async def get_dataset(
    dataset_id: str,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取数据集详情"""
    try:
        dataset = await container.dataset_service.get_dataset(
            dataset_id, user_id=user_id
        )
        return ApiResponse(
            code=200, message="success", data=dataset.model_dump()
        )
    except DatasetNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
    except DatasetPermissionDenied as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.message
        )


@router.put("/{dataset_id}", response_model=ApiResponse)
async def update_dataset(
    dataset_id: str,
    request: DatasetUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """更新数据集信息"""
    try:
        dataset = await container.dataset_service.update_dataset(
            dataset_id, request, user_id=user_id
        )
        return ApiResponse(
            code=200, message="更新成功", data=dataset.model_dump()
        )
    except DatasetNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
    except DatasetPermissionDenied as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.message
        )


@router.delete("/{dataset_id}", response_model=ApiResponse)
async def delete_dataset(
    dataset_id: str,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """删除数据集（级联删除关联文档与切片）"""
    try:
        await container.dataset_service.delete_dataset(
            dataset_id, user_id=user_id
        )
        return ApiResponse(code=200, message="数据集已删除")
    except DatasetNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
    except DatasetPermissionDenied as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.message
        )
