from setuptools import setup, find_packages

setup(name="wyag",
      version="0.0.1",
      packages=find_packages(),
      install_requires=[
        "Click"
      ],
      entry_points={
        "console_scripts": [
          "wyag = wyag.wyag_lib:cli"
        ]
      })
