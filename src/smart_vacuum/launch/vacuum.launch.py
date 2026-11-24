"""Launch the full smart vacuum system: hardware driver, map loader, task manager."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='smart_vacuum',
            executable='hardware_driver',
            name='hardware_driver',
            output='screen',
        ),
        Node(
            package='smart_vacuum',
            executable='map_loader',
            name='map_loader',
            output='screen',
        ),
        Node(
            package='smart_vacuum',
            executable='task_manager',
            name='task_manager',
            output='screen',
        ),
    ])
