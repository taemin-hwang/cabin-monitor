
import math
from service.rule.state.body_gesture_state import IdleState

class BodyGestureManager:
    def __init__(self):
        self.pose_idx = ('nose',
        'left_eye',
        'right_eye',
        'left_ear',
        'right_ear',
        'left_shoulder',
        'right_shoulder',
        'left_elbow',
        'right_elbow',
        'left_wrist',
        'right_wrist',
        'left_hip',
        'right_hip',
        'left_knee',
        'right_knee',
        'left_ankle',
        'right_ankle',
        'neck')

        self.pose_dic = {'nose': [0,0],
        'left_eye': [0,0],
        'right_eye': [0,0],
        'left_ear' : [0,0],
        'right_ear' : [0,0],
        'left_shoulder' : [0,0],
        'right_shoulder' : [0,0],
        'left_elbow' : [0,0],
        'right_elbow' : [0,0],
        'left_wrist' : [0,0],
        'right_wrist' : [0,0],
        'left_hip' : [0,0],
        'right_hip' : [0,0],
        'left_knee' : [0,0],
        'right_knee' : [0,0],
        'left_ankle' : [0,0],
        'right_ankle' : [0,0],
        'neck' : [0,0]}

        self.WIDTH = 224
        self.HEIGHT = 224
        self.X_compress = 640.0 / self.WIDTH * 1.0
        self.Y_compress = 480.0 / self.HEIGHT * 1.0

        self.bool_idle = False
        self.idle_wrist = [0,0]
        self.idle_elbow = [0,0]
        self.idle_dist_elbow_2_wrist = 0

        self.prev_state = 'idle'
        self.state = IdleState()
        self.control = -1
        self.status = -1

    '''
    identify gesture from body skeleton (joints)
    '''
    def classify_gesture(self, joints):
        for i in range(len(joints)):
            if joints[i][1]:
                x = round(joints[i][2] * self.WIDTH * self.X_compress)
                y = round(joints[i][1] * self.HEIGHT * self.Y_compress)
                self.pose_dic[self.pose_idx[i]][0] = x
                self.pose_dic[self.pose_idx[i]][1] = y
            else:
                self.pose_dic[self.pose_idx[i]][0] = 0
                self.pose_dic[self.pose_idx[i]][1] = 0
        self.transit_state()
        # self.status = self.get_status()
        return self.control

    def get_status(self):
        p_nose = self.pose_dic['nose']
        p_leye = self.pose_dic['left_eye']
        p_reye = self.pose_dic['right_eye']
        p_lear = self.pose_dic['left_ear']
        p_rear = self.pose_dic['right_ear']

        d1 = math.sqrt( ((p_nose[0]-p_leye[0])**2)+((p_nose[1]-p_leye[1])**2))
        d2 = math.sqrt( ((p_nose[0]-p_reye[0])**2)+((p_nose[1]-p_reye[1])**2))

        status = 1
        if (d1 > d2) and (p_lear[0] == 0):
            print("Gaze Left")
            status = 2
        elif (d1 < d2) and (p_rear[0] == 0):
            print("Gaze Left")
            status = 2
        else:
            status = 1
        return status

    def transit_state(self):
        if self.is_idle() == True:
            self.on_event('idle')
        else:
            event = self.is_direction()
            self.on_event(event)

    def on_event(self, event):
        self.prev_state = self.state.current_state()
        self.state = self.state.on_event(event)

        if(self.prev_state != self.state.current_state()):
            #print(self.prev_state + " ------> " + self.state.current_state())
            pass

        if(self.prev_state == 'IdleState' and self.state.current_state() == 'UpState'):
            # self.client.send_direction_packet(0)
            # print("UP")
            self.control = 1
        elif(self.prev_state == 'IdleState' and self.state.current_state() == 'DownState'):
            # self.client.send_direction_packet(1)
            # print("Down")
            self.control = 2
        elif(self.prev_state == 'IdleState' and self.state.current_state() == 'LeftState'):
            # self.client.send_direction_packet(3)
            # print("Left")
            self.control = 3
        elif(self.prev_state == 'IdleState' and self.state.current_state() == 'RightState'):
            # self.client.send_direction_packet(2)
            # print("Right")
            self.control = 4
        else:
            # print("IDLE")
            self.control = -1

    def is_idle(self):
        p1 = self.pose_dic['right_elbow']
        p2 = self.pose_dic['right_wrist']
        p3 = self.pose_dic['right_shoulder']

        if p1[0] == 0 or p2[0] == 0 or p3[0] == 0:
            return self.bool_idle

        dist_elbow_2_wrist = math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2) )
        dist_elbow_2_shoulder = math.sqrt( ((p1[0]-p3[0])**2)+((p1[1]-p3[1])**2) )

        if dist_elbow_2_shoulder * 0.5 >= dist_elbow_2_wrist:
            self.bool_idle = True
            self.idle_elbow[0] = p1[0]
            self.idle_elbow[1] = p1[1]
            self.idle_wrist[0] = p2[0]
            self.idle_wrist[1] = p2[1]
            self.idle_dist_elbow_2_wrist = dist_elbow_2_wrist
            return True
        else:
            self.bool_idle = False
            return False

    def is_direction(self):
        p1 = self.pose_dic['right_elbow']
        p2 = self.pose_dic['right_wrist']
        p3 = self.pose_dic['right_shoulder']

        dist_elbow_2_wrist = math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2) )
        dist_diff_elbow = math.sqrt( ((self.idle_elbow[0]-p1[0])**2)+((self.idle_elbow[1]-p1[1])**2) )
        dist_elbow_2_shoulder = math.sqrt( ((p1[0]-p3[0])**2)+((p1[1]-p3[1])**2) )

        if p1[0] == 0 or p2[0] == 0 or p3[0] == 0:
            return 'idle' if self.bool_idle == True else 'invalid'

        if dist_diff_elbow >= (self.idle_dist_elbow_2_wrist * 0.4):
            return 'idle' if self.bool_idle == True else 'invalid'

        if dist_elbow_2_shoulder * 0.7 <= dist_elbow_2_wrist:
            return 'idle' if self.bool_idle == True else 'invalid'

        x_diff = p2[0] - self.idle_wrist[0]
        y_diff = p2[1] - self.idle_wrist[1]

        config = 0.7

        # print(str(x_diff) + ", " + str(y_diff))

        if x_diff > 0 and (abs(x_diff)*config > abs(y_diff)):
            return 'left'
        elif x_diff <= 0 and (abs(x_diff)*config >= abs(y_diff)):
            return 'right'
        elif y_diff > 0 and (abs(y_diff)*config > abs(x_diff)):
            return 'down'
        elif y_diff <= 0 and (abs(y_diff)*config >= abs(x_diff)):
            return 'up'
        else:
            return 'invalid'

    def is_raise_left_hand(self):
        return True

    def is_raise_right_hand(self):
        return True

    def is_making_o(self):
        return True

    def is_making_x(self):
        return True

