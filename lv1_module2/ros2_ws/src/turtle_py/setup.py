import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'turtle_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 문제 9: launch 파일과 파라미터 YAML 을 share/ 에 설치해야
        # ros2 launch turtle_py ... 로 찾을 수 있고 params_file 기본 경로가 유효해집니다.
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pa33',
    maintainer_email='chj021216@gmail.com',
    description='turtlesim distance / watcher / square driver nodes',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'turtle_distance_publisher = turtle_py.ex03_distance_publisher:main',
            'turtle_distance_subscriber = turtle_py.ex03_distance_subscriber:main',
            'square = turtle_py.square:main',
            'builtin_service_client = turtle_py.ex05_builtin_service_client:main',
            'rotate_absolute_client = turtle_py.ex05_rotate_absolute_client:main',
            'toggle_servers = turtle_py.ex05_toggle_servers:main',
            'polygon_action_server = turtle_py.ex06_polygon_action_server:main',
            'waypoint_publisher = turtle_py.ex06_waypoint_publisher:main',
            'qos_sensor_publisher = turtle_py.ex07_qos_sensor_publisher:main',
            'qos_subscriber = turtle_py.ex07_qos_subscriber:main',
            'tf_broadcaster = turtle_py.tf_broadcaster:main',
            'waypoint_markers = turtle_py.waypoint_markers:main',
        ],
    },
)
