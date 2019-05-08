from setuptools import setup, find_packages

# requires = [
#          'scipy',
#          'numpy',
#          'pyrtlsdr',
#          'matplotlib'
#         ]

requires = []

setup(name='rtltoolkit',
      version='0.1',
      description='A command line toolkit for the RTL-SDR',
      url='http://github.com/vitonaychev/RTL_SDR_Toolkit',
      author='Viktor Naychev',
      author_email='vik.naychev.tues19@gmail.com',
      license='GPL-3.0',
      python_requires='>=3.4',
      packages=find_packages(),
      install_requires=requires,
      entry_points={
        'console_scripts': [
            'rtltoolkit=rtltoolkit.main',
        ],
      },
      zip_safe=False)
