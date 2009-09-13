from distutils.core import setup
import os

# borrowed from django
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('spindrop'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[9:] # Strip "spindrop/"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))


setup(name='spindrop',
      version='0.1',
      description="Some wierd diversion of openid/simonw's code.  don't use it",
      url = 'http://spindrop.us/',
      package_dir={'spindrop': 'spindrop'},
      packages=packages,
      package_data={'spindrop': data_files},
      )
