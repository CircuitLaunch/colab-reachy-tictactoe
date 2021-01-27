from reachy import Reachy, parts
from reachy.trajectory import TrajectoryRecorder
import numpy as np
from collections import OrderedDict
import traceback
import re


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

io_setting = None
while not io_setting:
    input_answer = input("Is this a simulated Reachy? y/n? ")
    if input_answer == "y" or input_answer == "Y":
        io_setting = "ws"
    elif input_answer == "n" or input_answer == "N":
        io_setting = "/dev/ttyUSB*"

try:
    reachy = Reachy(right_arm=parts.RightArm(io=io_setting, hand="force_gripper"))
except:
    traceback.print_exc()
    exit("Exception when initializing Reachy")

if io_setting == "ws":
    input("Connect the Unity simulator, then press Enter to continue.")

for m in reachy.right_arm.motors:
    print(f"Motor found: {m.name} - pos:{m.present_position}")
    m.compliant = True


stop_loop = False
while not stop_loop:
    print("Ready to record!")

    record_motor_list = []

    print(
        "Type in the motors you want to record by index. Shoulder pitch is 0, gripper is 7."
    )
    print(
        "For example, if you want to record shoulder pitch, shoulder roll and forearm yaw, type '014'."
    )
    while not record_motor_list:
        input_motor_nums = input("Enter motors now. Only enter digits 0-7: ")
        if input_motor_nums and not re.compile(r"[^0-7]").search(input_motor_nums):
            if "0" in input_motor_nums:
                record_motor_list.append(reachy.right_arm.shoulder_pitch)
            if "1" in input_motor_nums:
                record_motor_list.append(reachy.right_arm.shoulder_roll)
            if "2" in input_motor_nums:
                record_motor_list.append(reachy.right_arm.arm_yaw)
            if "3" in input_motor_nums:
                record_motor_list.append(reachy.right_arm.elbow_pitch)
            if "4" in input_motor_nums:
                record_motor_list.append(reachy.right_arm.hand.forearm_yaw)
            if "5" in input_motor_nums:
                record_motor_list.append(reachy.right_arm.hand.wrist_pitch)
            if "6" in input_motor_nums:
                record_motor_list.append(reachy.right_arm.hand.wrist_roll)
            if "7" in input_motor_nums:
                record_motor_list.append(reachy.right_arm.hand.gripper)

            print(f"You have selected {[motor.name for motor in record_motor_list]}")
            input_answer = input(
                "Enter y to continue, enter anything else to repeat selection: "
            )
            if input_answer != "y" and input_answer != "Y":
                record_motor_list = []

    recording_type = None
    while not recording_type:
        input_answer = input(
            "Enter recording type. p for position, or t for trajectory: "
        )
        if input_answer == "t" or input_answer == "T":
            recording_type = "trajectory"
        elif input_answer == "p" or input_answer == "P":
            recording_type = "position"

    recording = None

    if recording_type == "position":
        input("Move the arm into the desired position, then press Enter to capture it:")
        recording = {motor.name: motor.present_position for motor in record_motor_list}
        print(f"Recorded position: {recording}")
    else:
        recorder = TrajectoryRecorder(record_motor_list)
        input(
            "Move the arm into the start position for the trajectory, then press Enter to begin recording:"
        )
        recorder.start()
        input("To stop recording, press Enter again:")
        recorder.stop()
        recording = recorder.trajectories
        print("Recorded trajectory:")
        print(recording)

    save = None
    while not save:
        input_answer = input("Save this? y/n: ")
        if input_answer == "n" or input_answer == "N":
            save = True
        elif input_answer == "y" or input_answer == "Y":
            save = True
            filename = input("Enter filename to save as: ")
            filename = filename + ".npz"
            try:
                np.savez(filename, **recording)
                print(f'Saved as {filename}!')
            except:
                traceback.print_exc()
                exit("Exception when saving file")
    
    again = None
    while not again:
        input_answer = input("Record another? y/n: ")
        if input_answer == "n" or input_answer == "N":
            again = True
            stop_loop = True
        elif input_answer == "y" or input_answer == "Y":
            again = True
