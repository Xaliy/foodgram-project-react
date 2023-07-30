from rest_framework.pagination import PageNumberPagination


class CustomPaginator(PageNumberPagination):
    """Пагинатор PageNumberPagination с ограничением limit."""

    page_size = 6
    page_size_query_param = 'limit'
