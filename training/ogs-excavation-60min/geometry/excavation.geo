// OGS 60-minute training: 2D excavation, finite-width impermeable wall notch
// The wall is an excluded domain strip, width 0.2 m, reaching to y=8 m.
// Soil remains connected below the toe; no duplicate coincident vertices.
// Run: gmsh -2 geometry/excavation.geo -format msh2 -o mesh/excavation.msh
SetFactory("Built-in");
L = 65;
H = 30;
wall_x = 32.5;
wall_width = 0.2;
wall_toe = 8;
lc = 2.0;
xl = wall_x - wall_width / 2;
xr = wall_x + wall_width / 2;
Point(1) = {0,0,0,lc};
Point(2) = {L,0,0,lc};
Point(3) = {L,H,0,lc};
Point(4) = {xr,H,0,lc};
Point(5) = {xr,wall_toe,0,lc};
Point(6) = {xl,wall_toe,0,lc};
Point(7) = {xl,H,0,lc};
Point(8) = {0,H,0,lc};
Line(1) = {1,2};
Line(2) = {2,3};
Line(3) = {3,4}; // top right Dirichlet
Line(4) = {4,5}; // right wall face
Line(5) = {5,6}; // impermeable wall toe
Line(6) = {6,7}; // left wall face
Line(7) = {7,8}; // top left Dirichlet
Line(8) = {8,1};
Curve Loop(11) = {1,2,3,4,5,6,7,8};
Plane Surface(11) = {11};
Physical Surface("bulk",1) = {11};
Physical Curve("top_left",101) = {7};
Physical Curve("top_right",102) = {3};
Physical Curve("wall_left",103) = {6};
Physical Curve("wall_right",104) = {4};
Physical Curve("wall_toe",107) = {5};
Physical Curve("bottom",105) = {1};
Physical Curve("outside",106) = {2,8};
Mesh.Algorithm = 6;
Mesh.MshFileVersion = 2.1;
