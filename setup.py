import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name = 'appia',
    version = '7.2.2',
    author = 'Rich Posert',
    author_email = 'posert@ohsu.edu',
    description = 'Chromatography processing made easy',
    long_description=long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/PlethoraChutney/Appia',
    classifiers= [
        'License :: OSI Approved :: MIT License'
    ],
    package_dir = {'': 'src'},
    package_data={'appia': ['plotters/manual_plot_FPLC.R', 'plotters/manual_plot_HPLC.R']},
    include_package_data=True,
    packages = setuptools.find_packages(where = 'src'),
    python_requires = ">=3.6",
    install_requires = [
        'couchdb',
        'pandas',
        'plotly',
        'kaleido'
    ],
    entry_points = {
        'console_scripts': ['appia=appia.appia:main']
    }
)