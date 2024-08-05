import binascii
import numpy as np
import cv2

sizeof_MULTI_REC=4120
sizeof_REC_DATA=14
FILE_HEAD_FLAG=0x87654321
FILE_DATA_FLAG=0x12345678
FILE_DEF_FLAG=0xabcd1234

def printhex(bytecontents):
    hex_data = binascii.hexlify(bytecontents)
    print(hex_data.decode('utf-8'))

class multi_video_file():
    def __init__(self, file_path):
        self._file=open(file_path, 'rb')
        file_contents=self._file.read(sizeof_MULTI_REC)
        int_val = int.from_bytes(file_contents[0:4], 'little', signed=False)
        self._file_init=FILE_HEAD_FLAG==int_val
        if not self._file_init:
            print(file_path+' file format error!')
            self._file.close()    
            return
        self._ver= int.from_bytes(file_contents[4:8], 'little', signed=False)    
        self._groupnum= int.from_bytes(file_contents[8:12], 'little', signed=False)  
        self._total_num= int.from_bytes(file_contents[12:16], 'little', signed=False)    
        self._width= int.from_bytes(file_contents[16:20], 'little', signed=False)      
        self._height= int.from_bytes(file_contents[20:24], 'little', signed=False)   
        print('groupnum:'+str(self._groupnum))  
        print('width:'+str(self._width))  
        print('height:'+str(self._height))  
        self._temp_images=[]
        self._is_first=True
      
    def ReadImages(self):
        images=[]
        dets=[]
        timesnaps=[]
        if not self._file_init:
            print(' file not init!')
            return None,None,None
        if self._is_first:
            for i in range(self._groupnum):
                det=[]
                file_contents=self._file.read(sizeof_REC_DATA)
                flag= int.from_bytes(file_contents[0:4], 'little', signed=False)   
                if flag!=FILE_DATA_FLAG:
                     self._file.close()
                     self._file_init=False
                     print('file format error!')
                     return None,None,None
                datalen= int.from_bytes(file_contents[4:8], 'little', signed=False)  
                detnum= int.from_bytes(file_contents[8:10], 'little', signed=False)    
                timesnap= int.from_bytes(file_contents[10:14], 'little', signed=False)      
                if detnum>0:
                    for j in range(detnum):
                        point=[]
                        point_contents=self._file.read(4)
                        #printhex(point_contents)
                        x= int.from_bytes(point_contents[0:2], 'little', signed=False)    
                        y= int.from_bytes(point_contents[2:4], 'little', signed=False)  
                        point.append(x)
                        point.append(y)
                        #print(point)
                        det.append(point)
                dets.append(det)
                img_data=self._file.read(datalen)
                img_mat = np.ndarray(shape=(self._height, self._width, 3), dtype=np.uint8, buffer=img_data)
                images.append(img_mat)
                timesnaps.append(timesnap)
            self._temp_images=np.copy(images)
            self._is_first=False
            return images,dets,timesnaps
        else:
            for i in range(self._groupnum):
                det=[]
                image=self._temp_images[i]
                file_contents=self._file.read(sizeof_REC_DATA)
                if len(file_contents)!=sizeof_REC_DATA:
                    self._file.close()
                    self._file_init=False
                    return None,None,None
                flag= int.from_bytes(file_contents[0:4], 'little', signed=False)   
                if flag!=FILE_DEF_FLAG:
                     self._file.close()
                     self._file_init=False
                     print('file format error!')
                     return None,None,None
                datalen= int.from_bytes(file_contents[4:8], 'little', signed=False)  
                detnum= int.from_bytes(file_contents[8:10], 'little', signed=False)    
                timesnap= int.from_bytes(file_contents[10:14], 'little', signed=False)      
                if detnum>0:
                    for j in range(detnum):
                        point=[]
                        point_contents=self._file.read(4)
                        #printhex(point_contents)
                        x= int.from_bytes(point_contents[0:2], 'little', signed=False)    
                        y= int.from_bytes(point_contents[2:4], 'little', signed=False)  
                        point.append(x)
                        point.append(y)
                        #print(point)
                        det.append(point)
                dets.append(det)
                def_data=self._file.read(datalen)
                for j in range(0,datalen,7):
                    x= int.from_bytes(def_data[j:j+2], 'little', signed=False)
                    y= int.from_bytes(def_data[j+2:j+4], 'little', signed=False)  
                    r= def_data[j+4]
                    g= def_data[j+5]
                    b= def_data[j+6]
                    image[y,x]=(r,g,b)
                #self._temp_images[i]=np.copy(image)
                images.append(np.copy(image))
                timesnaps.append(timesnap)
            return images,dets,timesnaps


mvf=multi_video_file('/home/shr/vnc_files/20231206162205.mvf')
n=0
while True:
    images,dets,timesnaps=mvf.ReadImages()
    if images is None:
        break
    m=0
    for i in range(len(images)):
        img=images[i]
        det=dets[i]
        for d in det:
            cv2.circle(img,d,5,(2,30,200),-1 )
        cv2.imshow("image:"+str(m),img) 
        #cv2.imwrite("./Cam"+str(m)+"/image_"+str(n)+".jpg",img)
        m+=1
    cv2.waitKey(-1)
    n+=1
    print(n)


