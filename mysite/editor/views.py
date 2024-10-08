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
from django.http import HttpResponse
import traceback
import logging

logger = logging.getLogger(__name__)



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


@login_required
@require_POST
def compile_latex(request, project_id):
    try:
        logger.info(f"Starting compilation for project_id: {project_id}")
        project = LatexProject.objects.get(id=project_id, user=request.user)
        logger.info(f"Project found: {project.title}")
        main_file = project.latex_files.get(is_main_file=True)
        logger.info(f"Main file: {main_file.filename}")

        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info(f"Created temporary directory: {tmpdir}")

            # Create images directory
            images_dir = os.path.join(tmpdir, 'images')
            os.makedirs(images_dir)
            logger.info(f"Created images directory: {images_dir}")

            # Copy all project files to temp directory
            for file in project.latex_files.all():
                with open(os.path.join(tmpdir, file.filename), 'w') as f:
                    f.write(file.content)
                logger.info(f"Copied file: {file.filename}")


            # Copy all project images to images directory
            for image in project.images.all():
                with open(os.path.join(images_dir, image.image.name), 'wb') as f:
                    f.write(image.image.read())
                logger.info(f"Copied image: {image.image.name}")

            # Run pdflatex
            logger.info("Starting pdflatex compilation")
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', main_file.filename],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )

            if process.returncode != 0:
                logger.error(f"LaTeX compilation failed. Return code: {process.returncode}")
                logger.error(f"STDOUT: {process.stdout}")
                logger.error(f"STDERR: {process.stderr}")
                return HttpResponse(process.stderr, status=500, content_type='text/plain')

            # Read the generated PDF
            pdf_filename = os.path.splitext(main_file.filename)[0] + '.pdf'
            pdf_path = os.path.join(tmpdir, pdf_filename)
            
            if os.path.exists(pdf_path):
                logger.info(f"PDF generated successfully: {pdf_path}")
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                
                return HttpResponse(pdf_content, content_type='application/pdf')
            else:
                logger.error(f"PDF not generated. Path does not exist: {pdf_path}")
                return HttpResponse('PDF not generated', status=500, content_type='text/plain')
    except Exception as e:
        logger.exception(f"Unexpected error in compile_latex: {str(e)}")
        return HttpResponse(f"An error occurred: {str(e)}\n\n{traceback.format_exc()}", status=500, content_type='text/plain')