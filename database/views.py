from django.http import JsonResponse
import psutil

def stream(request):
    data = {
        'cpu': psutil.cpu_percent(interval=1),
        'mem': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'load': psutil.getloadavg()[0],
    }
    print(data)
    return JsonResponse(data)