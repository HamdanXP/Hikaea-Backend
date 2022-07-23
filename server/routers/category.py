from fastapi import APIRouter

from server.models.category import Category, CategoriesList

router = APIRouter(tags=['Categories'])


@router.get("/list_of_categories", description="Use to get all the categories", response_model=CategoriesList,
            status_code=200)
def get_categories():
    return CategoriesList()


@router.put("/add_new_category", description="Use to add a new category", status_code=200)
def add_new_category(category: Category):
    return {"categoryId": category.id}
