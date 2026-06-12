"""文档路由 — 上传、列表、详情、删除、切片、状态

/datasets/{dataset_id}/documents/*
/documents/{id}/*
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.deps import Container, get_container, get_current_user_id
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.document_service import (
    DocumentNotFound,
    DocumentPermissionDenied,
    UnsupportedFileType,
)

router = APIRouter(tags=["文档"])


# ── 文档列表 ────────────────────────────────────────────────


@router.get(
    "/datasets/{dataset_id}/documents",
    response_model=ApiResponse,
)
async def list_documents(
    dataset_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取数据集下的文档列表（分页）"""
    result = await container.document_service.list_documents(
        dataset_id=dataset_id,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    paginated = PaginatedResponse.build(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )
    return ApiResponse(
        code=200, message="success", data=paginated.model_dump()
    )


# ── 文档上传 ────────────────────────────────────────────────


@router.post(
    "/datasets/{dataset_id}/documents",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    dataset_id: str,
    file: UploadFile = File(..., description="要上传的文件"),
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """上传文档到指定数据集

    支持格式: txt, md, pdf, docx, pptx, xlsx, png, jpg
    """
    try:
        content = await file.read()
        doc = await container.document_service.upload_document(
            user_id=user_id,
            dataset_id=dataset_id,
            filename=file.filename or "unknown",
            content=content,
        )
        return ApiResponse(
            code=201,
            message="文档上传成功，正在处理",
            data=doc.model_dump(),
        )
    except UnsupportedFileType as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        )


# ── 文档详情 ────────────────────────────────────────────────


@router.get("/documents/{document_id}", response_model=ApiResponse)
async def get_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取文档详情"""
    try:
        doc = await container.document_service.get_document(
            document_id, user_id=user_id
        )
        return ApiResponse(
            code=200, message="success", data=doc.model_dump()
        )
    except DocumentNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )


# ── 文档删除 ────────────────────────────────────────────────


@router.delete("/documents/{document_id}", response_model=ApiResponse)
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """删除文档"""
    try:
        await container.document_service.delete_document(
            document_id, user_id=user_id
        )
        return ApiResponse(code=200, message="文档已删除")
    except DocumentNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )


# ── 文档处理状态 ────────────────────────────────────────────


@router.get("/documents/{document_id}/status", response_model=ApiResponse)
async def get_document_status(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取文档处理状态"""
    try:
        status_info = await container.document_service.get_document_status(
            document_id, user_id=user_id
        )
        return ApiResponse(
            code=200, message="success", data=status_info.model_dump()
        )
    except DocumentNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )


# ── 文档切片列表 ────────────────────────────────────────────


@router.get("/documents/{document_id}/chunks", response_model=ApiResponse)
async def list_chunks(
    document_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=200, description="每页条数"),
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取文档的切片列表（分页）"""
    try:
        result = await container.document_service.list_chunks(
            doc_id=document_id,
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        paginated = PaginatedResponse.build(
            items=[item.model_dump() for item in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
        )
        return ApiResponse(
            code=200, message="success", data=paginated.model_dump()
        )
    except DocumentNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
