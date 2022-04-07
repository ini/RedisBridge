import setuptools

with open('README.md', 'r') as readme_file:
	long_description = readme_file.read()

setuptools.setup(
	name='RedisBridge',
	version='2.0.2',
	author='Ini Oguntola',
	author_email='ini@alum.mit.edu',
	description='Send and receive messages via a Redis server',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/ini/RedisBridge',
	packages=setuptools.find_packages(),
	classifiers=[
		'Programming Language :: Python :: 3',
		'License :: OSI Approved :: MIT License',
		'Operating System :: OS Independent',
	],
	python_requires='>=3.6',
	install_requires=[
		'atexit',
		'redis>=3',
		'fakeredis',
	],
)
