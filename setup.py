import setuptools

with open('README.md', 'r') as readme_file:
	long_description = readme_file.read()

setuptools.setup(
	name='RedisBridge',
	version='1.1.2',
	author='Ini Oguntola',
	author_email='ioguntol@andrew.cmu.edu',
	description='Send and receive messages via a Redis server',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://gitlab.com/cmu_asist/RedisBridge',
	packages=setuptools.find_packages(),
	classifiers=[
		'Programming Language :: Python :: 3',
		'License :: OSI Approved :: MIT License',
		'operating System :: OS Independent',
	],
	python_requires='>=3.6',
	install_requires=[
		'redis>=3',
		'fakeredis',
	],
)
