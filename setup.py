from setuptools import setup


setup(
    name="caster",
    version="0.1",
    py_modules=['caster'],
    author="Aviv Palivoda",
    author_email="palaviv@gmail.com",
    description="Caster is a command line tool for casting media to chromecast",
    license="MIT",
    url="https://github.com/palaviv/caster",
    download_url="https://github.com/palaviv/caster/tarball/0.1",
    entry_points={
        'console_scripts': ['caster=caster:main'],
    },
    install_requires=[
        'six',
        'pychromecast',
        'readchar'
    ],
)
