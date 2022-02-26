setup(
    name="aws-transcript",
    version="1.0.0",
    description="Parses AWS Transcribe output and converts to CSV, TSV, or HTML",
    long_description=README,
    long_description_content_type="",
    url="https://github.com/senorkrabs/aws-transcript",
    author="",
    author_email="",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    packages=["aws_transcript"],
    include_package_data=True,
    install_requires=[
        "pandas"
    ],
    entry_points={"console_scripts": ["aws-transcript=aws_transcript:__main__:main"]},
)
