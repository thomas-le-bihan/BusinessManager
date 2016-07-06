from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.list_invoice, name="list_invoice"),
    url(r'^edit/$', views.edit_invoice, name="edit_invoice"),
    url(r'^pdf/$', views.pdf_invoice, name="pdf_invoice"),
    url(r'^mail/$', views.mail_invoice, name="mail_invoice"),
    url(r'^pay/$', views.pay_invoice, name="pay_invoice"),
]
