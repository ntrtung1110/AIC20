import numpy as np
import time
import cv2
import os
import multiprocessing

RATE = 0.6
EPS = 1E-7;

# PATH_DATA = '../info'
PATH_DATA = '../Center_net/info_new'
PATH_RESULT = '../Center_net/reidentify'
# PATH_RESULT = '../reidentify'
PATH_VID = '../data/AIC20_track1/Dataset_A'
# PATH_SVID = '../video_reid'
PATH_SVID = '../Center_net/video_reid_small_frame_interval'
PATH_SFRA = '../Center_net/frame_reid'
# PATH_SFRA = '../frame_reid'
IS_VISUALIZE = True
LENGTH_FRAME = 900

def overlap(anchor, other):
    dx = min(anchor[2], other[2]) - max(anchor[0], other[0])
    dy = min(anchor[3], other[3]) - max(anchor[1], other[1])
    area = 0.0
    if (dx > 0) and (dy > 0):
        area = dx * dy
    anchor_area = (anchor[2] - anchor[0]) * (anchor[3] - anchor[1])
    overlap_rate = area / anchor_area
    #print overlap_rate
    assert overlap_rate <= 1 + EPS;
    return overlap_rate

def process(video_name, delta=10):
    COUNT = 0
    # video_name = video_name.split('.')[0]
    labels = np.load(PATH_DATA + '/info_' + video_name + '.npy')
    N = labels.shape[0]
    frame_id = labels[:, -1].astype(np.int).reshape(N)
    object_index = -1 * np.ones((labels.shape[0], ), dtype=np.int)
    print ('Process video %s' % video_name)
    print ('Re-identify Object ...', labels.shape)
    duration = time.time()
    delta_fix = delta
    for idx in range(1, LENGTH_FRAME + 1):
        cur_index = np.where(frame_id == idx)[0]
        for i in cur_index:
            cur_frame = labels[i]
            best_id = -1
            best_rate = 0.0
            for delta in range(1, delta_fix):
                pre_index = np.where(frame_id == (idx - delta))[0]
                for j in pre_index:
                    pre_frame = labels[j]
                    rate = overlap(cur_frame, pre_frame)
                    if (rate > best_rate):
                        best_rate = rate
                        best_id = j
            if (best_rate + EPS >= RATE):
                object_index[i] = object_index[best_id]
            else:
                COUNT = COUNT + 1
                object_index[i] = COUNT
        # if idx==5:
        #     break

    duration = time.time() - duration
    print ('Finish Re-identify Object  takes %f second' % duration)
    res = np.zeros((N, 7), labels.dtype)
    for i in range(N):
        res[i][0] = labels[i][-1]
        res[i][1] = labels[i][-2]
        res[i][2] = object_index[i]
        res[i, 3:] = labels[i, :4]

    np.save(PATH_RESULT + '/info_' + video_name, res)

    if not IS_VISUALIZE:
        return

    print ('Writing Video')
    duration = time.time()
    video_name = video_name[:-4]
    input = cv2.VideoCapture(PATH_VID + '/' + video_name + '.mp4')
    width = int(input.get(3)) # get width
    print("here", video_name)
    height = int(input.get(4)) #get height
    output = cv2.VideoWriter(PATH_SVID + '/' + video_name + '.mp4', cv2.VideoWriter_fourcc('M','J','P','G'), 5.0, (width, height))
    idx = 0
    while (input.isOpened()):
        ret, frame = input.read()
        if not ret:
            break
        idx= idx + 1
        index = np.where(frame_id == idx)[0]
        for i in index:
            box = labels[i].astype(np.int)
            obj_id = object_index[i]
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 3 )
            cv2.putText(frame, str(obj_id).zfill(5), (box[0], box[1]), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2,cv2.LINE_AA)
        output.write(frame)
        # cv2.imwrite(os.path.join(PATH_SFRA,video_name+str(idx)+'.jpg'), frame)
        if(idx==LENGTH_FRAME):
            break

    input.release()
    output.release()
    duration = time.time() - duration
    print ('Finish Writing Video takes %f second' % duration)

if __name__ == '__main__':
    video_names = os.listdir(PATH_VID)
    for video_name in video_names:
        if(video_name.endswith(".mp4")):
        # if(video_name == "cam_6_snow.mp4"):
            process(video_name)
