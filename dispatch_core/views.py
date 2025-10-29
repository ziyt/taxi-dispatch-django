from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    try:
        return render(request, "dashboard.html")
    except Exception:
        return HttpResponse("OK")