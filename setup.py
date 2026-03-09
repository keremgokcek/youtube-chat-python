from setuptools import setup

setup(
    name='youtube-chat',
    version='0.1.0',
    url='https://github.com/mypackage.git',
    author='keremgokcek',
    author_email='keremgokcek@teteos.net',
    description='Library for fetching YouTube livestream chat',
    packages=['youtube_chat', 'youtube_chat.types'],
    install_requires=['aiohttp'],
)
