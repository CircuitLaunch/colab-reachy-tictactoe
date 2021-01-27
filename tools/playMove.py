import os
import numpy as np
from reachy import Reachy, parts
from reachy.trajectory import TrajectoryPlayer
from collections import OrderedDict

from glob import glob


def patch_right_arm_config(arm_cls):
    arm_cls.dxl_motors = OrderedDict(
        [
            (
                "shoulder_pitch",
                {
                    "id": 10,
                    "offset": 0.0,
                    "orientation": "indirect",
                    "angle-limits": [-180, 60],
                    "link-translation": [0, -0.19, 0],
                    "link-rotation": [0, 1, 0],
                },
            ),
            (
                "shoulder_roll",
                {
                    "id": 11,
                    "offset": 90.0,
                    "orientation": "indirect",
                    "angle-limits": [-100, 90],
                    "link-translation": [0, 0, 0],
                    "link-rotation": [1, 0, 0],
                },
            ),
            (
                "arm_yaw",
                {
                    "id": 12,
                    "offset": 0.0,
                    "orientation": "indirect",
                    "angle-limits": [-90, 90],
                    "link-translation": [0, 0, 0],
                    "link-rotation": [0, 0, 1],
                },
            ),
            (
                "elbow_pitch",
                {
                    "id": 13,
                    "offset": 0.0,
                    "orientation": "indirect",
                    "angle-limits": [0, 125],
                    "link-translation": [0, 0, -0.28],
                    "link-rotation": [0, 1, 0],
                },
            ),
        ]
    )

    return arm_cls


def patch_force_gripper(forceGripper):
    def __init__(self, root, io):
        """Create a new Force Gripper Hand."""
        parts.hand.Hand.__init__(self, root=root, io=io)

        dxl_motors = OrderedDict(
            {name: dict(conf) for name, conf in self.dxl_motors.items()}
        )

        self.attach_dxl_motors(dxl_motors)

        """
        self._load_sensor = self.io.find_module('force_gripper')
        self._load_sensor.offset = 4
        self._load_sensor.scale = 10000
        """

    forceGripper.__init__ = __init__

    return forceGripper


parts.RightArm = patch_right_arm_config(parts.RightArm)
parts.arm.RightForceGripper = patch_force_gripper(parts.arm.RightForceGripper)

dir_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "reachy_tictactoe", "moves")


names = [
    os.path.splitext(os.path.basename(f))[0]
    for f in glob(os.path.join(dir_path, "*.npz"))
]

moves = {name: np.load(os.path.join(dir_path, f"{name}.npz")) for name in names}


rest_pos = {
    "right_arm.shoulder_pitch": 50,
    "right_arm.shoulder_roll": -15,
    "right_arm.arm_yaw": 0,
    "right_arm.elbow_pitch": -80,
    "right_arm.hand.forearm_yaw": -15,
    "right_arm.hand.wrist_pitch": -60,
    "right_arm.hand.wrist_roll": 0,
}

base_pos = {
    "right_arm.shoulder_pitch": 60,
    "right_arm.shoulder_roll": -15,
    "right_arm.arm_yaw": 0,
    "right_arm.elbow_pitch": -95,
    "right_arm.hand.forearm_yaw": -15,
    "right_arm.hand.wrist_pitch": -50,
    "right_arm.hand.wrist_roll": 0,
    "right_arm.hand.gripper": -45,
}

reachy = Reachy(right_arm=parts.RightArm(io="ws", hand="force_gripper"))
input("Connect the Unity simulator, then press Enter to continue.")

while True:
    selection = input("Name a move: ")
    
    if selection == 'rest_pos':
        reachy.goto(
            goal_positions=rest_pos,
            duration=1,
            wait=True,
            interpolation_mode="minjerk",
            starting_point="goal_position",
        )
    elif selection == 'base_pos':
        reachy.goto(
            goal_positions=base_pos,
            duration=1,
            wait=True,
            interpolation_mode="minjerk",
            starting_point="goal_position",
        )
    else:
        move = moves[selection]

        if np.ndim(move[move.files[0]]) == 0:  # Position
            reachy.goto(
                goal_positions=move,
                duration=1,
                wait=True,
                interpolation_mode="minjerk",
                starting_point="goal_position",
            )
        else:
            j = {
                m: j for j, m in zip(np.array(list(move.values()))[:, 0], list(move.keys()))
            }

            reachy.goto(
                goal_positions=j,
                duration=0.5,
                wait=True,
                interpolation_mode="minjerk",
                starting_point="goal_position",
            )
            TrajectoryPlayer(reachy, move).play(wait=True)
