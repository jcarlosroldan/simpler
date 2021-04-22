from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as fp:
	long_description = fp.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
	requirements = f.read().strip().split()

setup(
	name='simpler',
	version='2.0.0',
	author='Juan C. Roldán',
	author_email='juancarlos@sevilla.es',
	description='Makes Python simpler.',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/juancroldan/simpler',
	license='MIT',
	packages=find_packages(),
	install_requires=requirements,
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
	],
)