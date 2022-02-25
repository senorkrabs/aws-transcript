
import os
import shutil

dependencies = [
    'dateutil',
    'numpy',
    'pandas',
    'pip',
    'pkg_resources',
    'python_dateutil',
    'pytz',
    'setuptools',
    'six'
]

print("Deleting all local dependencies")
root_directory = '../aws-transcript'
for item in os.listdir(root_directory):
    include = False
    full_path = os.path.join(root_directory, item)
    if os.path.isdir(full_path):
        directory = item
        for dependency in dependencies:
            if directory.startswith(dependency):
                include = True

        if include:
            print(f"Deleting {full_path}")
            shutil.rmtree(full_path)

print(f"Deleting six.py")
os.remove(os.path.join(root_directory, "six.py"))
