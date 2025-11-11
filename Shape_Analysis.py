import numpy as np
import cv2 as cv
import subprocess
import time
import os
import glob
import csv
import shutil

# Path to ImageJ executable (adjust this based on your installation)
imagej_executable = '/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx'
print("Path to ImageJ executable (adjust if incorrect): " + imagej_executable)
  
def rotate_save_coordinates(foldername, time_inst, initial_rotation):
    """
    Load a .tif frame. Extract the outer contour and compute shape properties. 
    Rotate the contour such that contour is "upright". Save the rotated coordinates in a .txt file.
    
    ----
    Arguments
    ----
    
        foldername (str): Name of folder of specific example to be analyzed.
        time_inst (int): Number of frame to be analyzed.
        initial_rotation (float): Angle of rotation for contour. For the first frame it is computed in this function. 
                                For all subsequent frames we use the value compute for the first frame such that contour is rotated by same angle for all frames.
    ----
    Returns
    ----
    
        properties (list): Properties of contour [center-of-mass x-coordinate, COM y-coordinate, width, height, orientation angle, length perimeter, area]
    """
    
    # --- File paths ---
    base_path = os.path.join(foldername, "Outline_Outside_Coords")
    img_path = os.path.join(base_path, str(time_inst).zfill(4)+'.tif')
    out_path = os.path.join(base_path, 'Coords_'+str(time_inst).zfill(4)+'.txt')
    
    # --- Load grayscale image ---
    img = cv.imread(img_path, cv.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {img_path}")
    
    # --- Threshold image and find outer contour ---
    _,thresh = cv.threshold(img,0,255,0)
    contours,_ = cv.findContours(thresh, 1, cv.CHAIN_APPROX_NONE)
    cnt = contours[0]
    
    # --- Compute image moments and use these to compute COM coordinates [cx, cy] ---
    M = cv.moments(cnt)
    cx = float(M['m10']/M['m00'])
    cy = float(M['m01']/M['m00'])
    
    # --- Fit ellipse to contour and compute its properties (height, width, orientation angle, length perimenter, area)  ---
    rect = cv.fitEllipse(cnt) #returns rectangle in which ellipse is inscribed
    [width, height]=rect[1]
    angle_deg = rect[2]
    perimeter = cv.arcLength(cnt,True)
    area = cv.contourArea(cnt)
    
    # --- Save all properties in list  ---
    properties = [cx, cy, width, height, angle_deg, perimeter, area]
    
    # --- Downsample contour points (keep 1/10 of original points) to equidistant points ---
    x_coords = [x[0][0] for x in cnt]
    y_coords = [x[0][1] for x in cnt]
    NumPointsIWant = len(x_coords)/10 #reduce number of points by 10
    dd = perimeter/NumPointsIWant #distance between points should be perimeter divided by number of points
    coords = np.vstack((x_coords, y_coords)).T
    
    index_array_equidistant = [0]
    counter = 0
    
    for j in range(len(coords)):
        dist = np.sqrt((coords[index_array_equidistant[counter]][0] - coords[j][0])**2 + (coords[index_array_equidistant[counter]][1] - coords[j][1])**2)
        if dist > dd:
            index_array_equidistant.append(j)
            counter += 1
    
    x_coord_equi = []
    y_coord_equi = []
    
    for j in range(len(index_array_equidistant)):
        x_coord_equi.append(coords[index_array_equidistant[j]][0]) 
        y_coord_equi.append(coords[index_array_equidistant[j]][1]) 
    
    
    # --- Determine rotation angle: for first frame compute the orientation angle of the contour. For all other frames use the angle of the first frame ---
    x_coords_rot = []
    y_coords_rot = []
    
    if time_inst == 0:
        angle_rad = -rect[2]*np.pi/180
    else:
        angle_rad = -initial_rotation*np.pi/180
    
    # --- Apply rotation about COM to get equidistant, rotated points of contour ---
    for i in range(len(x_coord_equi)):
        x_point = x_coord_equi[i] - cx
        y_point = y_coord_equi[i] - cy
        rot_x = np.cos(angle_rad) * x_point - np.sin(angle_rad) * y_point + cx
        rot_y = np.sin(angle_rad) * x_point + np.cos(angle_rad) * y_point + cy
        x_coords_rot.append(rot_x)
        y_coords_rot.append(rot_y)

    coords = np.vstack((x_coords_rot, y_coords_rot)).T
    
    # --- Save coordinates ---
    np.savetxt(out_path, coords, fmt ='%1.2f', delimiter="\t")
    
    return properties

def run_rotate_coordinates(foldername, Num_Frames):
    """
    Run the rotation and coordinate extraction for all frames in a given folder. 
    For the first frame, compute the rotation angle. For all subsequent frames, use the same rotation angle to ensure consistent orientation across frames.
    Saves properties of contour of all frames in txt file.
    
    ----
    Arguments
    ----
    
        foldername (str): Name of folder of specific example to be analyzed.
        Num_Frames (int): Total number of frames to be analyzed.
        
    ----
    Returns
    ----
    
        1

    """
    
    properties_array = []
    
    # --- Process each frame and append properties to properties_array ---
    for frames in range(Num_Frames):
        if frames == 0: # Compute rotation for the first frame
            properties = rotate_save_coordinates(foldername, frames, 0)
        else: # Reuse initial rotation (from first frame)
            properties = rotate_save_coordinates(foldername, frames, properties_array[0][4])
        
        properties_array.append(properties)   
        
    # --- Save properties from all frames to file ---
    
    np.savetxt(os.path.join(foldername, "Outline_Outside_Coords/Properties.txt"), np.array(properties_array), fmt ='%1.2f', delimiter="\t")
    
    return 1
def rotate_save_moments(foldername, time_inst):
    
    """
    Load a .tif frame. Extract the outer contour and compute geometric moments. 
    Rotate the image so that the contour is upright and calculate the rotated contour's image moments.
    
    ----
    Arguments
    ----
    
        foldername (str): Name of folder of specific example to be analyzed.
        time_inst (int): Number of frame to be analyzed.
    
    ----
    Returns
    ----
    
        moments_ret (list): Selected contour moments [m00, mu20, mu12, mu11, mu21, mu02]
    """
    
    # --- File paths ---
    base_path = os.path.join(foldername, "Outline_Outside_Coords")
    img_path = os.path.join(base_path, str(time_inst).zfill(4)+'.tif')
    
    # --- Load grayscale image ---
    img = cv.imread(img_path, cv.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {img_path}")
        
    # --- Threshold image ---
    _,thresh = cv.threshold(img,0,255,0)
    
    # --- Find outer contour and compute image moments and COM. Fit ellipse to get orientation angle. ---
    contours,_ = cv.findContours(thresh, 1, cv.CHAIN_APPROX_NONE)
    cnt = contours[0]
    M = cv.moments(cnt)
    cx = float(M['m10']/M['m00'])
    cy = float(M['m01']/M['m00'])
    rect = cv.fitEllipse(cnt) #returns rectangle in which ellipse is inscribed
    center, axes, angle = rect
    
     # --- Rotate image to align contour "upright" and find contours again, compute moments ---
    (h, w) = img.shape
    rotation_matrix = cv.getRotationMatrix2D(center, angle, 1.0)
    
    # --- Rotate thresholded image  ---
    rotated_thresh = cv.warpAffine(thresh, rotation_matrix, (w, h))
    contours,hierarchy = cv.findContours(rotated_thresh, 1, cv.CHAIN_APPROX_NONE)
    contours = contours[0]
    moments = cv.moments(contours)
    
    # --- Return selected image moments for the rotated contour ---
    moments_ret = [moments['m00'], moments['mu20'],moments['mu12'], moments['mu11'], moments['mu21'],moments['mu02']]
    
    return moments_ret
    
def run_rotate_moments(foldername, Num_Frames):
    """
    Run the rotation and moment extraction for all frames in a given folder.
    For each frame, compute the contour moments after aligning the contour upright.
    Save all computed moments in single txt file.
    
    ----
    Arguments
    ----
    
        foldername (str): Name of folder of specific example to be analyzed.
        Num_Frames (int): Total number of frames to be analyzed.
    
    ----
    Returns
    ----
    
        1
    """
    
    moments_array = []
    
    # --- Process each frame and append properties to properties_array ---
    for frames in range(Num_Frames):
        moments = rotate_save_moments(foldername, frames)
        moments_array.append(moments) 
        
     # --- Save properties from all frames to file ---
        
    np.savetxt(os.path.join(foldername, "Outline_Outside_Coords/moments.txt"), np.array(moments_array), fmt ='%1.2f', delimiter="\t")
    
    return 1

def run_imagej_macro(macro_file, dir_macro, dir_data, data_file):
    """
    Run a ImageJ macro on a specified data file using a subprocess call.
    Monitors execution and terminates the process if it exceeds a set timeout.
    
    ----
    Arguments
    ----
    
        macro_file (str): Name of the ImageJ macro file to run.
        dir_macro (str): Directory containing the macro file.
        dir_data (str): Directory containing the data file to be processed.
        data_file (str): Name of the data file to be processed by the macro.
    
    ----
    Returns
    ----
    
        1
    """
    
    # --- Paths ---
    macro_path = os.path.join(dir_macro, macro_file)
    data_path = os.path.join(dir_data, data_file)
    
    # --- Construct command to run ImageJ with the macro ---
    command = [imagej_executable, '-macro', macro_path, data_path]
   
    # Launch ImageJ as subprocess
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for ImageJ to complete or timeout occurs (adjust timeout as needed)
    timeout_seconds = 90  # Adjust as necessary
    start_time = time.time()
    while process.poll() is None:
        time.sleep(1)
        if time.time() - start_time > timeout_seconds:
            print("Timeout: ImageJ process took too long.")
            break

    # Terminate ImageJ process
    if process.poll() is None:
        print("Force terminating ImageJ")
        process.terminate()
        time.sleep(2)  # Wait for 2 seconds
        # If still running, force kill
        if process.poll() is None:
            process.kill()
            
    return 1
    

if __name__ == '__main__': 
    
    """
    Search the current directory and subdirectories for files containing 'seg' in their name.
    Create necessary folders.
    For each found file, run the ImageJ macro to generate contours, then compute rotated coordinates and geometric moments, which are saved in .txt file.
    Finally, write the list of all files found, together with the total number of frames for each, into a .csv file.
    """


    array_file_names = []
    array_tifCounter = []
    
    # --- Get the directory where this script is located ---
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # --- Search all subdirectories for files containing "seg" ---
    for folder,dirs,file in os.walk(dir_path):
        for files in file:
            if "seg" in files: 
                file_name = os.path.join(folder,files)
                array_file_names.append(file_name)
    
    # --- Process each found file ---
    for i in range(len(array_file_names)):
        print(str(round(100*i/len(array_file_names),1)) + "%")
        print(array_file_names[i])
        
        # Directories for imagej macro and data files
        dir_macro = os.path.dirname(os.path.abspath(__file__)) + '/'
        dir_data = array_file_names[i].rsplit('/',1)[0] + '/'
        data_file = array_file_names[i].rsplit('/',1)[1]
        data_file = data_file.removesuffix('.avi')  # Remove '.avi' extension from data file name
        
        # --- If output folders do not exist, create them. Then run the functions to process the data. ---
        if not os.path.exists(dir_data + data_file):
            os.makedirs(dir_data + data_file)
            if not os.path.exists(dir_data + data_file + '/Inside_Shape'):
                os.makedirs(dir_data + data_file + '/Inside_Shape')
            if not os.path.exists(dir_data + data_file + '/Outline_Outside_Coords'):
                os.makedirs(dir_data + data_file + '/Outline_Outside_Coords')
            
            # --- Run ImageJ macro to extract outline data ---
            run_imagej_macro("ExtractOutline.ijm", dir_macro, dir_data, data_file)
            
            # Count number of generated .tif frames
            tifCounter = len(glob.glob1(dir_data + data_file + '/Outline_Outside_Coords',"*.tif"))
            array_tifCounter.append(tifCounter)
            
            # --- Process frames to compute rotated coordinates and shape moments ---
            run_rotate_coordinates(dir_data + data_file + '/', tifCounter)
            run_rotate_moments(dir_data + data_file + '/', tifCounter) #quick and dirty way to save more image moments, re-does many things of run_rotate_coordinates, the two should be factorized
            
            # --- Clean up temporary folder ---
            shutil.rmtree(dir_data + data_file + '/Inside_Shape')
        
        
        # --- If folders already exists, only count existing frames ---
        else:
            tifCounter = len(glob.glob1(dir_data + data_file + '/Outline_Outside_Coords',"*.tif"))
            array_tifCounter.append(tifCounter)
    
    # --- Save list of processed files and frame counts to CSV ---
    with open("list_data.csv", 'w', newline='\n') as myfile:
        wr = csv.writer(myfile)
        wr.writerow(array_file_names)  
        wr.writerow(array_tifCounter)  
