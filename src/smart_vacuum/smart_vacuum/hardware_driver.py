"""Hardware driver node: publishes simulated telemetry on /vacuum/status at 1 Hz."""

import random

import rclpy
from rclpy.node import Node
from smart_vacuum_interfaces.msg import VacuumStatus

DUSTBIN_FULL_THRESHOLD = 80.0  # %
LOW_BATTERY_THRESHOLD = 5.0    # % - simulated auto-recharge on the dock below this


class HardwareDriver(Node):

    def __init__(self):
        super().__init__('hardware_driver')
        self.publisher = self.create_publisher(VacuumStatus, '/vacuum/status', 10)
        self.battery = 100.0
        self.dustbin = 0.0
        self.timer = self.create_timer(1.0, self.publish_status)
        self.get_logger().info('Hardware driver ready: publishing "/vacuum/status" at 1 Hz')

    def publish_status(self):
        # Slow simulated drain so a demo session lasts several minutes
        self.battery = max(0.0, self.battery - random.uniform(0.05, 0.2))
        if self.battery < LOW_BATTERY_THRESHOLD:
            self.get_logger().warn('Battery low: simulating recharge on dock')
            self.battery = 100.0
        self.dustbin = min(100.0, self.dustbin + random.uniform(0.1, 0.5))

        msg = VacuumStatus()
        msg.battery_level = self.battery
        msg.dustbin_fullness_status = (
            'FULL' if self.dustbin >= DUSTBIN_FULL_THRESHOLD else 'OK')
        msg.cliff_state = random.random() < 0.05
        msg.bumper_state = random.random() < 0.05

        self.publisher.publish(msg)
        self.get_logger().info(
            f'Battery={self.battery:.1f}%, '
            f'Dustbin={msg.dustbin_fullness_status} ({self.dustbin:.1f}%), '
            f'Cliff={msg.cliff_state}, Bumper={msg.bumper_state}')


def main(args=None):
    rclpy.init(args=args)
    hardware_driver = HardwareDriver()
    try:
        rclpy.spin(hardware_driver)
    except KeyboardInterrupt:
        pass
    finally:
        hardware_driver.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
