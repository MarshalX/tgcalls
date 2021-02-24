from setuptools import setup, find_packages

packages = find_packages()

setup(
    name='pytgcalls',
    version='0.0.1.beta.3',
    author='Il`ya Semyonov',
    author_email='ilya@marshal.dev',
    license='LGPLv3',
    description='Library connecting python binding for tgcalls and pyrogram',
    long_description='',
    packages=packages,
    install_requires=['tgcalls == 0.0.1b2', 'pyrogram >= 1.1.13'],
    python_requires="~=3.6",
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Internet',
        'Programming Language :: Python',
    ],
    project_urls={
        'Author': 'https://github.com/MarshalX',
        'Telegram Channel': 'https://t.me/tgcallslib',
        'Telegram Chat': 'https://t.me/tgcallschat',
    }
)
