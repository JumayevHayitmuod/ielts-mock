from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("tests/", views.test_catalog, name="test_catalog"),
    path("signup/", views.signup, name="signup"),
    path("test/<int:pk>/details/", views.test_details, name="test_details"),
    path("full-test/", views.full_exam, name="full_exam"),
    path("test/<int:pk>/", views.take_test, name="test"),
    path("attempt/<int:pk>/", views.review, name="review"),
    path("speaking/", views.speaking, name="speaking"),
    path("speaking/<int:pk>/", views.speaking, name="speaking_task"),
    path("writing/", views.writing, name="writing"),
    path("writing/attempt/<int:pk>/", views.writing_result, name="writing_result"),
    path("writing/<int:pk>/", views.writing, name="writing_task"),
    path("resources/", views.resources, name="resources"),
    path("vocabulary/", views.vocabulary, name="vocabulary"),
    path("vocabulary/test/", views.vocabulary_test, name="vocabulary_test"),
    path("results/", views.results, name="results"),
]
