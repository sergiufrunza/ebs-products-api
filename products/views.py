from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Category, Product
from .serializers import (
    AveragePriceByCategoryInputSerializer,
    AveragePriceByProductInputSerializer,
    CategorySerializer,
    PriceSerializer,
    ProductSerializer,
)
from .utils.average import get_average_by_category, get_average_by_product


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @swagger_auto_schema(
        method="get",
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                format="date",
                required=True,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                format="date",
                required=True,
            ),
            openapi.Parameter(
                "group_by",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=["week", "month"],
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Average price per period (week/month)",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "period": openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                            "average_price": openapi.Schema(type=openapi.TYPE_NUMBER, format="decimal"),
                        },
                        required=["period", "average_price"],
                    ),
                ),
            ),
            400: openapi.Response(
                description="Validation error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "field_name": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_STRING),
                        )
                    },
                ),
            ),
            404: openapi.Response(
                description="Product not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="average-price")
    def average_price(self, request, pk=None):
        serializer = AveragePriceByProductInputSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        group_by = request.query_params.get("group_by")
        product = self.get_object()
        return get_average_by_product(product, start_date=start_date, end_date=end_date, group_by=group_by)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class PriceViewSet(viewsets.ViewSet):
    @swagger_auto_schema(request_body=PriceSerializer, responses={201: PriceSerializer})
    def create(self, request):
        serializer = PriceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method="get",
        manual_parameters=[
            openapi.Parameter(
                "category",
                openapi.IN_QUERY,
                description="Category Name",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format="date",
                required=True,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format="date",
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Average price response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "category": openapi.Schema(type=openapi.TYPE_STRING),
                        "start_date": openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                        "end_date": openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                        "average_price": openapi.Schema(type=openapi.TYPE_NUMBER, format="decimal"),
                    },
                ),
            ),
            400: openapi.Response(
                description="Validation error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "field_name": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_STRING),
                        )
                    },
                ),
            ),
            404: openapi.Response(
                description="Category not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=["get"], url_path="average-by-category", url_name="average-by-category")
    def average_by_category(self, request):
        serializer = AveragePriceByCategoryInputSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category_name = serializer.validated_data["category"]
        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        return get_average_by_category(category_name, start_date, end_date)
