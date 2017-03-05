from django.shortcuts import render
from tempfile import TemporaryFile

from tools.parser.parseJS import parse
from tools.parser.convertJS import convert
from tools.parser.util import ParseException
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
					pythonObj = parse(f.read().decode('utf-8'))
					context["parsedObject"] = convert(pythonObj)
					print(context)
					return render(request, 'analyzer/parsed.html', context)
				except ParseException:
					context["error"] = {
						'message': "Error parsing file."
					}
	else:
		form = UploadFileForm()

	context["form"] = form
	return render(request, 'analyzer/index.html', context)