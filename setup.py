import setuptools

with open('README.md', 'r') as readme_file:
	long_description = readme_file.read()

setuptools.setup(
	name='RedisBridge',
	version='1.0',
	author='Ini Oguntola',
	author_email='ioguntol@andrew.cmu.edu',
	description='Bridge to internal Redis bus',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://gitlab.com/cmu_asist/RedisBridge',
	packages=setuptools.find_packages(include=['RedisBridge']),
	classifiers=[
		'Programming Language :: Python :: 3',
		'License :: OSI Approved :: MIT License',
		'operating System :: OS Independent',
	],
	python_requires='>=3.6',
	install_requires=[
		'redis>=3',
	],
)
