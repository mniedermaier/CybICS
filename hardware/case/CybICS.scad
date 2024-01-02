union() difference() { 
  union() { 
    // Base plate
    cube(size = [164,70.8,1], center = false);
    // Front plate
    union() difference() { 
      translate([-1,-1,0])    
        cube(size = [166,2,10], center = false);
      // CybICS Text
      translate ([10,0,3]) {
        rotate([90,0,0])
          linear_extrude(height = 1) {
           text("CybICS", font = "Liberation Sans", size = 6);
        }
      } 
  }
    // Back plate
    translate([-2,70.8,0])    
      cube(size = [167,1,74], center = false); 
    // Left plate
    union() difference() { 
      union() {
        translate([-2,0,13]) {
          rotate([90,180,90]) {
            linear_extrude(7) {
              polygon(points=[[0,0],[-70.8,0],[-70.8,-70.8]], paths=[[0,1,2]]);
            }
          }
        }
        translate([-2,-1,0])    
          cube(size = [7,72.8,13], center = false); 
      }
      translate([0,0,6])    
        rotate([45,0,0])
          cube(size = [5,120,3], center = false); 
      translate([-2,10,16])    
        rotate([45,0,0])
          cube(size = [7,75,8], center = false); 
    }
    // Right plate
    union() difference() { 
      union() {
        translate([158,0,13]) {
          rotate([90,180,90]) {
            linear_extrude(7) {
              polygon(points=[[0,0],[-70.8,0],[-70.8,-70.8]], paths=[[0,1,2]]);
            }
          }
        }
        translate([158,-1,0])    
          cube(size = [7,72.8,13], center = false); 
      }
      translate([158,0,6])    
        rotate([45,0,0])
          cube(size = [5,120,3], center = false); 
      translate([158,10,16])    
        rotate([45,0,0])
          cube(size = [7,75,8], center = false); 
    }
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
    translate([17.5+25*x, 70, 55])
      rotate([180,90,90]) {
        cylinder(h = 12, r=10, center = true);
      }
  }
  for (x = [0:4]){
    translate([30+25*x, 70, 35])
      rotate([180,90,90]) {
        cylinder(h = 10, r=10, center = true);
      }
  } 
}