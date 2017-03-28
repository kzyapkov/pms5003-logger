from distutils.core import setup

setup(
    name="pms5003-logger",
    version="0.1.0",
    description="Acquire data from PMS5003",
    author="Kiril Zyapkov",
    author_email="kiril.zyapkov@gmail.com",
    url="http://github.com/kzyapkov/pms5003-logger",
    py_modules=['pmlog'],
    scripts=['pmlog.py'],
    install_requires=['python-periphery'],
)
