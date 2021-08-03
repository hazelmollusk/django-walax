from django.shortcuts import render
from .serializers import WalaxModelSerializer
from .metadata import WalaxModelMetadata
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.decorators import action
from rest_framework import viewsets, permissions
from rest_framework.response import Response

USER = get_user_model()


class UserSerializer(WalaxModelSerializer):
    class Meta:
        model = USER
        fields = "__all__"


class CurrentUserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    @action(detail=True)
    def user(self, request):
        user = request.user
        if type(user) == AnonymousUser:
            print("anonymous")
            return Response(None)
        serializer = self.get_serializer(user, many=False)
        return Response(serializer.data)


class WalaxModelViewSet(viewsets.ModelViewSet):
    metadata_class = WalaxModelMetadata

    def list(self, request):
        filters = {}
        for k, v in request.GET.items():
            if k in ["format", "_limit", "_offset"]:
                continue
            filters[k] = v
        filters = self.validate_filters(filters)
        queryset = self.queryset.filter(**filters)
        # if '_limit' in request.GET:
        #     limit = int(request.GET['_limit']) \
        #         if '_limit' in request.GET else 0
        #     offset = int(request.GET['_offset']) \
        #         if '_offset' in request.GET else 0
        #     print (limit, offset)
        #     ret = ret[offset:offset+limit]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def validate_filters(self, filters):
        return filters

    @staticmethod
    def for_model(modelo, serializer=None):

        if not serializer:

            class aWalaxModelSerializer(WalaxModelSerializer):
                class Meta:
                    model = modelo
                    fields = "__all__"

            serializer = aWalaxModelSerializer

        class aWalaxModelViewSet(WalaxModelViewSet):
            serializer_class = aWalaxModelSerializer
            queryset = modelo.objects.all()
            permission_classes = [permissions.AllowAny]

        return aWalaxModelViewSet
