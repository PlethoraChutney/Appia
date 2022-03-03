import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name = 'appia',
    version = '7.0.11',
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
    package_data={'appia': ['processors/flow_rates.json']},
    packages = setuptools.find_packages(where = 'src'),
    python_requires = ">=3.6",
    install_requires = [
        'Gooey',
        'couchdb',
        'pandas',
        'easygui',
        'slack',
        'plotly'
    ],
    entry_points = {
        'console_scripts': ['appia=appia.appia:main']
    }
)