from reachy import Reachy, parts
from reachy.trajectory import TrajectoryPlayer
from collections import OrderedDict
import time
from threading import Thread, Event
import os
import numpy as np

from glob import glob

dir_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "reachy_tictactoe",
    "moves",
)


names = [
    os.path.splitext(os.path.basename(f))[0]
    for f in glob(os.path.join(dir_path, "*.npz"))
]

moves = {name: np.load(os.path.join(dir_path, f"{name}.npz")) for name in names}


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


parts.arm.RightForceGripper = patch_force_gripper(parts.arm.RightForceGripper)

io_setting = None
while not io_setting:
    input_answer = input("Is this a simulated Reachy? y/n? ")
    if input_answer == "y" or input_answer == "Y":
        io_setting = "ws"
    elif input_answer == "n" or input_answer == "N":
        io_setting = "/dev/ttyUSB*"


class LimitedTictactoePlayground(object):
    def __init__(self):
        print("Creating the playground")

        self.reachy = Reachy(
            right_arm=parts.RightArm(io=io_setting, hand="force_gripper",)
        )

        self.pawn_played = 0

    def setup(self):
        print("Setup the playground")

        self.goto_rest_position()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        print("Closing the playground")
        self.reachy.close()

    # Playground and game functions

    def shuffle_board(self):
        self.goto_base_position()
        # self.reachy.head.look_at(0.5, 0, -0.4, duration=1, wait=False)
        m = moves['shuffle-board']  # Trevor change
        j = {
            m: j
            for j, m in zip(
                np.array(list(m.values()))[:, 0],
                list(m.keys())
            )
        }
        self.goto_position(j, duration=0.5, wait=True)
        TrajectoryPlayer(self.reachy, m).play(wait=True)
        self.goto_rest_position()
        # self.reachy.head.look_at(1, 0, 0, duration=1, wait=True)

    def play_pawn(self, grab_index, box_index):
        # Goto base position
        self.goto_base_position()

        if grab_index >= 4:
            self.goto_position(
                moves["grab_3"], duration=1, wait=True,
            )

        # Grab the pawn at grab_index
        self.goto_position(
            moves[f"grab_{grab_index}"], duration=1, wait=True,
        )
        self.goto_position(moves["grip_pawn"], duration=0.5, wait=True)  # Trevor change

        if grab_index >= 4:
            self.reachy.goto(
                {
                    "right_arm.shoulder_pitch": self.reachy.right_arm.shoulder_pitch.goal_position
                    + 10,
                    "right_arm.elbow_pitch": self.reachy.right_arm.elbow_pitch.goal_position
                    - 30,
                },
                duration=1,
                wait=True,
                interpolation_mode="minjerk",
                starting_point="goal_position",
            )

        # Lift it
        self.goto_position(
            moves["lift"], duration=1, wait=True,
        )

        # self.reachy.head.look_at(0.5, 0, -0.35, duration=0.5, wait=False)
        time.sleep(0.1)

        # Put it in box_index
        put = moves[f"put_{box_index}"]  # Trevor change
        j = {m: j for j, m in zip(np.array(list(put.values()))[:, 0], list(put.keys()))}
        self.goto_position(j, duration=0.5, wait=True)
        TrajectoryPlayer(self.reachy, put).play(wait=True)

        self.reachy.right_arm.hand.open()

        # Go back to rest position
        self.goto_position(
            moves[f"back_{box_index}_upright"], duration=1, wait=True,
        )

        # self.reachy.head.look_at(1, 0, 0, duration=1, wait=False)

        if box_index in (8, 9):
            self.goto_position(
                moves["back_to_back"], duration=1, wait=True,
            )

        self.goto_position(
            moves["back_rest"], duration=2, wait=True,
        )

        self.goto_rest_position()

    def run_my_turn(self):
        self.goto_base_position()
        m = moves['my-turn']  # Trevor change
        j = {
            m: j
            for j, m in zip(
                np.array(list(m.values()))[:, 0],
                list(m.keys())
            )
        }
        self.goto_position(j, duration=0.5, wait=True)
        TrajectoryPlayer(self.reachy, m).play(wait=True)
        self.goto_rest_position()

    def run_your_turn(self):
        self.goto_base_position()
        m = moves['your-turn']  # Trevor change
        j = {
            m: j
            for j, m in zip(
                np.array(list(m.values()))[:, 0],
                list(m.keys())
            )
        }
        self.goto_position(j, duration=0.5, wait=True)
        TrajectoryPlayer(self.reachy, m).play(wait=True)
        self.goto_rest_position()

    # Robot lower-level control functions

    def goto_position(self, goal_positions, duration, wait):
        self.reachy.goto(
            goal_positions=goal_positions,
            duration=duration,
            wait=wait,
            interpolation_mode="minjerk",
            starting_point="goal_position",
        )

    def goto_base_position(self, duration=2.0):
        for m in self.reachy.right_arm.motors:
            m.compliant = False

        time.sleep(0.1)

        self.reachy.right_arm.shoulder_pitch.torque_limit = 75
        self.reachy.right_arm.elbow_pitch.torque_limit = 75
        time.sleep(0.1)

        self.goto_position(moves["base_pos"], duration, wait=True)  # Trevor change

    def goto_rest_position(self, duration=2.0):
        # FIXME: Why is it needed?
        time.sleep(0.1)

        self.goto_base_position(0.6 * duration)
        time.sleep(0.1)

        self.goto_position(
            moves["rest_pos"], 0.4 * duration, wait=True
        )  # Trevor change
        time.sleep(0.1)

        self.reachy.right_arm.shoulder_pitch.torque_limit = 0
        self.reachy.right_arm.elbow_pitch.torque_limit = 0

        time.sleep(0.25)

        for m in self.reachy.right_arm.motors:
            if m.name != "right_arm.shoulder_pitch":
                m.compliant = True

        time.sleep(0.25)

    def need_cooldown(self):
        motor_temperature = np.array([m.temperature for m in self.reachy.motors])

        temperatures = {}
        temperatures.update({m.name: m.temperature for m in self.reachy.motors})

        print(f"Checking motor temperatures: {temperatures}")
        return np.any(motor_temperature > 50)

    def wait_for_cooldown(self):
        self.goto_rest_position()
        # self.reachy.head.look_at(0.5, 0, -0.65, duration=1.25, wait=True)
        # self.reachy.head.compliant = True

        while True:
            motor_temperature = np.array([m.temperature for m in self.reachy.motors])

            temperatures = {}
            temperatures.update({m.name: m.temperature for m in self.reachy.motors})
            print(f"Motors cooling down... {temperatures}")

            if np.all(motor_temperature < 45):
                break

            time.sleep(30)

    def enter_sleep_mode(self):
        # self.reachy.head.look_at(0.5, 0, -0.65, duration=1.25, wait=True)
        # self.reachy.head.compliant = True

        self._idle_running = Event()
        self._idle_running.set()

        def _idle():
            while self._idle_running.is_set():
                time.sleep(0.01)

        self._idle_t = Thread(target=_idle)
        self._idle_t.start()

    def leave_sleep_mode(self):
        # self.reachy.head.compliant = False
        time.sleep(0.1)
        # self.reachy.head.look_at(1, 0, 0, duration=1, wait=True)

        self._idle_running.clear()
        self._idle_t.join()


with LimitedTictactoePlayground() as playground:
    if io_setting == 'ws':
        input("Connect the Unity simulator, then press Enter to continue.")

    playground.setup()

    while True:
        picked_action = input(
            'Enter "p" to pick and place a pawn, "m" for the "my-turn" gesture, "y" for the "your-turn" gesture, or "s" for the "shuffle-board" gesture: '
        )

        if picked_action == "m":
            playground.run_my_turn()
        elif picked_action == "y":
            playground.run_your_turn()
        elif picked_action == "s":
            playground.shuffle_board()
        elif picked_action == "p":
            pick_index = input("Enter pick index, 1-5: ")
            place_index = input("Enter place index, 1-9: ")
            if int(pick_index) in range(1, 6) and int(place_index) in range(
                1, 10
            ):  # Python ranges don't count upper bound
                playground.play_pawn(int(pick_index), int(place_index))

        if playground.need_cooldown():
            print("Reachy needs cooldown")
            playground.enter_sleep_mode()
            playground.wait_for_cooldown()
            playground.leave_sleep_mode()
            print("Reachy cooldown finished")
