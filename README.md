# Smart Vacuum – ROS 2 Autonomous Home Vacuum Cleaner

ROS 301E – Programming Techniques for Robotics, HW I.

A simulated ROS 2 (Humble) software architecture for an autonomous home vacuum
cleaner, demonstrating the three core ROS 2 communication patterns:

| Pattern | Name | Interface | Provided by |
|---|---|---|---|
| Topic (1 Hz telemetry) | `/vacuum/status` | `smart_vacuum_interfaces/msg/VacuumStatus` | `hardware_driver` |
| Service (floor configuration) | `/vacuum/set_floor_level` | `smart_vacuum_interfaces/srv/SetFloorLevel` | `map_loader` |
| Action (cleaning session) | `/vacuum/clean` | `smart_vacuum_interfaces/action/CleaningTask` | `task_manager` |

## Workspace layout

```
vacuum_ws/
└── src/
    ├── smart_vacuum_interfaces/      # ament_cmake – custom interfaces
    │   ├── msg/VacuumStatus.msg
    │   ├── srv/SetFloorLevel.srv
    │   └── action/CleaningTask.action
    └── smart_vacuum/                 # ament_python – nodes (rclpy)
        ├── smart_vacuum/
        │   ├── hardware_driver.py
        │   ├── map_loader.py
        │   └── task_manager.py
        └── launch/vacuum.launch.py
```

## Architecture

```
┌──────────────────┐   /vacuum/status (VacuumStatus, 1 Hz)   ┌──────────────────┐
│ hardware_driver  │ ──────────────────────────────────────▶ │  task_manager    │
└──────────────────┘                                          │ (action server)  │
                                                              └────────▲─────────┘
                                                                       │ /vacuum/clean
                                                                       │ (CleaningTask)
┌──────────────────┐   /vacuum/set_floor_level (SetFloorLevel)  ┌──────┴─────────┐
│   map_loader     │ ◀───────────────────────────────────────── │  user / CLI    │
│ (service server) │                                            └────────────────┘
└──────────────────┘
```

- **hardware_driver** – simulates the robot hardware and publishes battery
  level, dustbin status and cliff/bumper sensor state every second.
- **map_loader** – service server; given a floor ID it loads the floor's grid
  map into memory, sets the initial pose parameters and returns a
  success flag with an informative message.
- **task_manager** – action server; runs a multi-step cleaning session, streams
  feedback (current room, completion %, battery) every 0.5 s, returns
  session statistics, and supports mid-task cancellation ("Return to Dock").
  It subscribes to `/vacuum/status` to track the battery and aborts the session
  if the battery is depleted.

Valid floor IDs for the service are `Floor_1`, `Floor_2` and `Floor_3`.

## Interfaces

### `msg/VacuumStatus.msg`
```
float64 battery_level            # battery charge (%)
string  dustbin_fullness_status  # dustbin state
bool    cliff_state              # cliff sensor triggered
bool    bumper_state             # bumper sensor triggered
```

### `srv/SetFloorLevel.srv`
```
string floor_id
---
bool   success
string message
```

### `action/CleaningTask.action`
```
string mode        # MAP_ONLY | CLEAN_EXISTING_MAP | SLAM_AND_CLEAN
string power_mode  # ECO | STANDARD | TURBO
---
float64 cleaned_area        # total area cleaned (m^2)
float64 total_elapsed_time  # session duration (s)
int64   completion_code     # SUCCESS=0, CANCELLED=1, FAILED=2 (battery depleted)
---
string  current_room
float64 completion_percentage
float64 battery_level
```

## Build

Requires ROS 2 Humble.

```bash
cd ~/vacuum_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## Run

Start the whole system with the launch file:

```bash
ros2 launch smart_vacuum vacuum.launch.py
```

Or run each node in its own terminal:

```bash
ros2 run smart_vacuum hardware_driver
ros2 run smart_vacuum map_loader
ros2 run smart_vacuum task_manager
```

## Verification (V1–V4)

Run each command in a new terminal after `source install/setup.bash`.

**V1 – System graph**
```bash
rqt_graph
```

**V2 – Live telemetry**
```bash
ros2 topic echo /vacuum/status
ros2 topic hz /vacuum/status      # ~1 Hz
rqt                               # Plugins → Topics → Topic Monitor
```

**V3 – Floor configuration service**
```bash
ros2 service call /vacuum/set_floor_level smart_vacuum_interfaces/srv/SetFloorLevel "{floor_id: 'Floor_2'}"
```

**V4 – Cleaning action with feedback and cancellation**
```bash
ros2 action send_goal --feedback /vacuum/clean smart_vacuum_interfaces/action/CleaningTask \
  "{mode: 'SLAM_AND_CLEAN', power_mode: 'TURBO'}"
```
Press `Ctrl+C` in the `send_goal` terminal while feedback is streaming to send a
cancel request. The task manager logs the cancellation, stops the session and
returns the partial statistics with `completion_code: 1` (CANCELLED).

Invalid goals (e.g. `mode: 'FOO'`) are rejected by the goal callback.
