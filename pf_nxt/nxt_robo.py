#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nxt.motor import *
from nxt.sensor import *
from nxt.bluesock import BlueSock

import time

from pf_nxt.nxt_player import Nxt_Player
from pf_nxt.nxt_pad import PadController
from pf_nxt.nxt_autopilot import AutoPilot
from pf_nxt.nxt_pair import Pair


class ScoutRobo(object):
    '''
    ScoutRobo is a python class to control a lego-nxt robot by using bluetooth
    or usb connection.
    '''

    def __init__(self, baddr, pin):
        '''
        initialize robot. by default robot is found using bluetooth,
        remember to install bluetooth lib before usage!
        :param baddr: The bluetooth mac address
        :param pin: The pin to ensure the connection
        '''

        # Pair with nxt via bluetooth
        self.stable_connection = Pair(baddr, pin)

        # Connect to nxt via bluetooth
        self.brick = BlueSock(baddr).connect()

        # initialize basic functions
        self.init_motors()
        self.init_sensors()

        # initialize some useful vars
        self.touch_right = False
        self.touch_left = False

        # locked is used to stop robo from moving when it has collided
        # getting orders from http-server
        self.locked = False

        # player for beeps and stuff
        self.player = Nxt_Player(self.brick)

        # Initialize pad and autopilot modules
        # TODO: do not start padmode if server
        self.pad_controller = PadController(self)
        self.autopilot = AutoPilot(self)

        self.calibrate()

    def init_motors(self):
        '''
        find and initialize motors from ports of brick
        '''

        self.motors = [
            Motor(self.brick, PORT_A),
            # Motor(self.brick, PORT_B)
        ]

        self.steering_motor = Motor(self.brick, PORT_C)
        self.steering_motor.brake()

    def calibrate(self):
        '''
        turn steering motor to extreme positions and calculate middle position
        from both end positions
        '''
        print('calibrating...')
        direction = 1
        self.steering_motor.run(power=direction * 60)
        time.sleep(10)
        self.steering_motor.brake()
        tacho = self.steering_motor.get_tacho()
        tacho_one = tacho.tacho_count
        self.max_left = tacho_one
        print('left max', tacho_one)
        direction = -1
        self.steering_motor.run(power=direction * 60)
        time.sleep(10)
        self.steering_motor.brake()
        tacho = self.steering_motor.get_tacho()
        tacho_two = tacho.tacho_count
        self.max_right = tacho_two
        print('max right', tacho_two)
        interval = tacho_one - tacho_two
        self.steering_interval = interval / 2
        # middle = interval / 2
        self.tacho_middle = tacho_two + self.steering_interval
        for i in range(5):
            tacho = self.steering_motor.get_tacho()
            tacho_cur = tacho.tacho_count
            tacho_diff = self.tacho_middle - tacho_cur
            if tacho_diff > 0:
                self.steering_motor.turn(power=50, tacho_units=tacho_diff)
                time.sleep(1)
            elif tacho_diff < 0:
                self.steering_motor.turn(power=-50, tacho_units=-tacho_diff)
                time.sleep(1)

        tacho = self.steering_motor.get_tacho()
        tacho_middle_now = tacho.tacho_count
        self.steering_motor.idle()
        print('calibration done', tacho_one, tacho_two, self.tacho_middle, tacho_middle_now)

    def init_sensors(self):
        '''
        find and initialize sensors from ports of brick
        useful sensors: 'touch_left', 'touch_right', 'light_color', 'ultrasonic'
        '''

        # map sensor names against driver class and port plugged in robot for
        # safe initialization
        SENSOR_MAP = {
            "touch_left": (Touch, PORT_2),
            "touch_right": (Touch, PORT_1),
            "light_color": (Color20, PORT_3),  # unable to false-detect this one
            "ultrasonic": (Ultrasonic, PORT_4),
        }

        self.sensors = {}
        for sensor_name, sensor in SENSOR_MAP.items():
            sensor_class, port = sensor
            try:
                sensor_instance = sensor_class(self.brick, port)
                sensor_instance.get_sample()
            except Exception:
                print('Init sensor %s on port %s failed.' % (sensor_name, port))
                print('Are you sure its plugged in?')  # Have u tried turning it off and on again?
                continue
            self.sensors[sensor_name] = sensor_instance

    def move(self, forward, turn):
        '''
        move robot based on forward and turn values which should be between -1
        and 1
        '''

        # do not react to forward/turn values smaller than...
        STEERING_MARGIN = 0.1
        # fraction of steering interval used, 1 means full (not recommended!)
        STEERING_DAMPENING = 0.5
        # power used on steering motor, between ~60 and 127
        STEERING_POWER = 90

        # check if forward/backward has to be performed
        # 60 is minimum power and maximum is 127
        if forward < -STEERING_MARGIN:
            self.go_forward(power=(-60 + 67 * forward))
        if forward > STEERING_MARGIN:
            self.go_forward(power=(60 + 67 * forward))

        tacho = self.steering_motor.get_tacho()
        tacho_cur = tacho.tacho_count

        # stop robot if nothing is found
        if abs(forward) < STEERING_MARGIN:
            self.stop()
        if abs(turn) < STEERING_MARGIN:
            # go to middle position
            tacho_diff = self.tacho_middle - tacho_cur
            if tacho_diff > 0:
                self.steering_motor.turn(
                    power=STEERING_POWER,
                    tacho_units=tacho_diff
                )
            elif tacho_diff < 0:
                self.steering_motor.turn(
                    power=-STEERING_POWER,
                    tacho_units=-tacho_diff
                )
        else:  # ...or perform steering by
            # calculating difference to middle position based on turn value
            # avoid oversteering, only use fraction of steering_interval
            tacho_desired = self.tacho_middle + turn * abs(self.steering_interval) * STEERING_DAMPENING
            tacho_diff = tacho_cur - tacho_desired
            if tacho_diff < 0:
                self.steering_motor.turn(
                    power=STEERING_POWER,
                    tacho_units=-tacho_diff
                )
            elif tacho_diff > 0:
                self.steering_motor.turn(
                    power=-STEERING_POWER,
                    tacho_units=tacho_diff
                )

        # lock steering_motor
        self.steering_motor.brake()

    def keep_alive(self):
        '''
        Keeps robot connection alive so it won't turn off automatically after
        time. It will come to weird errors if the robot turns off while the
        server is running. Only option is to terminate the process then.
        Don't even know if this is working, just a theory
        '''
        self.brick.sock.send("DD!")

    def get_telemetry(self):
        '''
        method to acquire sensor data, called e.g. by external modules
        '''

        # Fancy oneliner to create a new dictionary with old keys but new values
        telemetry = {k: v.get_sample() for k, v in self.sensors.items()}

        return telemetry

    def check_color(self):
        '''
        check if underground has white color (= 6)
        '''
        # TODO: check docs and write / use dictionary mapping color codes
        if self.sensors.get("light_color"):
            val = self.sensors["light_color"].get_sample()
            if val == 5:
                return True
            else:
                return False
        else:
            return False

    def check_collision(self):
        '''
        check touch and ultrasonic sensors to detect collisions
        '''
        if self.sensors.get("touch_left") and self.sensors.get("touch_right"):
            self.touch_left = self.sensors["touch_left"].get_sample()
            self.touch_right = self.sensors["touch_right"].get_sample()

            if self.touch_left or self.touch_right:
                return True

        # also check ultrasonic here, its useful if robo drives straight
        # forward towards a wall, so touch sensors cant detect collision
        if self.sensors.get("ultrasonic"):
            self.distance = self.sensors["ultrasonic"].get_sample()
            # TODO: magic number --> config file!
            if self.distance < 6:
                return True

        return False

    def timed_checks(self, ftime):
        '''
        timed collision and color checks done while robo is moving
        '''

        # count times color sensor detects goal color
        color_times = 0

        # color sensor can be a little fuzzy, so one detection does not
        # necessarily mean "goal reached"
        color_times_limit = 3

        # TODO: reset counter after certain amount of time!

        start = time.time()
        while True:
            now = time.time()
            if (now - start) > ftime:
                break
            if self.check_collision():
                self.stop()
                if not self.player.playing_song:
                    self.player.play_song('fail')
                # self.locked = True
                break
            if self.check_color():
                color_times += 1
                if color_times > color_times_limit:
                    self.stop()
                    if not self.player.playing_song:
                        self.player.play_song('success')
                    # self.locked = True
                    break
        return

    def unlock(self):
        '''
        robo is locked when it collides. unlock is called by nxt-control app
        '''
        self.locked = False

    def go_forward(self, power=80):
        for motor in self.motors:
            motor.run(power)

    def stop(self):
        for motor in self.motors:
            motor.idle()