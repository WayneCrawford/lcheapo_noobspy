import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()
    
version={}
with open("lcheapo/version.py") as fp:
    exec(fp.read(),version)

setuptools.setup(
    name="seaplan",
    version=version['__version__'],
    author="Wayne Crawford",
    author_email="crawford@ipgp.fr",
    description="LCHEAPO data operations",
    long_description=long_description,
    long_description_content_type="text/x-rst; charset=UTF-8",
    url="https://github.com/pypa/lcheapo",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
      ],
    entry_points={
         'console_scripts': [
             'lcfix=lcheapo.lcfix:main'
             'lcdump=lcheapo.lcdump:main'
             'lcheader=lcheapo.lcheader:main'
         ]
    },
    python_requires='==2.7',
    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics"
    ),
    keywords='oceanography, marine, OBS'
)