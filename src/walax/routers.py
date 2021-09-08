from django.urls import include, path
from rest_framework.schemas import get_schema_view
from rest_framework import routers, serializers, viewsets
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
import inspect
from pprint import pp
from .views import WalaxModelViewSet, CurrentUserViewSet, ModelActionViewSet


class ModelActionRouter(routers.BaseRouter):
    def __init__(self, model):
        super().__init__()
        self.model = model

    @property
    def urls(self):
        urlpatterns = [
        ]
        funcs = inspect.getmembers(self.model, predicate=inspect.isfunction)
        for n, f in funcs:
            if getattr(f, 'walax_action', False):
                urlpatterns.append(path('<str:id>/%s/' % n,
                                        ModelActionViewSet.as_view(
                                            actions={'get': 'call', 'post': 'call'})))
        return urlpatterns


class ActionRouter(routers.BaseRouter):
    def __init__(self, base):
        super().__init__()
        self.base = base

    @property
    def urls(self):
        urlpatterns = [
            path(
                model._meta.verbose_name.replace(" ", "_"),
                include(ModelActionRouter(model).urls)
            )
            for model in self.base.models
        ]
        return urlpatterns


class WalaxRouter(routers.DefaultRouter):
    def __init__(self):
        super().__init__()
        self.models = []
        self.registry = []
        self.views = {}
        self.action_router = ActionRouter(self)

    def register_model(self, model=False, view=False):
        self.models.append(model)
        if not view:
            view = WalaxModelViewSet.for_model(model)
        # fixme
        modelSlug = model._meta.verbose_name.replace(" ", "_")

        self.register(modelSlug, view)

    def register_view(self, url, view):
        self.views[url] = view

    @property
    def urls(self):
        urlpatterns = [
            path("models/", include(super().urls)),
            # path('action/', include(self.action_router.urls))
        ]
        for url, view in self.views.items():
            urlpatterns.append(path(url, view))

        # add auth urls
        #   these can be broken into subrouters if needed :wq
        for p in [
            path('action/', include(self.action_router.urls)),
            path(
                r"auth/user/",
                CurrentUserViewSet.as_view({"get": "user"}),
                name="current_user",
            ),
            path(
                r"auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"
            ),
            path(
                r"auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"
            ),
            path(
                r"auth/token/verify/", TokenVerifyView.as_view(), name="token_refresh"
            ),
            # path(
            #     "auth/user/",
            #     CurrentUserViewSet.as_view({"get": "user"}),
            #     name="current_user",
            # ),
        ]:
            urlpatterns.append(p)

        return urlpatterns
