from setuptools import setup, find_packages

setup(
    name='ims_speech',
    version='0.1',
    url='https://github.com/lifefeel/ims_speech',
    license='MIT',
    author='J.P Lee',
    author_email='koreanfeel@gmail.com',
    description='IMS Speech',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    setup_requires=[]
)
