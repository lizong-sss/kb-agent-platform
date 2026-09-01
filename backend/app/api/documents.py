"""文档管理接口：上传、入库。需要登录后使用。"""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_current_user
from app.core.config import settings
from app.db import milvus
from app.models.user import User
from app.services.document.chunker import split_text
from app.services.document.parser import parse_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """上传文档：解析 → 分块 → 向量化 → 入库 Milvus。"""
    content = await file.read()
    filename = file.filename or "unnamed"

    try:
        text = parse_file(filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="文件解析后没有文本内容（可能是扫描件/图片PDF）")

    chunks = split_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="文件内容太短，无法切分出有效文本块")

    milvus.connect(settings.MILVUS_HOST, settings.MILVUS_PORT)
    inserted = milvus.insert_chunks(chunks, source=filename)

    return {
        "filename": filename,
        "total_chars": len(text),
        "chunk_count": len(chunks),
        "inserted": inserted,
    }
