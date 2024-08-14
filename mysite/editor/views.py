from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from .models import LatexDocument
from django.views.decorators.csrf import csrf_exempt
import tempfile
import os
import subprocess
import base64

def editor_view(request):
    files = os.listdir(settings.TEX_FILES_DIR)
    files = [f for f in files if f.endswith(('.tex', '.png', '.jpg', '.pdf'))]
    
    context = {
        'files': files,
    }
    
    return render(request, 'editor/editor.html', context)
@csrf_exempt
def compile_latex(request):
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled Document')
        content = request.POST.get('content', '')

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_file = os.path.join(tmpdir, 'document.tex')
                with open(tex_file, 'w') as f:
                    f.write(content)

                subprocess.run(['pdflatex', '-output-directory', tmpdir, tex_file], check=True)

                pdf_path = os.path.join(tmpdir, 'document.pdf')

                if os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
                    return JsonResponse({'pdf_base64': pdf_base64})
                else:
                    raise Exception("PDF file was not generated")

        except subprocess.CalledProcessError as e:
            return JsonResponse({'error': f"LaTeX compilation failed: {e}"}, status=400)
        except Exception as e:
            return JsonResponse({'error': f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_file_content(request):
    filename = request.GET.get('filename')
    if filename:
        file_path = os.path.join(settings.TEX_FILES_DIR, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
            return JsonResponse({'content': content})
    return JsonResponse({'error': 'File not found'}, status=404)

# Add a new view to save files
@csrf_exempt
def save_file(request):
    if request.method == 'POST':
        filename = request.POST.get('filename')
        content = request.POST.get('content')
        if filename and content:
            file_path = os.path.join(settings.TEX_FILES_DIR, filename)
            with open(file_path, 'w') as file:
                file.write(content)
            return JsonResponse({'message': 'File saved successfully'})
    return JsonResponse({'error': 'Invalid request'}, status=400)