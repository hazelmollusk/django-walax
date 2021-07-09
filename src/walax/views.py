from django.shortcuts import render
from rest_framework import viewsets, permissions
from .serializers import WalaxModelSerializer
from rest_framework.response import Response

class WalaxModelViewSet(viewsets.ModelViewSet):

    def list(self, request):
        filters = {}
        for k, v in request.GET.items():
            if k != 'format': filters[k] = v
        self.queryset = self.queryset.filter(**filters)
        return super().list(self, request)

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
