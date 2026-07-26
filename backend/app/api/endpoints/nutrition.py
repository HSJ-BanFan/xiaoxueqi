from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Path
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_current_user, get_db
from app.db.models import User, FoodNutrition
from app.models.nutrition import (
    FoodNutritionCreate, FoodNutritionUpdate, FoodNutrition as FoodNutritionModel,
    FoodNutritionPage, FoodNutritionImport, FoodNutritionImportResponse,
    FoodNutritionCategories, ImageUploadResponse
)
from app.services.nutrition import (
    create_food_nutrition, get_food_nutrition, get_food_nutrition_list,
    update_food_nutrition, delete_food_nutrition, import_food_nutrition_data,
    get_food_by_category, get_all_categories, get_diabetes_friendly_foods,
    get_low_gi_foods, get_foods_by_gi_range, search_foods,
    upload_food_image, delete_food_image
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=FoodNutritionModel)
def create_food(
    food_in: FoodNutritionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建食物营养记录
    """
    # 检查用户是否有管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能创建食物营养记录"
        )
    
    return create_food_nutrition(db=db, food_in=food_in)


@router.get("", response_model=FoodNutritionPage)
def read_foods(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    diabetes_friendly: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取食物营养记录列表
    """
    try:
        return get_food_nutrition_list(
            db=db,
            page=page,
            size=size,
            category=category,
            diabetes_friendly=diabetes_friendly,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except Exception as e:
        logger.error(f"获取食物列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取食物列表时发生内部错误"
        )


@router.get("/{food_id:int}", response_model=FoodNutritionModel)
def read_food(
    food_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取单个食物营养记录
    """
    food = get_food_nutrition(db=db, food_id=food_id)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食物记录不存在"
        )
    
    return food


@router.put("/{food_id:int}", response_model=FoodNutritionModel)
def update_food(
    food_id: int = Path(..., ge=1),
    food_in: FoodNutritionUpdate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新食物营养记录
    """
    # 检查用户是否有管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能更新食物营养记录"
        )
    
    food = update_food_nutrition(db=db, food_id=food_id, food_in=food_in)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食物记录不存在"
        )
    
    return food


@router.delete("/{food_id:int}", status_code=status.HTTP_200_OK)
def delete_food(
    food_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    删除食物营养记录
    """
    # 检查用户是否有管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能删除食物营养记录"
        )
    
    food = get_food_nutrition(db=db, food_id=food_id)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食物记录不存在"
        )
    
    # 如果有图片，删除图片
    if food.image_url:
        delete_food_image(food_id=food_id, image_url=food.image_url)
    
    success = delete_food_nutrition(db=db, food_id=food_id)
    
    return {"message": "食物营养记录已删除", "status": "success"}


@router.post("/import", response_model=FoodNutritionImportResponse)
def import_foods(
    import_data: FoodNutritionImport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    批量导入食物营养数据
    """
    # 检查用户是否有管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能导入食物营养数据"
        )
    
    try:
        imported_count, failed_count = import_food_nutrition_data(
            db=db, items=import_data.items
        )
        
        return FoodNutritionImportResponse(
            imported_count=imported_count,
            failed_count=failed_count,
            message="食物营养数据导入成功",
            status="success"
        )
    except Exception as e:
        logger.error(f"导入食物数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导入食物数据时发生内部错误"
        )


@router.get("/categories/{category}", response_model=FoodNutritionPage)
def read_foods_by_category(
    category: str = Path(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    按分类获取食物列表
    """
    return get_food_by_category(
        db=db, category=category, page=page, size=size
    )


@router.get("/categories", response_model=FoodNutritionCategories)
def read_all_categories(
    db: Session = Depends(get_db)
) -> Any:
    """
    获取所有食物分类
    """
    categories = get_all_categories(db=db)
    return FoodNutritionCategories(categories=categories)


@router.get("/diabetes-friendly", response_model=FoodNutritionPage)
def read_diabetes_friendly_foods(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取适合糖尿病患者的食物
    """
    return get_diabetes_friendly_foods(
        db=db, page=page, size=size, category=category
    )


@router.get("/low-gi", response_model=FoodNutritionPage)
def read_low_gi_foods(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    threshold: int = Query(55, ge=0, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取低GI食物
    """
    return get_low_gi_foods(
        db=db, page=page, size=size, threshold=threshold
    )


@router.get("/gi-range", response_model=FoodNutritionPage)
def read_foods_by_gi_range(
    min: int = Query(0, ge=0),
    max: int = Query(100, le=100),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    根据血糖指数范围查询食物
    """
    return get_foods_by_gi_range(
        db=db, min_gi=min, max_gi=max, page=page, size=size
    )


@router.get("/search", response_model=FoodNutritionPage)
def search_food(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    搜索食物
    """
    return search_foods(
        db=db, query=q, page=page, size=size
    )


@router.post("/{food_id:int}/image", response_model=ImageUploadResponse)
async def upload_image(
    food_id: int = Path(..., ge=1),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    上传食物图片
    """
    # 检查用户是否有管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能上传食物图片"
        )
    
    # 检查食物是否存在
    food = get_food_nutrition(db=db, food_id=food_id)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食物记录不存在"
        )
    
    # 验证文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能上传图片文件"
        )
    
    try:
        # 上传图片
        result = await upload_food_image(file=file, food_id=food_id)
        
        # 更新食物记录中的图片URL
        food_update = FoodNutritionUpdate(image_url=result["file_path"])
        update_food_nutrition(db=db, food_id=food_id, food_in=food_update)
        
        return ImageUploadResponse(
            file_path=result["file_path"],
            file_size=result["file_size"],
            message="食物图片上传成功",
            status="success"
        )
    except Exception as e:
        logger.error(f"上传食物图片失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="上传食物图片时发生内部错误"
        )


@router.delete("/{food_id:int}/image", status_code=status.HTTP_200_OK)
def delete_image(
    food_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    删除食物图片
    """
    # 检查用户是否有管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能删除食物图片"
        )
    
    # 检查食物是否存在
    food = get_food_nutrition(db=db, food_id=food_id)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食物记录不存在"
        )
    
    # 检查是否有图片
    if not food.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该食物没有关联的图片"
        )
    
    # 删除图片
    success = delete_food_image(food_id=food_id, image_url=food.image_url)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除食物图片失败"
        )
    
    # 更新食物记录中的图片URL为空
    food_update = FoodNutritionUpdate(image_url=None)
    update_food_nutrition(db=db, food_id=food_id, food_in=food_update)
    
    return {"message": "食物图片已删除", "status": "success"}
