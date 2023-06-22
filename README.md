Use function create_txt in foo.py passing the list of diffrent trajectories to cypcle through, 
the list of deltas in z_height for each layer (first layer will use defalut height from routes passed) 
and output path of the resulting txt

You can use the the functionality by changing parameters on run() at main.py

This project works by parsing trajectory and points from the source routes into objects, 
then it is able to make operations in the dots, such as changing z height. And at last it builds a new
route based on the objects.

It is important to know that for every use of each source route, all points will be redeclared.