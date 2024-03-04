from django.http import JsonResponse
from .forms import ImageForm


def image_upload(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save()
            image_url = request.build_absolute_uri(image.image.url)
            return JsonResponse(
                {'result': True, 'message': 'Image uploaded successfully', 'data': {'image_url': image_url}},
                status=201)
        else:
            return JsonResponse({'result': False, 'error': 'Invalid request', 'message': 'Image upload failed',
                                 'errorMsg': 'Invalid request'}, status=400)
    else:
        # If it's a GET request, return an empty form page or simply return an error status
        return JsonResponse({'result': False, 'error': 'Invalid request', 'message': 'Image upload failed',
                             'errorMsg': 'Invalid request'}, status=400)
