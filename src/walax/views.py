from django.shortcuts import render
from rest_framework import viewsets, permissions
from .serializers import WalaxModelSerializer
from rest_framework.response import Response

class WalaxModelViewSet(viewsets.ModelViewSet):

    def list(self, request):
        filters = {}
        for k, v in request.GET.items():
            if k in ['format','_limit','_offset']: continue
            filters[k] = v
        filters = self.validate_filters(filters)
        self.queryset = self.queryset.filter(**filters)
        ret = super().list(self, request)
        # if '_limit' in request.GET:
        #     limit = int(request.GET['_limit']) \
        #         if '_limit' in request.GET else 0
        #     offset = int(request.GET['_offset']) \
        #         if '_offset' in request.GET else 0
        #     print (limit, offset)
        #     ret = ret[offset:offset+limit]
        return ret

    def validate_filters(self, filters):
        return filters

    @staticmethod
    def for_model(modelo, serializer=None):

        if not serializer:
            class aWalaxModelSerializer(WalaxModelSerializer):
                class Meta:
                    model = modelo
                    fields = '__all__'
            serializer = aWalaxModelSerializer

        class aWalaxModelViewSet(WalaxModelViewSet):
            serializer_class = aWalaxModelSerializer
            queryset = modelo.objects.all()
            permission_classes = [permissions.AllowAny]

        return aWalaxModelViewSet
