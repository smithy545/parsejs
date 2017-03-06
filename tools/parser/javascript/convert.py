import json
from .objects import *

def convert(objs):
	jsonString = ""
	for obj in objs:
		if isinstance(obj, Function):
			pass
		elif isinstance(obj, Array):
			pass
		elif isinstance(obj, Logic):
			pass
		elif isinstance(obj, Variable):
			pass
		elif isinstance(obj, Container):
			pass
		elif isinstance(obj, Expression):
			pass
		elif isinstance(obj, Return):
			pass
		elif isinstance(obj, Regex):
			pass

	return str(objs)