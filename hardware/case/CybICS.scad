union() difference() { 
  union() { 
    // Base plate
    cube(size = [160,70.8,1], center = false);
    // Front plate
    translate([-1,-1,0])    
      cube(size = [162,1,10], center = false); 
    // Back plate
    translate([-1,70.8,0])    
      cube(size = [162,1,80.8], center = false); 
    // Left plate
    translate([-1,0,10]) {
      rotate([90,180,90]) {
        linear_extrude(1) {
          polygon(points=[[0,0],[-70.8,0],[-70.8,-70.8]], paths=[[0,1,2]]);
        }
      }
    }
    translate([0,0,8]) {
      rotate([90,180,90]) {
        linear_extrude(2) {
          polygon(points=[[0,0],[-70.8,0],[-70.8,-70.8]], paths=[[0,1,2]]);
        }
      }
    }
    translate([-1,-1,0])    
      cube(size = [1,72.8,10], center = false); 
    translate([-1,-1,0])    
      cube(size = [3,72.8,8], center = false);; 
    // Right plate
    translate([160,0,10]) {
      rotate([90,180,90]) {
        linear_extrude(1) {
          polygon(points=[[0,0],[-70.8,0],[-70.8,-70.8]], paths=[[0,1,2]]);
        }
      }
    }
    translate([158,0,8]) {
      rotate([90,180,90]) {
        linear_extrude(2) {
          polygon(points=[[0,0],[-70.8,0],[-70.8,-70.8]], paths=[[0,1,2]]);
        }
      }
    }
    translate([160,-1,0])    
      cube(size = [1,72.8,10], center = false); 
    translate([158,-1,0])    
      cube(size = [2,72.8,8], center = false);; 
  }
  
  // Baseplate honey
  $fn=6;
  for (x = [0:5]){
    translate([17.5+25*x, 10, 0])
      cylinder(h = 5, r=10, center = true);
    translate([17.5+25*x, 60, 0])
      cylinder(h = 5, r=10, center = true);
  }
  for (x = [0:4]){
    translate([30+25*x, 35, 0])
      cylinder(h = 5, r=10, center = true);
  }
  // Backplate honey
  for (x = [0:5]){
    translate([17.5+25*x, 70, 15])
      rotate([180,90,90]) {
        cylinder(h = 12, r=10, center = true);
      }
    translate([17.5+25*x, 70, 65])
      rotate([180,90,90]) {
        cylinder(h = 12, r=10, center = true);
      }
  }
  for (x = [0:4]){
    translate([30+25*x, 70, 40])
      rotate([180,90,90]) {
        cylinder(h = 10, r=10, center = true);
      }
  } 
}