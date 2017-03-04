from analyze import analyze

objects = analyze('./test.js')
for obj in objects:
    print obj
