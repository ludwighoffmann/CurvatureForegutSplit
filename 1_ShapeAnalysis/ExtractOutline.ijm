// Run ImageJ macro to segment and extract object outlines from an input .avi file and save results as .tif sequences.


// ---- Get path passed from Python script ----
data_path = getArgument();

// ---- Open input AVI movie ----
open(data_path + ".avi");

// ---- Export each frame as an image sequence to Inside_Shape folder ----
run("Image Sequence... ", "select=[" + data_path + "/Inside_Shape] dir=[" + data_path + "/Inside_Shape/] format=TIFF name=[]");
close();

// ---- Reload sequence for processing ----
File.openSequence(data_path + "/Inside_Shape");

// ---- Convert frames to binary images ----
run("Make Binary", "background=Dark calculate black");

// ---- Detect large objects and create mask of main shape ----
run("Analyze Particles...", "size=28000-Infinity show=Masks clear include add composite stack");

// ---- Combine binary mask with original Inside_Shape stack ----
imageCalculator("AND stack", "Inside_Shape","Mask of Inside_Shape");

// ---- Close intermediate mask image ----
selectImage("Mask of Inside_Shape");
close();

// ---- Fill small internal holes within the shape, smooth contour using Gaussian blur ----
selectImage("Inside_Shape");
run("Fill Holes", "stack");
run("Gaussian Blur...", "sigma=4 stack");

// ---- Re-threshold and binarize again for clean edges ----
run("Convert to Mask", "background=Dark calculate black");

// ---- Fill holes again after blurring ----
run("Fill Holes", "stack");

// ---- Detect final large object masks after cleaning ----
run("Analyze Particles...", "size=28000-Infinity show=Masks clear include add composite stack");

// ---- Combine mask and shape again for refinement ----
imageCalculator("AND stack", "Inside_Shape","Mask of Inside_Shape");

// ---- Close intermediate mask ----
selectImage("Mask of Inside_Shape");
close();

// ---- Final cleaning of Inside_Shape ----
selectImage("Inside_Shape");
run("Close-", "stack");
run("Fill Holes", "stack");

// ---- Export final processed stack to Outline_Outside_Coords folder ----
run("Image Sequence... ", "select=[" + data_path + "/Outline_Outside_Coords] dir=[" + data_path + "/Outline_Outside_Coords/] format=TIFF name=[] digits=4");

// ---- Close all open images and ROI Manager ----
close();
close("ROI Manager");

// ---- Exit ImageJ ----
run("Quit");