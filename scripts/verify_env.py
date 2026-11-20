import sys

print("Python:", sys.version.split()[0])
print("-" * 30)

checks = ["numpy", "cv2", "PIL", "pandas", "fastapi", "streamlit", "easyocr", "sqlalchemy"]

for name in checks:
    try:
        module = __import__(name)
        print(f"OK   {name} {getattr(module, '__version__', '')}")
    except Exception as e:
        print(f"FAIL {name}: {e}")
