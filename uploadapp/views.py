# Create your views here.
from django.http import JsonResponse
from .forms import ImageForm

def image_upload(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save()
            image_url = request.build_absolute_uri(image.image.url)
            return JsonResponse({'image_url': image_url}, status=201)
        else:
            return JsonResponse({'error': 'Invalid request'}, status=400)
    else:
        form = ImageForm()
        # 如果是GET请求，返回一个空的表单页面或者仅仅返回错误状态
        return JsonResponse({'error': 'Invalid request'}, status=400)