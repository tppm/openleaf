from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import JsonResponse, FileResponse
from .models import LatexProject, LatexFile
from django.core.files.base import ContentFile
from django.conf import settings
import subprocess
import os
import tempfile
from django.views.decorators.http import require_POST



@login_required(login_url='login')
def project_select_view(request):
    projects = LatexProject.objects.filter(user=request.user)
    return render(request, 'editor/project_select.html', {'projects': projects})

@login_required(login_url='login')
def editor_view(request, project_id):
    project = get_object_or_404(LatexProject, id=project_id, user=request.user)
    files = project.latex_files.all()
    main_file = files.filter(is_main_file=True).first()



    if not main_file:
        main_file = LatexFile.objects.create(
            project=project,
            filename="main.tex",
            content=r"\documentclass{article}\n\begin{document}\n\nYour content here.\n\n\end{document}",
            is_main_file=True
        )


    context = {
        'project': project,
        'files': files,
        'main_file': main_file
    }
    
    return render(request, 'editor/editor.html', context)


@login_required
def get_file(request, file_id):
    file = get_object_or_404(LatexFile, id=file_id, project__user=request.user)
    return JsonResponse({
        'id': file.id,
        'filename': file.filename,
        'content': file.content,
    })

@login_required
@require_POST
def save_file(request, file_id):
    file = get_object_or_404(LatexFile, id=file_id, project__user=request.user)
    content = request.POST.get('content')
    if content is not None:
        file.content = content
        file.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'No content provided'}, status=400)



@login_required(login_url='login')
def create_project(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'Project title is required'})
        
        project = LatexProject.objects.create(
            title=title,
            user=request.user
        )
        
        # Create a main LaTeX file for the project
        content = r"\documentclass{article}\n\begin{document}\n\nYour content here.\n\n\end{document}"
        LatexFile.objects.create(
            project=project,
            filename=f"{title.replace(' ', '_')}.tex",
            content=content,
            is_main_file=True
        )
        
        return JsonResponse({'success': True, 'project_id': project.id})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('editor')
    else:
        form = UserCreationForm()
    return render(request, 'editor/register.html', {'form': form})


@login_required(login_url='login')
def compile_latex(request, project_id):
    project = get_object_or_404(LatexProject, id=project_id, user=request.user)
    main_file = get_object_or_404(LatexFile, project=project, is_main_file=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file_path = os.path.join(tmpdir, main_file.filename)
        with open(tex_file_path, 'w') as f:
            f.write(main_file.content)

        try:
            # Run pdflatex twice to ensure all references are resolved
            for _ in range(2):
                subprocess.run(['pdflatex', '-interaction=nonstopmode', '-output-directory', tmpdir, tex_file_path], 
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            pdf_file_path = os.path.splitext(tex_file_path)[0] + '.pdf'
            if os.path.exists(pdf_file_path):
                with open(pdf_file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'inline; filename="{os.path.basename(pdf_file_path)}"'
                    return response
            else:
                return JsonResponse({"error": "Failed to generate PDF"}, status=500)

        except subprocess.CalledProcessError as e:
            # If pdflatex fails, return an error message
            error_output = e.stderr.decode('utf-8')
            return JsonResponse({"error": f"Error generating PDF: {error_output}"}, status=500)