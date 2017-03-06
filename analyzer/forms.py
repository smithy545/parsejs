from django import forms

class UploadFileForm(forms.Form):
	filetype = forms.ChoiceField(choices=[("js", "JavaScript")])
	file = forms.FileField()