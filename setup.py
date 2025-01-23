from typing import List
from setuptools import find_packages, setup

HYPHEN_E_DOT = '-e .'

def get_requirements(file_path: str) -> List[str]:
    """
    Reads a requirements file and returns a list of required packages.

    This function reads the specified requirements file, processes each line
    to remove newline characters, and removes any occurrence of the '-e .'
    entry, which indicates the current directory should be installed in editable mode.

    Args:
        file_path (str): The path to the requirements file.

    Returns:
        List[str]: A list of package requirements.
    """
    with open(file_path, encoding='utf-8') as file_obj:
        requirements = file_obj.readlines()
        requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

        # Removing editable flag from list of packages if present
        if HYPHEN_E_DOT in requirements:
            requirements.remove(HYPHEN_E_DOT)

    return requirements

setup(
    name='Are You Not Entertained',
    version='0.0.1',
    author='Kristiyan Bonev',
    author_email='k.s.bonev@gmail.com',
    description='A success predictions project for movies and TV series',
    long_description=open('README.md', encoding='utf-8').read(),  # Assuming you have a README.md
    long_description_content_type='text/markdown',
    url='https://github.com/JustaKris/Are-You-Not-Entertained',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt'),
    setup_requires=['setuptools>=58.0.0'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
    entry_points={
        'console_scripts': ['are_you_not_entertained=app:main']
    }
)
