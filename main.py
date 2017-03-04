from analyzejs import analyze
from structure import organize

def main():
    objects = analyze("./test.js")
    structure = organize(objects)

if __name__ == "__main__":
    main()

