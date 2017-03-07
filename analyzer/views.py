from django.shortcuts import render
from tempfile import TemporaryFile

from tools.parser.javascript.parse import Parser as ParserJS
from tools.parser.util import ParseError
from .forms import UploadFileForm

def index(request):
	context = {}
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			with TemporaryFile(mode='wb+') as f:
				for chunk in request.FILES['file'].chunks():
					f.write(chunk)
				f.seek(0)
				try:
					ftype = form.cleaned_data['filetype']
					context["obj"] = ""
					if ftype == 'js':
						p = ParserJS(f.read().decode('utf-8'))
						p.parse()
						context["obj"] = p.convert()

					return render(request, 'analyzer/parsed.html', context)
				except ParseError as e:
					context["error"] = {
						'message': "Error parsing file."
					}
	else:
		form = UploadFileForm()

	context["form"] = form
	return render(request, 'analyzer/index.html', context)
