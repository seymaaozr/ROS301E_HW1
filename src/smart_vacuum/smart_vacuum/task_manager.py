"""Task manager node: /vacuum/clean action server for cleaning sessions."""

import time

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from smart_vacuum_interfaces.action import CleaningTask
from smart_vacuum_interfaces.msg import VacuumStatus

ROOMS = ['Living Room', 'Kitchen', 'Bedroom', 'Bathroom']

# Cleaning speed per power mode (m^2 per second)
POWER_SPEED = {'ECO': 0.5, 'STANDARD': 1.0, 'TURBO': 1.5}

# Simulated duration of each mode (seconds)
MODE_DURATION = {'MAP_ONLY': 5.0, 'CLEAN_EXISTING_MAP': 10.0, 'SLAM_AND_CLEAN': 15.0}

STEP_PERIOD = 0.5  # seconds between feedback updates


class TaskManager(Node):
    def __init__(self):
        super().__init__('task_manager')
        self.callback_group = ReentrantCallbackGroup()
        self.battery_level = 100.0

        self.status_sub = self.create_subscription(
            VacuumStatus,
            '/vacuum/status',
            self.status_callback,
            10,
            callback_group=self.callback_group,
        )

        self.action_server = ActionServer(
            self,
            CleaningTask,
            '/vacuum/clean',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.callback_group,
        )
        self.get_logger().info('Task manager ready: action server "/vacuum/clean"')

    def status_callback(self, msg):
        self.battery_level = msg.battery_level

    def goal_callback(self, goal_request):
        if goal_request.mode not in MODE_DURATION:
            self.get_logger().warn(f'Rejected goal: invalid mode "{goal_request.mode}"')
            return GoalResponse.REJECT
        if goal_request.power_mode not in POWER_SPEED:
            self.get_logger().warn(
                f'Rejected goal: invalid power mode "{goal_request.power_mode}"')
            return GoalResponse.REJECT
        self.get_logger().info(
            f'Accepted goal: mode={goal_request.mode}, power_mode={goal_request.power_mode}')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request (Return to Dock)')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        mode = goal_handle.request.mode
        power_mode = goal_handle.request.power_mode
        self.get_logger().info(f'Executing {mode} task in {power_mode} mode...')

        cleans = mode != 'MAP_ONLY'
        speed = POWER_SPEED[power_mode]
        steps = int(MODE_DURATION[mode] / STEP_PERIOD)

        start_time = time.monotonic()
        cleaned_area = 0.0
        feedback = CleaningTask.Feedback()

        for i in range(steps):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Task canceled, returning to dock')
                return self.make_result(
                    cleaned_area, start_time, CleaningTask.Result.CANCELLED)

            if self.battery_level <= 0.0:
                goal_handle.abort()
                self.get_logger().error('Battery depleted, task aborted')
                return self.make_result(
                    cleaned_area, start_time, CleaningTask.Result.FAILED)

            time.sleep(STEP_PERIOD)
            if cleans:
                cleaned_area += speed * STEP_PERIOD

            feedback.current_room = ROOMS[i * len(ROOMS) // steps]
            feedback.completion_percentage = (i + 1) / steps * 100.0
            feedback.battery_level = self.battery_level
            goal_handle.publish_feedback(feedback)

        goal_handle.succeed()
        result = self.make_result(cleaned_area, start_time, CleaningTask.Result.SUCCESS)
        self.get_logger().info(
            f'Task finished: area={result.cleaned_area:.2f} m^2, '
            f'time={result.total_elapsed_time:.1f} s')
        return result

    @staticmethod
    def make_result(cleaned_area, start_time, code):
        result = CleaningTask.Result()
        result.cleaned_area = cleaned_area
        result.total_elapsed_time = time.monotonic() - start_time
        result.completion_code = code
        return result


def main(args=None):
    rclpy.init(args=args)
    task_manager = TaskManager()
    executor = MultiThreadedExecutor()
    executor.add_node(task_manager)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        task_manager.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
