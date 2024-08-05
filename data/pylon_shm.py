import sysv_ipc
import cv2
import numpy as np
import time
import struct
import getpass
# shm addresss
SHM_MESSAGE_ADDR = 0
SHM_DETS_ADDR= 1024
SHM_POINTS_ADDR= 4096
SHM_IMAGE_ADDR = 4096*10
# message id
MSG_RECODER_START = 1
MSG_RECODER_STOP = 2
MSG_SERVE_SPEED = 3
MSG_REPLAY_START = 4


class PYLON_SHM():
    def __init__(self, shm_name):
        username = getpass.getuser()
        #print(username)
        shm_key = sysv_ipc.ftok('/home/'+username+'/shr_soft/.' + shm_name, 111, True)
        sem_key = sysv_ipc.ftok('/home/'+username+'/shr_soft/.' + shm_name, 112, True)
        msg_key = sysv_ipc.ftok('/home/'+username+'/shr_soft/.' + shm_name, 113, True)

        self._cam_name = shm_name
        # 连接到已经存在的共享内存段
        self._memory = sysv_ipc.SharedMemory(shm_key)
        self._message_addr = SHM_MESSAGE_ADDR
        self._dets_addr = SHM_DETS_ADDR
        self._mat_addr = SHM_IMAGE_ADDR
        self._points_addr = SHM_POINTS_ADDR
        self._mat_timesnap = 0
        # sem
        self._sem = sysv_ipc.Semaphore(sem_key)
        # message
        self._msg = sysv_ipc.MessageQueue(msg_key)
        self._msg_data = bytearray(12 + 256)

        self._img_mat = np.zeros((820, 1400, 3), np.uint8)
        self._img_dets=[]
        #self._is_show_fps = 0
        self._fps = 0.000
        self._frame_count = 0
        self._time_list = []    


    def get_fps(self):
        return self._fps

    def _get_tickcount(self):
        return int(time.monotonic() * 1000)

    def _shm_int_read(self, address, signed=True):
        data = self._memory.read(offset=address, byte_count=4)
        int_val = int.from_bytes(data, 'little', signed=signed)
        return int_val
    
    def _shm_short_read(self, address, signed=True):
        data = self._memory.read(offset=address, byte_count=2)
        short_val = int.from_bytes(data, 'little', signed=signed)
        return short_val

    def _shm_int_write(self, address, val):
        data = val.to_bytes(4, byteorder='little')
        self._memory.write(data, offset=address)
        return address+len(data)

    def _shm_float_write(self, address, float_value):
        data = struct.pack('f', float_value)
        self._memory.write(data, offset=address)
        return address+len(data)


    def _shm_float_read(self, address):
        data = self._memory.read(offset=address, byte_count=4)
        float_val = struct.unpack('f', data)[0]
        return float_val

    def _shm_send_message(self, msg_id, msg_val=0, msg_string='', is_wait_rsp=False):
        self._msg_data = bytearray(268)
        # |msg_val|timesnap_data|msg_strlen|msg_str...|
        msg_val_data = msg_val.to_bytes(4, byteorder='little')
        self._msg_data[0:4] = msg_val_data

        timesnap = self._get_tickcount()
        timesnap_data = timesnap.to_bytes(4, byteorder='little')
        self._msg_data[4:8] = timesnap_data

        byte_msg = bytes(msg_string, encoding='utf-8')
        msg_len = len(byte_msg)
        msg_len_data = msg_len.to_bytes(4, byteorder='little')
        self._msg_data[8:12] = msg_len_data
        self._msg_data[12:12 + msg_len] = byte_msg

        self._msg.send(self._msg_data, block=False, type=msg_id)
        print(self._cam_name + ' send msg_id:' + str(msg_id) + ' msg_val:' + str(msg_val) + ' msg_string:' + str(
            msg_string) + ' t:' + str(timesnap))
        if is_wait_rsp:
            while True:
                time.sleep(0.001)
                if self._msg.current_messages == 0:
                    return True
                if self._get_tickcount() - timesnap > 50:
                    return False
        return True

    def recoder_start(self, before_time, video_path):
        return self._shm_send_message(MSG_RECODER_START, before_time, video_path)

    def recoder_stop(self):
        return self._shm_send_message(MSG_RECODER_STOP)

    def tennis_message(self, describe):
        #|data_size|time|data
        time_msg = self._get_tickcount()
        bytes = describe.encode("UTF-8")
        shm_offset = self._message_addr
        shm_offset=self._shm_int_write(shm_offset,len(bytes))
        shm_offset=self._shm_int_write(shm_offset,time_msg)     
        self._memory.write(bytes, offset=shm_offset)
        #return self._shm_send_message(MSG_SERVE_SPEED, speed, describe)
    
    def replay_start(self, timesnap):
        return self._shm_send_message(MSG_REPLAY_START, timesnap, '')

    def is_srecoder_complete(self):
        return 1

    def release(self):
        return

    def is_ball_on_line(self,start_point, landing_point,show_point=0):
        # |datalen|time_msg|rsp|result|type|dir|inout|speed|res..|points_num|land_index|pt1_x|pt1_y|pt1_z|pt1_time|pt2_x|pt2_y|pt2_z|pt2_time|...
        time_msg = self._get_tickcount()
        shm_offset = self._points_addr
        
        shm_offset=self._shm_int_write(shm_offset,1972)#datalen
        shm_offset=self._shm_int_write(shm_offset,time_msg)#time_msg
        rsp_offset=shm_offset
        shm_offset=self._shm_int_write(rsp_offset,0)#rsp
        shm_offset=self._shm_int_write(shm_offset,0)#result
        shm_offset=self._shm_int_write(shm_offset,show_point)#type
        shm_offset=self._shm_int_write(shm_offset,0)#dir
        shm_offset=self._shm_int_write(shm_offset,0)#inout
        shm_offset=self._shm_float_write(shm_offset,0.0)#speed
        shm_offset+=4*20#res

        shm_offset=self._shm_int_write(shm_offset,2)#points_num
        shm_offset=self._shm_int_write(shm_offset,1)#land_index

        shm_offset=self._shm_float_write(shm_offset,start_point[0])
        shm_offset=self._shm_float_write(shm_offset,start_point[1])
        shm_offset=self._shm_float_write(shm_offset,start_point[2])
        shm_offset=self._shm_int_write(shm_offset,0)

        shm_offset=self._shm_float_write(shm_offset,landing_point[0])
        shm_offset=self._shm_float_write(shm_offset,landing_point[1])
        shm_offset=self._shm_float_write(shm_offset,landing_point[2])
        shm_offset=self._shm_int_write(shm_offset,0)

        time_start = self._get_tickcount()
        while True:
            rsp=self._shm_int_read(rsp_offset)#rsp
            if rsp!=0:
                return self._shm_int_read(rsp_offset+4)#rsp;
            if self._get_tickcount() - time_start > 100:
                print('get_result time out')
                return -1
            time.sleep(0.001)

    def set_3dpoints(self, points,timesnaps,landing_point_index,type,dir,inout,speed):
        # |datalen|time_msg|rsp|result|type|dir|inout|speed|res..|points_num|land_index|pt1_x|pt1_y|pt1_z|pt1_time|pt2_x|pt2_y|pt2_z|pt2_time|...
        if len(points)!=len(timesnaps) or len(points)==0 or len(timesnaps)==0 or len(points)>100:
            return
        time_msg = self._get_tickcount()
        shm_offset = self._points_addr
        
        shm_offset=self._shm_int_write(shm_offset,1972)#datalen
        shm_offset=self._shm_int_write(shm_offset,time_msg)#time_msg
        rsp_offset=shm_offset
        shm_offset=self._shm_int_write(rsp_offset,0)#rsp
        shm_offset=self._shm_int_write(shm_offset,0)#result
        shm_offset=self._shm_int_write(shm_offset,type)#type
        shm_offset=self._shm_int_write(shm_offset,dir)#dir
        shm_offset=self._shm_int_write(shm_offset,inout)#inout
        shm_offset=self._shm_float_write(shm_offset,speed)#speed
        shm_offset+=4*20#res

        shm_offset=self._shm_int_write(shm_offset,len(points))#points_num
        shm_offset=self._shm_int_write(shm_offset,landing_point_index)#land_index

        for i in range(0,len(points)):
            shm_offset=self._shm_float_write(shm_offset,points[i][0])
            shm_offset=self._shm_float_write(shm_offset,points[i][1])
            shm_offset=self._shm_float_write(shm_offset,points[i][2])
            shm_offset=self._shm_int_write(shm_offset,timesnaps[i])

    def get_mat(self, min_time=5):
        # |datalen|img_height|img_width|img_channel|time_snap|data...|
        time_start = self._get_tickcount()
        while True:
            if self._sem.value == 1:
                break
            if self._get_tickcount() - time_start > 50:
                print('get_mat time out')
                return self._img_mat
            time.sleep(0.005)

        shm_offset = self._mat_addr

        datalen = self._shm_int_read(shm_offset)
        shm_offset += 4

        img_height = self._shm_int_read(shm_offset)
        shm_offset += 4

        img_width = self._shm_int_read(shm_offset)
        shm_offset += 4

        img_channel = self._shm_int_read(shm_offset)
        shm_offset += 4

        time_snap = self._shm_int_read(shm_offset, False)
        shm_offset += 4

        dets=[]
        if self._mat_timesnap != time_snap:
            dataimg = self._memory.read(offset=shm_offset, byte_count=datalen)
            self._img_mat = np.ndarray(shape=(img_height, img_width, img_channel), dtype=np.uint8, buffer=dataimg)

            shm_offset = self._dets_addr
            all_len = self._shm_int_read(shm_offset)
            shm_offset+=4
            if all_len==402:
                det_num=self._shm_short_read(shm_offset)
                shm_offset+=2
                for i in range(det_num):
                    x=self._shm_short_read(shm_offset)
                    shm_offset+=2
                    y=self._shm_short_read(shm_offset)
                    shm_offset+=2
                    w=self._shm_short_read(shm_offset)
                    shm_offset+=2
                    h=self._shm_short_read(shm_offset)
                    shm_offset+=2
                    dets.append((x,y,w,h))

            self._time_list.append(time_snap)
            list_num = len(self._time_list)
            if list_num > 5:
                time1 = self._time_list[0]
                time2 = self._time_list[list_num - 1]
                self._fps = 1000 / ((time2 - time1) / list_num)
                if time2 - time1 > 3000:
                    self._time_list.pop(0)
            self._mat_timesnap = time_snap
            self._img_dets=dets
            
        return self._img_mat, time_snap,self._img_dets
        # cv2.putText(self._img_mat, self._cam_name, (5, 60), 0, 2, [0, 0, 255], thickness=2, lineType=cv2.LINE_AA)
        # if self._is_show_fps == 1:
            # cv2.putText(self._img_mat, 'fps:' + str("%.1f" % self._fps), (5, 120), 0, 2, [0, 0, 255], thickness=2,
            #             lineType=cv2.LINE_AA)
        #return self._img_mat, time_snap,dets

