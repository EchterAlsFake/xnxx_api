from setuptools import setup, find_packages

setup(
    name="xnxx_api",
    version="1.4.2",
    packages=find_packages(),
    install_requires=[
        "requests", "bs4", "lxml", "ffmpeg-progress-yield", "eaf_base_api"
    ],
    entry_points={
        'console_scripts': ['xnxx_api=xnxx_api.xnxx_api:main'
            # If you want to create any executable scripts
        ],
    },
    author="Johannes Habel",
    author_email="EchterAlsFake@proton.me",
    description="A Python API for the Porn Site xnxx.com",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license="LGPLv3",
    url="https://github.com/EchterAlsFake/xnxx_api",
    classifiers=[
        # Classifiers help users find your project on PyPI
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Programming Language :: Python",
    ],
)