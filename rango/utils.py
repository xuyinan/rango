from rango.models import Category





def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name_istartswith=starts_with)

    if max_results>0 and len(cat_list)>max_results:
        cat_list = cat_list[:max_results]

    return cat_list
