union() {
  union() difference() { 
    union() { 
      union() difference() {
        // Base
        cube(size = [10,70,5], center = false);
        // CybICS Text
        translate ([2.5,55,3]) {
          rotate([0,0,270])
            linear_extrude(height = 10) {
              text("CybICS", font = "Liberation Sans", size = 6);
        }
      } 
          
      }
      // Back
      translate([0,65,0]) 
        cube(size = [10,5,70], center = false);
    }
    union() {
      translate([0,0,0])    
        rotate([45,0,0])
          cube(size = [10,100,5], center = false); 
    }
  }
  $fn=20;
  translate([5,0.5,4.5]) 
    rotate([45,0,0])
      cylinder(h = 7, r=1.5, center = true);
  translate([5,65.5,69.5]) 
    rotate([45,0,0])
      cylinder(h = 7, r=1.5, center = true);
}