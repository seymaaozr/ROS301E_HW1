import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'smart_vacuum'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Şeyma Özer',
    maintainer_email='seymaozer5454@gmail.com',
    description='Nodes for a simulated autonomous home vacuum cleaner',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': ['hardware_driver = smart_vacuum.hardware_driver:main',
                            'map_loader = smart_vacuum.map_loader:main',
                            'task_manager = smart_vacuum.task_manager:main'
        ],
    },
)
