import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-walax",
    version="0.1.4",
    author="Matt Barry",
    author_email="matt@hazelmollusk.org",
    description="Walax Django API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hazelmollusk/django-walax",
    project_urls={
        "Bug Tracker": "https://github.com/pypa/sampleproject/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
