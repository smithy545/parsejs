import json
from django import template
from tools.parser.javascript.objects import *

register = template.Library()

@register.filter
def display(value):
	out = ""
	if isinstance(value, dict):
		out += "<div class='" + value["type"] + "'>"
		if value["type"] == 'function':
			out += "<div class='name'>" + value["name"] + "</div>"
			out += "<div class='returnContainer'>"
			for r in value["returned"]:
				out += display(r)
			out += "</div>"
		elif value["type"] == 'return':
			for e in value["expression"]:
				out += display(e)
		elif value["type"] == 'expression':
			temp = ""
			for v in value["values"]:
				if isinstance(v, str):
					out += v
				else:
					out += display(v)
			out += temp
		elif value["type"] == 'array':
			for e in value["elements"]:
				display(e)
		elif value["type"] == 'variable':
			out += "<div class='name'>" + value["name"] + "</div>"
			display(value["value"])
		elif value["type"] == 'object':
			for i in range(len(value["keys"])):
				out += "<div class='key'>"
				out += display(value["keys"][i])
				out += "</div><div class='value'>"
				out += display(value["values"][i])
				out += "</div>"
		elif value["type"] == 'logic':
			for e in value["expressions"]:
				display(e)
		elif value["type"] == 'regex':
			out += display(value["expression"])
		out += "</div>"
	else:
		out += value
	return out