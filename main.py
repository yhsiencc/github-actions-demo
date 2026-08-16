import os
import platform

print("=" * 40)
print("Hello from Python script in GitHub Actions!")
print(f"Operating System: {platform.system()} {platform.release()}")
print(f"Current Directory: {os.getcwd()}")
print("=" * 40)
