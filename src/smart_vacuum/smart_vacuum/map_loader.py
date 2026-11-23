"""Map loader node: /vacuum/set_floor_level service for floor configuration."""

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from smart_vacuum_interfaces.srv import SetFloorLevel

# floor_id -> (grid width, grid height, initial x, initial y, initial yaw)
FLOORS = {
    'Floor_1': (20, 20, 0.0, 0.0, 1.57),
    'Floor_2': (30, 30, 7.0, 2.0, 1.57),
    'Floor_3': (40, 40, 2.0, 4.0, 1.57),
}


class MapLoader(Node):

    def __init__(self):
        super().__init__('map_loader')
        self.declare_parameter('current_floor', '')
        self.declare_parameter('initial_pose_x', 0.0)
        self.declare_parameter('initial_pose_y', 0.0)
        self.declare_parameter('initial_pose_yaw', 0.0)
        self.grid_map = None
        self.srv = self.create_service(
            SetFloorLevel, '/vacuum/set_floor_level', self.set_floor_level_callback)
        self.get_logger().info('Map loader ready: service "/vacuum/set_floor_level"')

    def set_floor_level_callback(self, request, response):
        floor_id = request.floor_id
        if floor_id not in FLOORS:
            response.success = False
            response.message = (
                f'Invalid floor "{floor_id}". Valid options: {", ".join(FLOORS)}')
            self.get_logger().error(response.message)
            return response

        width, height, x, y, yaw = FLOORS[floor_id]

        # Load the (simulated) occupancy grid map into memory: 0 = free cell
        self.grid_map = [[0] * width for _ in range(height)]
        self.get_logger().info(f'Loaded grid map for {floor_id}: {width}x{height} cells')

        # Set initial pose parameters
        self.set_parameters([
            Parameter('current_floor', value=floor_id),
            Parameter('initial_pose_x', value=x),
            Parameter('initial_pose_y', value=y),
            Parameter('initial_pose_yaw', value=yaw),
        ])
        self.get_logger().info(f'Initial pose set to x={x}, y={y}, yaw={yaw}')

        response.success = True
        response.message = (
            f'Map for {floor_id} loaded ({width}x{height} grid). '
            f'Initial pose set to x={x}, y={y}, yaw={yaw}')
        return response


def main(args=None):
    rclpy.init(args=args)
    map_loader = MapLoader()
    try:
        rclpy.spin(map_loader)
    except KeyboardInterrupt:
        pass
    finally:
        map_loader.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
