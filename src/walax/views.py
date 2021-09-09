from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.decorators import action
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .serializers import WalaxModelSerializer
from .metadata import WalaxModelMetadata
import inspect
from pprint import pp

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
    def get_f(f, fn):
        from functools import wraps

        @action(detail=True, methods={'GET', 'POST'})
        @wraps(f)
        def callFunc(self, request, pk, fname=fn):
            obj = self.queryset.get(pk=pk)
            ff = getattr(obj, fname, lambda r: 1)
            pp({'o': obj, 'fn': fname, 'f': ff})
            # ret = ff(request)
            ret = fn

            return Response(ret)
        return callFunc

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

        funcs = inspect.getmembers(modelo, predicate=inspect.isfunction)
        pp(modelo._meta.verbose_name)
        for fname, func in funcs:
            from copy import copy
            if getattr(func, 'walax_action', False):
                pp({'found ': str(fname), 'func': func})
                setattr(aWalaxModelViewSet, fname,
                        WalaxModelViewSet.get_f(func, fname))

        return aWalaxModelViewSet
