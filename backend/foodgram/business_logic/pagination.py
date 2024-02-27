from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 6

    def get_page_size(self, request):
        try:
            print('query params: ', request.query_params)
            page_size = int(request.query_params.get(self.page_size_query_param))
            if page_size < 1:
                raise ValueError
            return page_size
        except (TypeError, ValueError):
            return self.page_size

    # def get_paginated_response(self, data):
    #     return Response({
    #         'count': self.page.paginator.count,
    #         'next': self.get_next_link(),
    #         'previous': self.get_previous_link(),
    #         'results': data
    #     })
