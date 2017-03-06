from django.shortcuts import render
from tempfile import TemporaryFile

from tools.parser.javascript.parse import Parser
from tools.parser.javascript.convert import convert
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
					pythonObj = Parser(f.read().decode('utf-8')).parse()
					context["obj"] = convert(pythonObj)

					return render(request, 'analyzer/parsed.html', context)
				except ParseError:
					context["error"] = {
						'message': "Error parsing file."
					}
	else:
		form = UploadFileForm()

	context["form"] = form
	return render(request, 'analyzer/index.html', context)
