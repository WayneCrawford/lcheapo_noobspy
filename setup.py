import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()
    
version={}
with open("lcheapo/version.py") as fp:
    exec(fp.read(),version)

setuptools.setup(
    name="lcheapo",
    version=version['__version__'],
    author="Wayne Crawford (original code by Paul Georgief at UCSD-SIO)",
    author_email="crawford@ipgp.fr",
    description="LCHEAPO data operations",
    long_description=long_description,
    long_description_content_type="text/x-rst; charset=UTF-8",
    url="https://github.com/WayneCrawford/lcheapo",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=['future','jsonref'],
    entry_points={
         'console_scripts': [
             'sdpcat=lcheapo.sdpchain:sdpcat',
             'lcfix=lcheapo.lcfix:main',
             'lcdump=lcheapo.lcdump:main',
             'lccut=lcheapo.lccut:main',
             'lcinfo=lcheapo.lcinfo:main',
             'lcheader=lcheapo.lcheader:main'
         ]
    },
    python_requires='>=3.6',
    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics"
    ),
    keywords='oceanography, marine, OBS'
)