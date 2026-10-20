The simple stand holds the CybICS PCB at 45 degrees on a desk, with a small packaging format.
Print the same part twice, one for each short edge of the board. It is symmetric
about its pin, so it fits either side.

Two pins go through the board's corner holes: H1 and H3 on the left, H2 and the
LCD's mounting hole on the right. A lip below the lower edge catches the board
while it is put on. The lower edge is lifted 30 mm off the desk,
so the Raspberry Pi's micro-USB and mini-HDMI ports, which point down past that
edge, stay usable. The frame is 6 mm wide and flush with the board edge, so it
stays clear of the Pi and the side USB-C jack; an 18 mm flange at the bottom
keeps it from tipping. The contact faces are relieved between the two pads,
clearing the THT pins of SW1, SW2 and the USB-C jack. The lower pin is
2.1 mm because the LCD's hole is only 2.5 mm, the upper one 2.8 mm for the
3.2 mm holes; change `pin_play` if they are too tight or too loose on your
printer.

Print upright, standing on the flange, no supports needed.
Everything is parametric (`lift`, `angle`, tolerances); open
`CybICSstandSimple.scad` in OpenSCAD and change the values at the top.
After a change, regenerate the files:

```bash
openscad --export-format binstl -o CybICSstandSimple.stl CybICSstandSimple.scad
openscad -D '$fn=20' --export-format asciistl -o CybICSstandSimple.ast CybICSstandSimple.scad
```

The preview below is the ASCII STL in `CybICSstandSimple.ast`.

```stl
solid OpenSCAD_Model
  facet normal -0.702731 -0.418234 0.575543
    outer loop
      vertex -0.523069 4.8578 34.7871
      vertex -0.998597 5.32061 34.5428
      vertex -0.549988 4.73762 34.6669
    endloop
  endfacet
  facet normal -0.323276 -0.0488098 0.945045
    outer loop
      vertex -0.169955 5.10749 35.0368
      vertex -0.617167 5.69183 34.914
      vertex -0.323275 5.05225 34.9815
    endloop
  endfacet
  facet normal -0.633929 -0.725286 0.268503
    outer loop
      vertex -0.523069 4.61744 34.5467
      vertex -0.998597 4.86174 34.0839
      vertex -0.444949 4.50903 34.4383
    endloop
  endfacet
  facet normal -0.702739 -0.575548 0.418213
    outer loop
      vertex -0.549988 4.73762 34.6669
      vertex -1.04999 5.09118 34.3133
      vertex -0.998597 4.86174 34.0839
    endloop
  endfacet
  facet normal -0.702751 -0.418258 0.575501
    outer loop
      vertex -0.998597 5.32061 34.5428
      vertex -1.04999 5.09118 34.3133
      vertex -0.549988 4.73762 34.6669
    endloop
  endfacet
  facet normal -0.111304 -0.993786 -0
    outer loop
      vertex 0 4.34872 34.278
      vertex -0.324464 4.38506 33.6072
      vertex 0 4.34872 33.5709
    endloop
  endfacet
  facet normal -0.503102 -0.852622 0.141151
    outer loop
      vertex -0.323275 4.42299 34.3523
      vertex -0.849458 4.65477 33.8769
      vertex -0.617167 4.49052 33.7127
    endloop
  endfacet
  facet normal 0.891019 -0.321001 -0.321005
    outer loop
      vertex 0.998597 4.86174 34.0839
      vertex 0.849458 6.8468 31.6849
      vertex 0.998597 7.05377 31.8919
    endloop
  endfacet
  facet normal 0.891019 -0.321001 -0.321005
    outer loop
      vertex 0.849458 6.8468 31.6849
      vertex 0.998597 4.86174 34.0839
      vertex 0.849458 4.65477 33.8769
    endloop
  endfacet
  facet normal -0.7027 -0.575631 0.418165
    outer loop
      vertex -0.549988 4.73762 34.6669
      vertex -0.998597 4.86174 34.0839
      vertex -0.523069 4.61744 34.5467
    endloop
  endfacet
  facet normal 0.323276 -0.0488098 0.945045
    outer loop
      vertex 0.617167 5.69183 34.914
      vertex 0.169955 5.10749 35.0368
      vertex 0.323275 5.05225 34.9815
    endloop
  endfacet
  facet normal 0.111185 1.97109e-05 0.9938
    outer loop
      vertex 0.324464 5.79729 35.0195
      vertex 0 5.83363 35.0558
      vertex 0.169955 5.10749 35.0368
    endloop
  endfacet
  facet normal -0.633921 -0.725304 0.268473
    outer loop
      vertex -0.444949 4.50903 34.4383
      vertex -0.998597 4.86174 34.0839
      vertex -0.849458 4.65477 33.8769
    endloop
  endfacet
  facet normal 0.7027 -0.575631 0.418165
    outer loop
      vertex 0.549988 4.73762 34.6669
      vertex 0.523069 4.61744 34.5467
      vertex 0.998597 4.86174 34.0839
    endloop
  endfacet
  facet normal -0.322936 -0.945171 0.0486301
    outer loop
      vertex -0.323275 4.42299 34.3523
      vertex -0.324464 4.38506 33.6072
      vertex -0.169955 4.36776 34.297
    endloop
  endfacet
  facet normal 0.111304 -0.993786 0
    outer loop
      vertex 0 4.34872 34.278
      vertex 0 4.34872 33.5709
      vertex 0.324464 4.38506 33.6072
    endloop
  endfacet
  facet normal -0.503121 -0.852606 0.14118
    outer loop
      vertex -0.444949 4.50903 34.4383
      vertex -0.849458 4.65477 33.8769
      vertex -0.323275 4.42299 34.3523
    endloop
  endfacet
  facet normal 0.323113 -0.0486713 0.945108
    outer loop
      vertex 0.324464 5.79729 35.0195
      vertex 0.169955 5.10749 35.0368
      vertex 0.617167 5.69183 34.914
    endloop
  endfacet
  facet normal 0.323006 -0.945147 0.048629
    outer loop
      vertex 0.617167 4.49052 33.7127
      vertex 0.323275 4.42299 34.3523
      vertex 0.324464 4.38506 33.6072
    endloop
  endfacet
  facet normal -0.323006 -0.945147 0.048629
    outer loop
      vertex -0.323275 4.42299 34.3523
      vertex -0.617167 4.49052 33.7127
      vertex -0.324464 4.38506 33.6072
    endloop
  endfacet
  facet normal -0.156489 -0.698392 -0.698398
    outer loop
      vertex -0.0791376 6.54961 31.3877
      vertex -0.324464 4.38506 33.6072
      vertex -0.324464 6.57708 31.4152
    endloop
  endfacet
  facet normal -0.111185 1.97109e-05 0.9938
    outer loop
      vertex 0 5.83363 35.0558
      vertex -0.324464 5.79729 35.0195
      vertex -0.169955 5.10749 35.0368
    endloop
  endfacet
  facet normal -0.707054 -0.500034 -0.500041
    outer loop
      vertex -0.617167 6.68254 31.5207
      vertex -0.849458 4.65477 33.8769
      vertex -0.849458 6.8468 31.6849
    endloop
  endfacet
  facet normal -0.707043 -0.500043 -0.500047
    outer loop
      vertex -0.849458 4.65477 33.8769
      vertex -0.617167 6.68254 31.5207
      vertex -0.617167 4.49052 33.7127
    endloop
  endfacet
  facet normal 0.503102 -0.852622 0.141151
    outer loop
      vertex 0.849458 4.65477 33.8769
      vertex 0.323275 4.42299 34.3523
      vertex 0.617167 4.49052 33.7127
    endloop
  endfacet
  facet normal 0.503121 -0.852606 0.14118
    outer loop
      vertex 0.444949 4.50903 34.4383
      vertex 0.323275 4.42299 34.3523
      vertex 0.849458 4.65477 33.8769
    endloop
  endfacet
  facet normal 0.987685 -0.110629 -0.11063
    outer loop
      vertex 1.04999 5.09118 34.3133
      vertex 0.998597 7.05377 31.8919
      vertex 1.04999 7.2832 32.1213
    endloop
  endfacet
  facet normal 0.987686 -0.110626 -0.110628
    outer loop
      vertex 0.998597 7.05377 31.8919
      vertex 1.04999 5.09118 34.3133
      vertex 0.998597 4.86174 34.0839
    endloop
  endfacet
  facet normal 0.702739 -0.575548 0.418213
    outer loop
      vertex 1.04999 5.09118 34.3133
      vertex 0.549988 4.73762 34.6669
      vertex 0.998597 4.86174 34.0839
    endloop
  endfacet
  facet normal 0.322936 -0.945171 0.0486301
    outer loop
      vertex 0.323275 4.42299 34.3523
      vertex 0.169955 4.36776 34.297
      vertex 0.324464 4.38506 33.6072
    endloop
  endfacet
  facet normal 0.454067 -0.630006 -0.630012
    outer loop
      vertex 0.324464 4.38506 33.6072
      vertex 0.617167 6.68254 31.5207
      vertex 0.617167 4.49052 33.7127
    endloop
  endfacet
  facet normal 0.454067 -0.630006 -0.630012
    outer loop
      vertex 0.617167 6.68254 31.5207
      vertex 0.324464 4.38506 33.6072
      vertex 0.324464 6.57708 31.4152
    endloop
  endfacet
  facet normal 0.156489 -0.698392 -0.698398
    outer loop
      vertex 0.324464 4.38506 33.6072
      vertex 0.0791376 6.54961 31.3877
      vertex 0.324464 6.57708 31.4152
    endloop
  endfacet
  facet normal -0.891019 -0.321001 -0.321005
    outer loop
      vertex -0.849458 6.8468 31.6849
      vertex -0.998597 4.86174 34.0839
      vertex -0.998597 7.05377 31.8919
    endloop
  endfacet
  facet normal -0.891019 -0.321001 -0.321005
    outer loop
      vertex -0.998597 4.86174 34.0839
      vertex -0.849458 6.8468 31.6849
      vertex -0.849458 4.65477 33.8769
    endloop
  endfacet
  facet normal -0.987685 -0.110629 -0.11063
    outer loop
      vertex -0.998597 7.05377 31.8919
      vertex -1.04999 5.09118 34.3133
      vertex -1.04999 7.2832 32.1213
    endloop
  endfacet
  facet normal -0.987686 -0.110626 -0.110628
    outer loop
      vertex -1.04999 5.09118 34.3133
      vertex -0.998597 7.05377 31.8919
      vertex -0.998597 4.86174 34.0839
    endloop
  endfacet
  facet normal -0.454067 -0.630006 -0.630012
    outer loop
      vertex -0.617167 6.68254 31.5207
      vertex -0.324464 4.38506 33.6072
      vertex -0.617167 4.49052 33.7127
    endloop
  endfacet
  facet normal -0.454067 -0.630006 -0.630012
    outer loop
      vertex -0.324464 4.38506 33.6072
      vertex -0.617167 6.68254 31.5207
      vertex -0.324464 6.57708 31.4152
    endloop
  endfacet
  facet normal -0.707162 0.499958 0.499965
    outer loop
      vertex -0.849458 7.7196 32.5577
      vertex -0.617167 5.69183 34.914
      vertex -0.617167 7.88386 32.722
    endloop
  endfacet
  facet normal -0.707151 0.499967 0.499971
    outer loop
      vertex -0.617167 5.69183 34.914
      vertex -0.849458 7.7196 32.5577
      vertex -0.849458 5.52758 34.7497
    endloop
  endfacet
  facet normal -0.323113 -0.0486713 0.945108
    outer loop
      vertex -0.324464 5.79729 35.0195
      vertex -0.617167 5.69183 34.914
      vertex -0.169955 5.10749 35.0368
    endloop
  endfacet
  facet normal 0.633921 -0.725304 0.268473
    outer loop
      vertex 0.998597 4.86174 34.0839
      vertex 0.444949 4.50903 34.4383
      vertex 0.849458 4.65477 33.8769
    endloop
  endfacet
  facet normal 0.891019 0.321002 0.321004
    outer loop
      vertex 0.849458 5.52758 34.7497
      vertex 0.998597 7.51263 32.3507
      vertex 0.849458 7.7196 32.5577
    endloop
  endfacet
  facet normal 0.890974 0.32107 0.321059
    outer loop
      vertex 0.998597 7.51263 32.3507
      vertex 0.849458 5.52758 34.7497
      vertex 0.998597 5.32061 34.5428
    endloop
  endfacet
  facet normal -0.111332 -0.993783 1.34786e-05
    outer loop
      vertex -0.169955 4.36776 34.297
      vertex -0.324464 4.38506 33.6072
      vertex 0 4.34872 34.278
    endloop
  endfacet
  facet normal -0.000386722 -0.70809 0.706122
    outer loop
      vertex 0 4.34872 34.278
      vertex -0.323275 4.42299 34.3523
      vertex -0.169955 4.36776 34.297
    endloop
  endfacet
  facet normal -0.633884 -0.268365 0.725376
    outer loop
      vertex -0.849458 5.52758 34.7497
      vertex -0.998597 5.32061 34.5428
      vertex -0.444949 4.96621 34.8955
    endloop
  endfacet
  facet normal 0.707054 -0.500034 -0.500041
    outer loop
      vertex 0.849458 4.65477 33.8769
      vertex 0.617167 6.68254 31.5207
      vertex 0.849458 6.8468 31.6849
    endloop
  endfacet
  facet normal 0.707043 -0.500043 -0.500047
    outer loop
      vertex 0.617167 6.68254 31.5207
      vertex 0.849458 4.65477 33.8769
      vertex 0.617167 4.49052 33.7127
    endloop
  endfacet
  facet normal -0.156358 -0.698414 -0.698405
    outer loop
      vertex -0.0791376 6.54961 31.3877
      vertex 0 4.34872 33.5709
      vertex -0.324464 4.38506 33.6072
    endloop
  endfacet
  facet normal -0.155866 -0.69846 -0.698469
    outer loop
      vertex 0 4.34872 33.5709
      vertex -0.0791376 6.54961 31.3877
      vertex 0 6.54075 31.3789
    endloop
  endfacet
  facet normal 0.156358 -0.698414 -0.698405
    outer loop
      vertex 0 4.34872 33.5709
      vertex 0.0791376 6.54961 31.3877
      vertex 0.324464 4.38506 33.6072
    endloop
  endfacet
  facet normal 0.155866 -0.69846 -0.698469
    outer loop
      vertex 0.0791376 6.54961 31.3877
      vertex 0 4.34872 33.5709
      vertex 0 6.54075 31.3789
    endloop
  endfacet
  facet normal -0.987685 0.110631 0.110627
    outer loop
      vertex -1.04999 7.2832 32.1213
      vertex -0.998597 5.32061 34.5428
      vertex -0.998597 7.51263 32.3507
    endloop
  endfacet
  facet normal -0.987691 0.110605 0.110606
    outer loop
      vertex -0.998597 5.32061 34.5428
      vertex -1.04999 7.2832 32.1213
      vertex -1.04999 5.09118 34.3133
    endloop
  endfacet
  facet normal -0.000368246 -0.707207 0.707007
    outer loop
      vertex 0.523069 4.8578 34.7871
      vertex 0.444949 4.96621 34.8955
      vertex 0.549988 4.73762 34.6669
    endloop
  endfacet
  facet normal -0.503165 -0.141229 0.852572
    outer loop
      vertex -0.617167 5.69183 34.914
      vertex -0.849458 5.52758 34.7497
      vertex -0.323275 5.05225 34.9815
    endloop
  endfacet
  facet normal 0.111102 0 0.993809
    outer loop
      vertex 0 5.83363 35.0558
      vertex 0 5.12652 35.0558
      vertex 0.169955 5.10749 35.0368
    endloop
  endfacet
  facet normal 0.987685 0.110631 0.110627
    outer loop
      vertex 0.998597 5.32061 34.5428
      vertex 1.04999 7.2832 32.1213
      vertex 0.998597 7.51263 32.3507
    endloop
  endfacet
  facet normal 0.987691 0.110605 0.110606
    outer loop
      vertex 1.04999 7.2832 32.1213
      vertex 0.998597 5.32061 34.5428
      vertex 1.04999 5.09118 34.3133
    endloop
  endfacet
  facet normal 0.453896 0.630081 0.630061
    outer loop
      vertex 0.324464 5.79729 35.0195
      vertex 0.617167 7.88386 32.722
      vertex 0.324464 7.98932 32.8274
    endloop
  endfacet
  facet normal 0.454067 0.630005 0.630014
    outer loop
      vertex 0.617167 7.88386 32.722
      vertex 0.324464 5.79729 35.0195
      vertex 0.617167 5.69183 34.914
    endloop
  endfacet
  facet normal 0.707162 0.499958 0.499965
    outer loop
      vertex 0.617167 5.69183 34.914
      vertex 0.849458 7.7196 32.5577
      vertex 0.617167 7.88386 32.722
    endloop
  endfacet
  facet normal 0.707151 0.499967 0.499971
    outer loop
      vertex 0.849458 7.7196 32.5577
      vertex 0.617167 5.69183 34.914
      vertex 0.849458 5.52758 34.7497
    endloop
  endfacet
  facet normal 0.000386722 -0.70809 0.706122
    outer loop
      vertex 0.323275 4.42299 34.3523
      vertex 0 4.34872 34.278
      vertex 0.169955 4.36776 34.297
    endloop
  endfacet
  facet normal 0.111332 -0.993783 1.34786e-05
    outer loop
      vertex 0.169955 4.36776 34.297
      vertex 0 4.34872 34.278
      vertex 0.324464 4.38506 33.6072
    endloop
  endfacet
  facet normal 0.503004 -0.140985 0.852708
    outer loop
      vertex 0.849458 5.52758 34.7497
      vertex 0.323275 5.05225 34.9815
      vertex 0.444949 4.96621 34.8955
    endloop
  endfacet
  facet normal -0.156547 0.698385 0.698392
    outer loop
      vertex -0.324464 7.98932 32.8274
      vertex 0 5.83363 35.0558
      vertex 0 8.02565 32.8638
    endloop
  endfacet
  facet normal -0.156358 0.698421 0.698399
    outer loop
      vertex 0 5.83363 35.0558
      vertex -0.324464 7.98932 32.8274
      vertex -0.324464 5.79729 35.0195
    endloop
  endfacet
  facet normal 0.702751 -0.418258 0.575501
    outer loop
      vertex 0.998597 5.32061 34.5428
      vertex 0.549988 4.73762 34.6669
      vertex 1.04999 5.09118 34.3133
    endloop
  endfacet
  facet normal -0.633909 -0.26846 0.72532
    outer loop
      vertex -0.444949 4.96621 34.8955
      vertex -0.998597 5.32061 34.5428
      vertex -0.523069 4.8578 34.7871
    endloop
  endfacet
  facet normal 0.000368246 -0.707207 0.707007
    outer loop
      vertex -0.523069 4.8578 34.7871
      vertex -0.549988 4.73762 34.6669
      vertex -0.444949 4.96621 34.8955
    endloop
  endfacet
  facet normal -0.453896 0.630081 0.630061
    outer loop
      vertex -0.617167 7.88386 32.722
      vertex -0.324464 5.79729 35.0195
      vertex -0.324464 7.98932 32.8274
    endloop
  endfacet
  facet normal -0.454067 0.630005 0.630014
    outer loop
      vertex -0.324464 5.79729 35.0195
      vertex -0.617167 7.88386 32.722
      vertex -0.617167 5.69183 34.914
    endloop
  endfacet
  facet normal 0.633884 -0.268365 0.725376
    outer loop
      vertex 0.849458 5.52758 34.7497
      vertex 0.444949 4.96621 34.8955
      vertex 0.998597 5.32061 34.5428
    endloop
  endfacet
  facet normal 0.503165 -0.141229 0.852572
    outer loop
      vertex 0.617167 5.69183 34.914
      vertex 0.323275 5.05225 34.9815
      vertex 0.849458 5.52758 34.7497
    endloop
  endfacet
  facet normal -0.111102 0 0.993809
    outer loop
      vertex 0 5.83363 35.0558
      vertex -0.169955 5.10749 35.0368
      vertex 0 5.12652 35.0558
    endloop
  endfacet
  facet normal 0.633929 -0.725286 0.268503
    outer loop
      vertex 0.523069 4.61744 34.5467
      vertex 0.444949 4.50903 34.4383
      vertex 0.998597 4.86174 34.0839
    endloop
  endfacet
  facet normal 0.156547 0.698385 0.698392
    outer loop
      vertex 0 5.83363 35.0558
      vertex 0.324464 7.98932 32.8274
      vertex 0 8.02565 32.8638
    endloop
  endfacet
  facet normal 0.156358 0.698421 0.698399
    outer loop
      vertex 0.324464 7.98932 32.8274
      vertex 0 5.83363 35.0558
      vertex 0.324464 5.79729 35.0195
    endloop
  endfacet
  facet normal -0.503004 -0.140985 0.852708
    outer loop
      vertex -0.323275 5.05225 34.9815
      vertex -0.849458 5.52758 34.7497
      vertex -0.444949 4.96621 34.8955
    endloop
  endfacet
  facet normal -0.891019 0.321002 0.321004
    outer loop
      vertex -0.998597 7.51263 32.3507
      vertex -0.849458 5.52758 34.7497
      vertex -0.849458 7.7196 32.5577
    endloop
  endfacet
  facet normal -0.890974 0.32107 0.321059
    outer loop
      vertex -0.849458 5.52758 34.7497
      vertex -0.998597 7.51263 32.3507
      vertex -0.998597 5.32061 34.5428
    endloop
  endfacet
  facet normal 0.702731 -0.418234 0.575543
    outer loop
      vertex 0.998597 5.32061 34.5428
      vertex 0.523069 4.8578 34.7871
      vertex 0.549988 4.73762 34.6669
    endloop
  endfacet
  facet normal 0.633909 -0.26846 0.72532
    outer loop
      vertex 0.998597 5.32061 34.5428
      vertex 0.444949 4.96621 34.8955
      vertex 0.523069 4.8578 34.7871
    endloop
  endfacet
  facet normal 0.000124817 -0.707107 0.707107
    outer loop
      vertex 0 4.34872 34.278
      vertex 0 5.12652 35.0558
      vertex -0.169955 5.10749 35.0368
    endloop
  endfacet
  facet normal -0.000301024 -0.707073 0.70714
    outer loop
      vertex -0.323275 4.42299 34.3523
      vertex -0.169955 5.10749 35.0368
      vertex -0.323275 5.05225 34.9815
    endloop
  endfacet
  facet normal -0.000124817 -0.707107 0.707107
    outer loop
      vertex 0 5.12652 35.0558
      vertex 0 4.34872 34.278
      vertex 0.169955 5.10749 35.0368
    endloop
  endfacet
  facet normal 0.000184791 -0.707073 0.70714
    outer loop
      vertex -0.323275 4.42299 34.3523
      vertex -0.323275 5.05225 34.9815
      vertex -0.444949 4.96621 34.8955
    endloop
  endfacet
  facet normal -6.24076e-05 -0.707114 0.7071
    outer loop
      vertex 0.323275 4.42299 34.3523
      vertex 0.169955 5.10749 35.0368
      vertex 0 4.34872 34.278
    endloop
  endfacet
  facet normal 0.0001269 -0.707151 0.707062
    outer loop
      vertex -0.523069 4.61744 34.5467
      vertex -0.444949 4.96621 34.8955
      vertex -0.549988 4.73762 34.6669
    endloop
  endfacet
  facet normal 0.000301024 -0.707073 0.70714
    outer loop
      vertex 0.169955 5.10749 35.0368
      vertex 0.323275 4.42299 34.3523
      vertex 0.323275 5.05225 34.9815
    endloop
  endfacet
  facet normal -0.00013344 -0.707122 0.707091
    outer loop
      vertex -0.444949 4.96621 34.8955
      vertex -0.523069 4.61744 34.5467
      vertex -0.444949 4.50903 34.4383
    endloop
  endfacet
  facet normal -0.000184791 -0.707073 0.70714
    outer loop
      vertex 0.323275 5.05225 34.9815
      vertex 0.323275 4.42299 34.3523
      vertex 0.444949 4.96621 34.8955
    endloop
  endfacet
  facet normal -0.000254328 -0.707122 0.707091
    outer loop
      vertex -0.444949 4.96621 34.8955
      vertex -0.444949 4.50903 34.4383
      vertex -0.323275 4.42299 34.3523
    endloop
  endfacet
  facet normal 0.000254328 -0.707122 0.707091
    outer loop
      vertex 0.444949 4.50903 34.4383
      vertex 0.444949 4.96621 34.8955
      vertex 0.323275 4.42299 34.3523
    endloop
  endfacet
  facet normal 6.24076e-05 -0.707114 0.7071
    outer loop
      vertex -0.169955 5.10749 35.0368
      vertex -0.323275 4.42299 34.3523
      vertex 0 4.34872 34.278
    endloop
  endfacet
  facet normal 0.00013344 -0.707122 0.707091
    outer loop
      vertex 0.523069 4.61744 34.5467
      vertex 0.444949 4.96621 34.8955
      vertex 0.444949 4.50903 34.4383
    endloop
  endfacet
  facet normal -0.0001269 -0.707151 0.707062
    outer loop
      vertex 0.444949 4.96621 34.8955
      vertex 0.523069 4.61744 34.5467
      vertex 0.549988 4.73762 34.6669
    endloop
  endfacet
  facet normal -0.703293 -0.418358 0.574765
    outer loop
      vertex -0.855945 71.4023 101.332
      vertex -1.33147 71.8651 101.087
      vertex -0.899994 71.2057 101.135
    endloop
  endfacet
  facet normal -0.987692 -0.110591 -0.110611
    outer loop
      vertex -1.33147 73.4453 98.2834
      vertex -1.39999 71.5592 100.781
      vertex -1.39999 73.7512 98.5894
    endloop
  endfacet
  facet normal -0.987692 -0.110591 -0.110611
    outer loop
      vertex -1.39999 71.5592 100.781
      vertex -1.33147 73.4453 98.2834
      vertex -1.33147 71.2533 100.475
    endloop
  endfacet
  facet normal 0.502912 -0.852733 0.141158
    outer loop
      vertex 1.13262 70.9773 100.2
      vertex 0.72811 70.8316 100.761
      vertex 0.822895 70.7583 99.9805
    endloop
  endfacet
  facet normal -0.702837 -0.575772 0.417741
    outer loop
      vertex -0.899994 71.2057 101.135
      vertex -1.39999 71.5592 100.781
      vertex -0.855945 71.009 100.938
    endloop
  endfacet
  facet normal -0.702958 -0.418095 0.575366
    outer loop
      vertex -1.33147 71.8651 101.087
      vertex -1.39999 71.5592 100.781
      vertex -0.899994 71.2057 101.135
    endloop
  endfacet
  facet normal 0.322985 -0.945154 0.04862
    outer loop
      vertex 0.822895 70.7583 99.9805
      vertex 0.278113 70.6004 100.53
      vertex 0.432621 70.6177 99.8399
    endloop
  endfacet
  facet normal -0.634228 -0.724875 0.268907
    outer loop
      vertex -0.855945 71.009 100.938
      vertex -1.33147 71.2533 100.475
      vertex -1.13262 70.9773 100.2
    endloop
  endfacet
  facet normal -0.503238 -0.140874 0.852588
    outer loop
      vertex -0.822895 72.3601 101.582
      vertex -1.13262 72.1411 101.363
      vertex -0.72811 71.5797 101.509
    endloop
  endfacet
  facet normal 0.706983 0.500053 0.500122
    outer loop
      vertex 1.01329 74.4262 99.2469
      vertex 1.13262 72.1411 101.363
      vertex 1.13262 74.3352 99.1692
    endloop
  endfacet
  facet normal 0.707183 0.499923 0.49997
    outer loop
      vertex 1.13262 72.1411 101.363
      vertex 1.01329 74.4262 99.2469
      vertex 0.894594 74.5374 99.3036
    endloop
  endfacet
  facet normal -0.111132 -0.993806 -0
    outer loop
      vertex 0 70.5693 100.499
      vertex -0.278113 70.6004 100.53
      vertex 0 70.5693 99.7914
    endloop
  endfacet
  facet normal 0.891034 0.320955 0.321009
    outer loop
      vertex 1.33147 71.8651 101.087
      vertex 1.28297 74.1245 98.9626
      vertex 1.13262 72.1411 101.363
    endloop
  endfacet
  facet normal 0.891123 0.320835 0.320879
    outer loop
      vertex 1.28297 74.1245 98.9626
      vertex 1.33147 71.8651 101.087
      vertex 1.33147 74.0571 98.8953
    endloop
  endfacet
  facet normal -0.502912 -0.852733 0.141158
    outer loop
      vertex -0.72811 70.8316 100.761
      vertex -1.13262 70.9773 100.2
      vertex -0.822895 70.7583 99.9805
    endloop
  endfacet
  facet normal 0.32307 -0.945121 0.0487136
    outer loop
      vertex 0.529002 70.6908 100.62
      vertex 0.278113 70.6004 100.53
      vertex 0.822895 70.7583 99.9805
    endloop
  endfacet
  facet normal -0.891123 0.320835 0.320879
    outer loop
      vertex -1.33147 71.8651 101.087
      vertex -1.28297 74.1245 98.9626
      vertex -1.33147 74.0571 98.8953
    endloop
  endfacet
  facet normal -0.891034 0.320955 0.321009
    outer loop
      vertex -1.28297 74.1245 98.9626
      vertex -1.33147 71.8651 101.087
      vertex -1.13262 72.1411 101.363
    endloop
  endfacet
  facet normal -0.111185 -0.9938 -1.99903e-05
    outer loop
      vertex -0.278113 70.6004 100.53
      vertex -0.432621 70.6177 99.8399
      vertex 0 70.5693 99.7914
    endloop
  endfacet
  facet normal 0.707013 -0.500055 -0.500078
    outer loop
      vertex 1.05708 73.1159 97.9541
      vertex 0.822895 70.7583 99.9805
      vertex 0.822895 72.9504 97.7885
    endloop
  endfacet
  facet normal 0.634228 -0.724875 0.268907
    outer loop
      vertex 1.33147 71.2533 100.475
      vertex 0.855945 71.009 100.938
      vertex 1.13262 70.9773 100.2
    endloop
  endfacet
  facet normal 0.702773 -0.575616 0.418062
    outer loop
      vertex 1.39999 71.5592 100.781
      vertex 0.855945 71.009 100.938
      vertex 1.33147 71.2533 100.475
    endloop
  endfacet
  facet normal 0.454106 -0.629981 -0.630009
    outer loop
      vertex 0.822895 70.7583 99.9805
      vertex 0.52781 72.844 97.6822
      vertex 0.822895 72.9504 97.7885
    endloop
  endfacet
  facet normal -0.453932 0.630071 0.630044
    outer loop
      vertex -0.513959 74.7663 99.3987
      vertex -0.432621 72.5007 101.723
      vertex -0.432621 74.8169 99.4067
    endloop
  endfacet
  facet normal -0.454474 0.629864 0.629861
    outer loop
      vertex -0.432621 72.5007 101.723
      vertex -0.513959 74.7663 99.3987
      vertex -0.822895 72.3601 101.582
    endloop
  endfacet
  facet normal 0.503238 -0.140874 0.852588
    outer loop
      vertex 0.822895 72.3601 101.582
      vertex 0.72811 71.5797 101.509
      vertex 1.13262 72.1411 101.363
    endloop
  endfacet
  facet normal 0.987692 -0.110591 -0.110611
    outer loop
      vertex 1.39999 71.5592 100.781
      vertex 1.33147 73.4453 98.2834
      vertex 1.39999 73.7512 98.5894
    endloop
  endfacet
  facet normal 0.987692 -0.110591 -0.110611
    outer loop
      vertex 1.33147 73.4453 98.2834
      vertex 1.39999 71.5592 100.781
      vertex 1.33147 71.2533 100.475
    endloop
  endfacet
  facet normal -0.322985 -0.945154 0.04862
    outer loop
      vertex -0.278113 70.6004 100.53
      vertex -0.822895 70.7583 99.9805
      vertex -0.432621 70.6177 99.8399
    endloop
  endfacet
  facet normal -0.702773 -0.575616 0.418062
    outer loop
      vertex -0.855945 71.009 100.938
      vertex -1.39999 71.5592 100.781
      vertex -1.33147 71.2533 100.475
    endloop
  endfacet
  facet normal 0.702837 -0.575772 0.417741
    outer loop
      vertex 0.899994 71.2057 101.135
      vertex 0.855945 71.009 100.938
      vertex 1.39999 71.5592 100.781
    endloop
  endfacet
  facet normal -0.634007 -0.725095 0.268834
    outer loop
      vertex -0.855945 71.009 100.938
      vertex -1.13262 70.9773 100.2
      vertex -0.72811 70.8316 100.761
    endloop
  endfacet
  facet normal -0.503007 -0.852676 0.141164
    outer loop
      vertex -0.72811 70.8316 100.761
      vertex -0.822895 70.7583 99.9805
      vertex -0.529002 70.6908 100.62
    endloop
  endfacet
  facet normal -0.323649 -0.0492072 0.944897
    outer loop
      vertex -0.432621 72.5007 101.723
      vertex -0.822895 72.3601 101.582
      vertex -0.278113 71.8109 101.74
    endloop
  endfacet
  facet normal 0.110779 0 0.993845
    outer loop
      vertex 0 72.5492 101.771
      vertex 0 71.842 101.771
      vertex 0.278113 71.8109 101.74
    endloop
  endfacet
  facet normal -0.707107 0.499966 0.500033
    outer loop
      vertex -0.894594 74.5374 99.3036
      vertex -0.822895 72.3601 101.582
      vertex -0.822895 74.6046 99.3378
    endloop
  endfacet
  facet normal -0.707093 0.499977 0.500043
    outer loop
      vertex -0.822895 72.3601 101.582
      vertex -0.894594 74.5374 99.3036
      vertex -1.13262 72.1411 101.363
    endloop
  endfacet
  facet normal 0.453932 0.630071 0.630044
    outer loop
      vertex 0.432621 72.5007 101.723
      vertex 0.513959 74.7663 99.3987
      vertex 0.432621 74.8169 99.4067
    endloop
  endfacet
  facet normal 0.454474 0.629864 0.629861
    outer loop
      vertex 0.513959 74.7663 99.3987
      vertex 0.432621 72.5007 101.723
      vertex 0.822895 72.3601 101.582
    endloop
  endfacet
  facet normal 0.890997 0.321012 0.321053
    outer loop
      vertex 1.15153 74.3069 99.145
      vertex 1.13262 72.1411 101.363
      vertex 1.28297 74.1245 98.9626
    endloop
  endfacet
  facet normal 0.891056 0.32093 0.320973
    outer loop
      vertex 1.13262 72.1411 101.363
      vertex 1.15153 74.3069 99.145
      vertex 1.13262 74.3352 99.1692
    endloop
  endfacet
  facet normal -0.32307 -0.945121 0.0487136
    outer loop
      vertex -0.529002 70.6908 100.62
      vertex -0.822895 70.7583 99.9805
      vertex -0.278113 70.6004 100.53
    endloop
  endfacet
  facet normal -0.707339 -0.499881 -0.49979
    outer loop
      vertex -1.05708 73.1159 97.9541
      vertex -1.13262 70.9773 100.2
      vertex -1.13262 73.1694 98.0075
    endloop
  endfacet
  facet normal -0.707496 -0.499765 -0.499684
    outer loop
      vertex -1.13262 70.9773 100.2
      vertex -1.05708 73.1159 97.9541
      vertex -0.822895 70.7583 99.9805
    endloop
  endfacet
  facet normal 0.453961 -0.630045 -0.630049
    outer loop
      vertex 0.432621 70.6177 99.8399
      vertex 0.52781 72.844 97.6822
      vertex 0.822895 70.7583 99.9805
    endloop
  endfacet
  facet normal 0.454037 -0.63002 -0.63002
    outer loop
      vertex 0.52781 72.844 97.6822
      vertex 0.432621 70.6177 99.8399
      vertex 0.432621 72.8097 97.6479
    endloop
  endfacet
  facet normal -0.890967 -0.321045 -0.321104
    outer loop
      vertex -1.13262 73.1694 98.0075
      vertex -1.33147 71.2533 100.475
      vertex -1.33147 73.4453 98.2834
    endloop
  endfacet
  facet normal -0.8907 -0.321474 -0.321415
    outer loop
      vertex -1.33147 71.2533 100.475
      vertex -1.13262 73.1694 98.0075
      vertex -1.13262 70.9773 100.2
    endloop
  endfacet
  facet normal 0.323649 -0.0492072 0.944897
    outer loop
      vertex 0.432621 72.5007 101.723
      vertex 0.278113 71.8109 101.74
      vertex 0.822895 72.3601 101.582
    endloop
  endfacet
  facet normal -0.110779 0 0.993845
    outer loop
      vertex 0 72.5492 101.771
      vertex -0.278113 71.8109 101.74
      vertex 0 71.842 101.771
    endloop
  endfacet
  facet normal 0.890967 -0.321045 -0.321104
    outer loop
      vertex 1.33147 71.2533 100.475
      vertex 1.13262 73.1694 98.0075
      vertex 1.33147 73.4453 98.2834
    endloop
  endfacet
  facet normal 0.8907 -0.321474 -0.321415
    outer loop
      vertex 1.13262 73.1694 98.0075
      vertex 1.33147 71.2533 100.475
      vertex 1.13262 70.9773 100.2
    endloop
  endfacet
  facet normal -0.15643 -0.698402 -0.698402
    outer loop
      vertex -0.432621 72.8097 97.6479
      vertex 0 70.5693 99.7914
      vertex -0.432621 70.6177 99.8399
    endloop
  endfacet
  facet normal -0.15643 -0.698402 -0.698402
    outer loop
      vertex 0 70.5693 99.7914
      vertex -0.432621 72.8097 97.6479
      vertex 0 72.7613 97.5994
    endloop
  endfacet
  facet normal 0.707339 -0.499881 -0.49979
    outer loop
      vertex 1.13262 70.9773 100.2
      vertex 1.05708 73.1159 97.9541
      vertex 1.13262 73.1694 98.0075
    endloop
  endfacet
  facet normal 0.707496 -0.499765 -0.499684
    outer loop
      vertex 1.05708 73.1159 97.9541
      vertex 1.13262 70.9773 100.2
      vertex 0.822895 70.7583 99.9805
    endloop
  endfacet
  facet normal 0.634007 -0.725095 0.268834
    outer loop
      vertex 0.855945 71.009 100.938
      vertex 0.72811 70.8316 100.761
      vertex 1.13262 70.9773 100.2
    endloop
  endfacet
  facet normal 0.503007 -0.852676 0.141164
    outer loop
      vertex 0.72811 70.8316 100.761
      vertex 0.529002 70.6908 100.62
      vertex 0.822895 70.7583 99.9805
    endloop
  endfacet
  facet normal -0.322078 -0.0474687 0.945522
    outer loop
      vertex -0.278113 71.8109 101.74
      vertex -0.822895 72.3601 101.582
      vertex -0.529002 71.7205 101.65
    endloop
  endfacet
  facet normal -0.156034 0.698439 0.698453
    outer loop
      vertex -0.432621 74.8169 99.4067
      vertex 0 72.5492 101.771
      vertex -0.346678 74.8335 99.4093
    endloop
  endfacet
  facet normal -0.1558 0.698487 0.698457
    outer loop
      vertex 0 72.5492 101.771
      vertex -0.432621 74.8169 99.4067
      vertex -0.432621 72.5007 101.723
    endloop
  endfacet
  facet normal 0.503856 -0.140915 0.852216
    outer loop
      vertex 0.822895 72.3601 101.582
      vertex 0.529002 71.7205 101.65
      vertex 0.72811 71.5797 101.509
    endloop
  endfacet
  facet normal -0.454056 0.629979 0.630047
    outer loop
      vertex -0.612608 74.705 99.3889
      vertex -0.822895 72.3601 101.582
      vertex -0.513959 74.7663 99.3987
    endloop
  endfacet
  facet normal -0.453916 0.630022 0.630106
    outer loop
      vertex -0.822895 72.3601 101.582
      vertex -0.612608 74.705 99.3889
      vertex -0.822895 74.6046 99.3378
    endloop
  endfacet
  facet normal -0.453961 -0.630045 -0.630049
    outer loop
      vertex -0.52781 72.844 97.6822
      vertex -0.432621 70.6177 99.8399
      vertex -0.822895 70.7583 99.9805
    endloop
  endfacet
  facet normal -0.454037 -0.63002 -0.63002
    outer loop
      vertex -0.432621 70.6177 99.8399
      vertex -0.52781 72.844 97.6822
      vertex -0.432621 72.8097 97.6479
    endloop
  endfacet
  facet normal 0.111132 -0.993806 0
    outer loop
      vertex 0 70.5693 100.499
      vertex 0 70.5693 99.7914
      vertex 0.278113 70.6004 100.53
    endloop
  endfacet
  facet normal 0.111185 -0.9938 -1.99903e-05
    outer loop
      vertex 0.278113 70.6004 100.53
      vertex 0 70.5693 99.7914
      vertex 0.432621 70.6177 99.8399
    endloop
  endfacet
  facet normal 0.15643 -0.698402 -0.698402
    outer loop
      vertex 0 70.5693 99.7914
      vertex 0.432621 72.8097 97.6479
      vertex 0.432621 70.6177 99.8399
    endloop
  endfacet
  facet normal 0.15643 -0.698402 -0.698402
    outer loop
      vertex 0.432621 72.8097 97.6479
      vertex 0 70.5693 99.7914
      vertex 0 72.7613 97.5994
    endloop
  endfacet
  facet normal 0.156521 0.698347 0.698436
    outer loop
      vertex 0 74.9006 99.4199
      vertex 0 72.5492 101.771
      vertex 0.346678 74.8335 99.4093
    endloop
  endfacet
  facet normal 0.987688 0.110611 0.110626
    outer loop
      vertex 1.33147 71.8651 101.087
      vertex 1.39999 73.7512 98.5894
      vertex 1.33147 74.0571 98.8953
    endloop
  endfacet
  facet normal 0.987692 0.110591 0.110611
    outer loop
      vertex 1.39999 73.7512 98.5894
      vertex 1.33147 71.8651 101.087
      vertex 1.39999 71.5592 100.781
    endloop
  endfacet
  facet normal -0.110253 -0.000200873 0.993904
    outer loop
      vertex 0 72.5492 101.771
      vertex -0.432621 72.5007 101.723
      vertex -0.278113 71.8109 101.74
    endloop
  endfacet
  facet normal 0.634124 -0.268316 0.725185
    outer loop
      vertex 1.13262 72.1411 101.363
      vertex 0.72811 71.5797 101.509
      vertex 1.33147 71.8651 101.087
    endloop
  endfacet
  facet normal 0.322078 -0.0474687 0.945522
    outer loop
      vertex 0.822895 72.3601 101.582
      vertex 0.278113 71.8109 101.74
      vertex 0.529002 71.7205 101.65
    endloop
  endfacet
  facet normal -0.634124 -0.268316 0.725185
    outer loop
      vertex -1.13262 72.1411 101.363
      vertex -1.33147 71.8651 101.087
      vertex -0.72811 71.5797 101.509
    endloop
  endfacet
  facet normal -0.987688 0.110611 0.110626
    outer loop
      vertex -1.39999 73.7512 98.5894
      vertex -1.33147 71.8651 101.087
      vertex -1.33147 74.0571 98.8953
    endloop
  endfacet
  facet normal -0.987692 0.110591 0.110611
    outer loop
      vertex -1.33147 71.8651 101.087
      vertex -1.39999 73.7512 98.5894
      vertex -1.39999 71.5592 100.781
    endloop
  endfacet
  facet normal -0.454106 -0.629981 -0.630009
    outer loop
      vertex -0.52781 72.844 97.6822
      vertex -0.822895 70.7583 99.9805
      vertex -0.822895 72.9504 97.7885
    endloop
  endfacet
  facet normal -0.707013 -0.500055 -0.500078
    outer loop
      vertex -0.822895 70.7583 99.9805
      vertex -1.05708 73.1159 97.9541
      vertex -0.822895 72.9504 97.7885
    endloop
  endfacet
  facet normal -0.00609603 -0.708493 0.705691
    outer loop
      vertex 0.855945 71.4023 101.332
      vertex 0.72811 71.5797 101.509
      vertex 0.899994 71.2057 101.135
    endloop
  endfacet
  facet normal 0.633979 -0.267229 0.725713
    outer loop
      vertex 1.33147 71.8651 101.087
      vertex 0.72811 71.5797 101.509
      vertex 0.855945 71.4023 101.332
    endloop
  endfacet
  facet normal 0.703293 -0.418358 0.574765
    outer loop
      vertex 1.33147 71.8651 101.087
      vertex 0.855945 71.4023 101.332
      vertex 0.899994 71.2057 101.135
    endloop
  endfacet
  facet normal 0.702958 -0.418095 0.575366
    outer loop
      vertex 1.33147 71.8651 101.087
      vertex 0.899994 71.2057 101.135
      vertex 1.39999 71.5592 100.781
    endloop
  endfacet
  facet normal 0.707107 0.499966 0.500033
    outer loop
      vertex 0.822895 72.3601 101.582
      vertex 0.894594 74.5374 99.3036
      vertex 0.822895 74.6046 99.3378
    endloop
  endfacet
  facet normal 0.707093 0.499977 0.500043
    outer loop
      vertex 0.894594 74.5374 99.3036
      vertex 0.822895 72.3601 101.582
      vertex 1.13262 72.1411 101.363
    endloop
  endfacet
  facet normal 0.453916 0.630022 0.630106
    outer loop
      vertex 0.612608 74.705 99.3889
      vertex 0.822895 72.3601 101.582
      vertex 0.822895 74.6046 99.3378
    endloop
  endfacet
  facet normal 0.454056 0.629979 0.630047
    outer loop
      vertex 0.822895 72.3601 101.582
      vertex 0.612608 74.705 99.3889
      vertex 0.513959 74.7663 99.3987
    endloop
  endfacet
  facet normal -0.156521 0.698347 0.698436
    outer loop
      vertex 0 74.9006 99.4199
      vertex -0.346678 74.8335 99.4093
      vertex 0 72.5492 101.771
    endloop
  endfacet
  facet normal 0.000210819 -0.706912 0.707301
    outer loop
      vertex 0 70.5693 100.499
      vertex 0 71.842 101.771
      vertex -0.278113 71.8109 101.74
    endloop
  endfacet
  facet normal 0.00102233 -0.70696 0.707252
    outer loop
      vertex -0.278113 70.6004 100.53
      vertex -0.278113 71.8109 101.74
      vertex -0.529002 71.7205 101.65
    endloop
  endfacet
  facet normal -0.000210819 -0.706912 0.707301
    outer loop
      vertex 0 71.842 101.771
      vertex 0 70.5693 100.499
      vertex 0.278113 71.8109 101.74
    endloop
  endfacet
  facet normal -0.000564509 -0.70721 0.707004
    outer loop
      vertex -0.529002 70.6908 100.62
      vertex -0.529002 71.7205 101.65
      vertex -0.72811 71.5797 101.509
    endloop
  endfacet
  facet normal 0.000221636 -0.706961 0.707253
    outer loop
      vertex 0.278113 70.6004 100.53
      vertex 0.278113 71.8109 101.74
      vertex 0 70.5693 100.499
    endloop
  endfacet
  facet normal 0.00157698 -0.707468 0.706743
    outer loop
      vertex -0.855945 71.009 100.938
      vertex -0.72811 71.5797 101.509
      vertex -0.899994 71.2057 101.135
    endloop
  endfacet
  facet normal -0.000221636 -0.706961 0.707253
    outer loop
      vertex -0.278113 71.8109 101.74
      vertex -0.278113 70.6004 100.53
      vertex 0 70.5693 100.499
    endloop
  endfacet
  facet normal -0.00208153 -0.707058 0.707153
    outer loop
      vertex -0.72811 71.5797 101.509
      vertex -0.855945 71.009 100.938
      vertex -0.72811 70.8316 100.761
    endloop
  endfacet
  facet normal 0.00120142 -0.707209 0.707003
    outer loop
      vertex 0.529002 70.6908 100.62
      vertex 0.529002 71.7205 101.65
      vertex 0.278113 70.6004 100.53
    endloop
  endfacet
  facet normal 0.000777167 -0.707059 0.707154
    outer loop
      vertex -0.72811 71.5797 101.509
      vertex -0.72811 70.8316 100.761
      vertex -0.529002 70.6908 100.62
    endloop
  endfacet
  facet normal 0.000564509 -0.70721 0.707004
    outer loop
      vertex 0.529002 71.7205 101.65
      vertex 0.529002 70.6908 100.62
      vertex 0.72811 71.5797 101.509
    endloop
  endfacet
  facet normal -0.00120142 -0.707209 0.707003
    outer loop
      vertex -0.529002 71.7205 101.65
      vertex -0.529002 70.6908 100.62
      vertex -0.278113 70.6004 100.53
    endloop
  endfacet
  facet normal -0.00102233 -0.70696 0.707252
    outer loop
      vertex 0.278113 71.8109 101.74
      vertex 0.278113 70.6004 100.53
      vertex 0.529002 71.7205 101.65
    endloop
  endfacet
  facet normal -0.000777167 -0.707059 0.707154
    outer loop
      vertex 0.72811 70.8316 100.761
      vertex 0.72811 71.5797 101.509
      vertex 0.529002 70.6908 100.62
    endloop
  endfacet
  facet normal 0.00208153 -0.707058 0.707153
    outer loop
      vertex 0.855945 71.009 100.938
      vertex 0.72811 71.5797 101.509
      vertex 0.72811 70.8316 100.761
    endloop
  endfacet
  facet normal -0.00157698 -0.707468 0.706743
    outer loop
      vertex 0.72811 71.5797 101.509
      vertex 0.855945 71.009 100.938
      vertex 0.899994 71.2057 101.135
    endloop
  endfacet
  facet normal 0.110253 -0.000200873 0.993904
    outer loop
      vertex 0.432621 72.5007 101.723
      vertex 0 72.5492 101.771
      vertex 0.278113 71.8109 101.74
    endloop
  endfacet
  facet normal 0.156034 0.698439 0.698453
    outer loop
      vertex 0 72.5492 101.771
      vertex 0.432621 74.8169 99.4067
      vertex 0.346678 74.8335 99.4093
    endloop
  endfacet
  facet normal 0.1558 0.698487 0.698457
    outer loop
      vertex 0.432621 74.8169 99.4067
      vertex 0 72.5492 101.771
      vertex 0.432621 72.5007 101.723
    endloop
  endfacet
  facet normal -0.891056 0.32093 0.320973
    outer loop
      vertex -1.15153 74.3069 99.145
      vertex -1.13262 72.1411 101.363
      vertex -1.13262 74.3352 99.1692
    endloop
  endfacet
  facet normal -0.890997 0.321012 0.321053
    outer loop
      vertex -1.13262 72.1411 101.363
      vertex -1.15153 74.3069 99.145
      vertex -1.28297 74.1245 98.9626
    endloop
  endfacet
  facet normal -0.707183 0.499923 0.49997
    outer loop
      vertex -1.01329 74.4262 99.2469
      vertex -1.13262 72.1411 101.363
      vertex -0.894594 74.5374 99.3036
    endloop
  endfacet
  facet normal -0.706983 0.500053 0.500122
    outer loop
      vertex -1.13262 72.1411 101.363
      vertex -1.01329 74.4262 99.2469
      vertex -1.13262 74.3352 99.1692
    endloop
  endfacet
  facet normal -0.633979 -0.267229 0.725713
    outer loop
      vertex -0.72811 71.5797 101.509
      vertex -1.33147 71.8651 101.087
      vertex -0.855945 71.4023 101.332
    endloop
  endfacet
  facet normal 0.00609603 -0.708493 0.705691
    outer loop
      vertex -0.855945 71.4023 101.332
      vertex -0.899994 71.2057 101.135
      vertex -0.72811 71.5797 101.509
    endloop
  endfacet
  facet normal -0.503856 -0.140915 0.852216
    outer loop
      vertex -0.529002 71.7205 101.65
      vertex -0.822895 72.3601 101.582
      vertex -0.72811 71.5797 101.509
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 68.014 69.7602
      vertex -3 76.014 98.4379
      vertex -3 76.014 3
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 67.8182 70.9963
      vertex -3 76.014 98.4379
      vertex -3 68.014 69.7602
    endloop
  endfacet
  facet normal -1 0 -0
    outer loop
      vertex -3 68.5894 91.3062
      vertex -3 76.014 98.4379
      vertex -3 67.8182 70.9963
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 68.2358 93.0739
      vertex -3 76.014 98.4379
      vertex -3 68.5894 91.3062
    endloop
  endfacet
  facet normal -1 0 -0
    outer loop
      vertex -3 74.3069 99.145
      vertex -3 76.014 98.4379
      vertex -3 68.2358 93.0739
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 75.965 98.7469
      vertex -3 74.3069 99.145
      vertex -3 75.823 99.0257
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 75.823 99.0257
      vertex -3 74.3069 99.145
      vertex -3 75.6018 99.2469
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 75.6018 99.2469
      vertex -3 74.3069 99.145
      vertex -3 75.323 99.3889
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 75.323 99.3889
      vertex -3 74.3069 99.145
      vertex -3 75.014 99.4379
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 68.014 69.7602
      vertex -3 76.014 3
      vertex -3 68.014 12
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 76.014 3
      vertex -3 67.8182 10.7639
      vertex -3 68.014 12
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 76.014 3
      vertex -3 67.25 9.64886
      vertex -3 67.8182 10.7639
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 76.014 3
      vertex -3 66.3651 8.76393
      vertex -3 67.25 9.64886
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 76.014 3
      vertex -3 65.25 8.19577
      vertex -3 66.3651 8.76393
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 76.014 3
      vertex -3 64.014 8
      vertex -3 65.25 8.19577
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 76.014 3
      vertex -3 12 8
      vertex -3 64.014 8
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 0 3
      vertex -3 8 19.8676
      vertex -3 8 12
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 0 3
      vertex -3 8 12
      vertex -3 8.19577 10.7639
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 8 19.8676
      vertex -3 0 30.2222
      vertex -3 5.02045 29.8586
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 5.02045 29.8586
      vertex -3 0 30.2222
      vertex -3 2.82841 32.0506
    endloop
  endfacet
  facet normal -1 0 -0
    outer loop
      vertex -3 0.292892 30.9293
      vertex -3 2.82841 32.0506
      vertex -3 0 30.2222
    endloop
  endfacet
  facet normal -1 0 -0
    outer loop
      vertex -3 1.4142 32.0506
      vertex -3 2.82841 32.0506
      vertex -3 0.292892 30.9293
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 2.82841 32.0506
      vertex -3 1.4142 32.0506
      vertex -3 2.5753 32.2345
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 2.27774 32.3312
      vertex -3 1.4142 32.0506
      vertex -3 1.96487 32.3312
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 1.96487 32.3312
      vertex -3 1.4142 32.0506
      vertex -3 1.66731 32.2345
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 2.5753 32.2345
      vertex -3 1.4142 32.0506
      vertex -3 2.27774 32.3312
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 0 3
      vertex -3 12 8
      vertex -3 76.014 3
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 0 3
      vertex -3 10.7639 8.19577
      vertex -3 12 8
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 0 3
      vertex -3 9.64886 8.76393
      vertex -3 10.7639 8.19577
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 0 3
      vertex -3 8.76393 9.64886
      vertex -3 9.64886 8.76393
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 0 3
      vertex -3 8.19577 10.7639
      vertex -3 8.76393 9.64886
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 8 19.8676
      vertex -3 0 3
      vertex -3 0 30.2222
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 0.292892 30.9293
      vertex -3 0 30.2222
      vertex -3 0.108994 30.6761
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 68.2358 93.0739
      vertex -3 68.5894 91.3062
      vertex -3 68.2358 91.6597
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 76.014 98.4379
      vertex -3 74.3069 99.145
      vertex -3 75.965 98.7469
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 68.0519 91.9128
      vertex -3 68.2358 93.0739
      vertex -3 68.2358 91.6597
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 68.0519 91.9128
      vertex -3 68.0519 92.8208
      vertex -3 68.2358 93.0739
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 67.9552 92.2104
      vertex -3 68.0519 92.8208
      vertex -3 68.0519 91.9128
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 68.0519 92.8208
      vertex -3 67.9552 92.2104
      vertex -3 67.9552 92.5232
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 75.014 99.4379
      vertex -3 74.3069 99.145
      vertex -3 74.705 99.3889
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 74.705 99.3889
      vertex -3 74.3069 99.145
      vertex -3 74.4262 99.2469
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 67.25 72.1113
      vertex -3 68.5894 91.3062
      vertex -3 67.8182 70.9963
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 66.3651 72.9963
      vertex -3 68.5894 91.3062
      vertex -3 67.25 72.1113
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 65.25 73.5644
      vertex -3 68.5894 91.3062
      vertex -3 66.3651 72.9963
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 64.014 73.7602
      vertex -3 68.5894 91.3062
      vertex -3 65.25 73.5644
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 62.7779 73.5644
      vertex -3 68.5894 91.3062
      vertex -3 64.014 73.7602
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 61.6628 72.9963
      vertex -3 68.5894 91.3062
      vertex -3 62.7779 73.5644
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 61.1855 72.5886
      vertex -3 68.5894 91.3062
      vertex -3 61.6628 72.9963
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 61.1855 72.5886
      vertex -3 14.7078 37.4246
      vertex -3 68.5894 91.3062
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 12.94 37.7782
      vertex -3 14.3543 37.7782
      vertex -3 14.7078 37.4246
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 14.0623 25.4654
      vertex -3 14.7078 37.4246
      vertex -3 61.1855 72.5886
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 13.0214 25.4654
      vertex -3 14.7078 37.4246
      vertex -3 14.0623 25.4654
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 14.3543 37.7782
      vertex -3 12.94 37.7782
      vertex -3 14.1012 37.9621
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 14.1012 37.9621
      vertex -3 12.94 37.7782
      vertex -3 13.8036 38.0587
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 13.8036 38.0587
      vertex -3 12.94 37.7782
      vertex -3 13.4907 38.0587
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3 14.7078 37.4246
      vertex -3 13.0214 25.4654
      vertex -3 12.94 37.7782
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 13.4907 38.0587
      vertex -3 12.94 37.7782
      vertex -3 13.1932 37.9621
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 5.02045 29.8586
      vertex -3 13.0214 25.4654
      vertex -3 11.8312 25.0787
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 5.02045 29.8586
      vertex -3 11.8312 25.0787
      vertex -3 10.8187 24.3431
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 5.02045 29.8586
      vertex -3 10.8187 24.3431
      vertex -3 9.17157 22.696
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 5.02045 29.8586
      vertex -3 9.17157 22.696
      vertex -3 8.43597 21.6835
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 5.02045 29.8586
      vertex -3 8.43597 21.6835
      vertex -3 8.04924 20.4933
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 13.0214 25.4654
      vertex -3 5.02045 29.8586
      vertex -3 12.94 37.7782
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3 5.02045 29.8586
      vertex -3 8.04924 20.4933
      vertex -3 8 19.8676
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 76.014 98.4379
      vertex 3 67.8182 70.9963
      vertex 3 68.014 69.7602
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.5894 91.3062
      vertex 3 67.25 72.1113
      vertex 3 67.8182 70.9963
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.5894 91.3062
      vertex 3 66.3651 72.9963
      vertex 3 67.25 72.1113
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.5894 91.3062
      vertex 3 65.25 73.5644
      vertex 3 66.3651 72.9963
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.5894 91.3062
      vertex 3 64.014 73.7602
      vertex 3 65.25 73.5644
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.5894 91.3062
      vertex 3 62.7779 73.5644
      vertex 3 64.014 73.7602
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.5894 91.3062
      vertex 3 61.6628 72.9963
      vertex 3 62.7779 73.5644
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.5894 91.3062
      vertex 3 61.1855 72.5886
      vertex 3 61.6628 72.9963
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 14.7078 37.4246
      vertex 3 61.1855 72.5886
      vertex 3 68.5894 91.3062
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 12.94 37.7782
      vertex 3 14.3543 37.7782
      vertex 3 14.1012 37.9621
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 14.7078 37.4246
      vertex 3 14.0623 25.4654
      vertex 3 61.1855 72.5886
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 14.3543 37.7782
      vertex 3 12.94 37.7782
      vertex 3 14.7078 37.4246
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 12.94 37.7782
      vertex 3 14.1012 37.9621
      vertex 3 13.8036 38.0587
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 12.94 37.7782
      vertex 3 13.8036 38.0587
      vertex 3 13.4907 38.0587
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 12.94 37.7782
      vertex 3 13.4907 38.0587
      vertex 3 13.1932 37.9621
    endloop
  endfacet
  facet normal 1 0 -0
    outer loop
      vertex 3 13.0214 25.4654
      vertex 3 14.7078 37.4246
      vertex 3 12.94 37.7782
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 14.7078 37.4246
      vertex 3 13.0214 25.4654
      vertex 3 14.0623 25.4654
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 5.02045 29.8586
      vertex 3 13.0214 25.4654
      vertex 3 12.94 37.7782
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 13.0214 25.4654
      vertex 3 5.02045 29.8586
      vertex 3 11.8312 25.0787
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 11.8312 25.0787
      vertex 3 5.02045 29.8586
      vertex 3 10.8187 24.3431
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 10.8187 24.3431
      vertex 3 5.02045 29.8586
      vertex 3 9.17157 22.696
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 9.17157 22.696
      vertex 3 5.02045 29.8586
      vertex 3 8.43597 21.6835
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 8.04924 20.4933
      vertex 3 0 30.2222
      vertex 3 8 19.8676
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 8.43597 21.6835
      vertex 3 0 30.2222
      vertex 3 8.04924 20.4933
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 0 30.2222
      vertex 3 8.43597 21.6835
      vertex 3 5.02045 29.8586
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 76.014 98.4379
      vertex 3 68.2358 93.0739
      vertex 3 68.5894 91.3062
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.2358 93.0739
      vertex 3 68.2358 91.6597
      vertex 3 68.5894 91.3062
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 68.0519 92.8208
      vertex 3 68.2358 91.6597
      vertex 3 68.2358 93.0739
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.0519 92.8208
      vertex 3 68.0519 91.9128
      vertex 3 68.2358 91.6597
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 67.9552 92.5232
      vertex 3 68.0519 91.9128
      vertex 3 68.0519 92.8208
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.0519 91.9128
      vertex 3 67.9552 92.5232
      vertex 3 67.9552 92.2104
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 74.3069 99.145
      vertex 3 76.014 98.4379
      vertex 3 75.965 98.7469
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 74.3069 99.145
      vertex 3 75.965 98.7469
      vertex 3 75.823 99.0257
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 74.3069 99.145
      vertex 3 75.823 99.0257
      vertex 3 75.6018 99.2469
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 74.3069 99.145
      vertex 3 75.6018 99.2469
      vertex 3 75.323 99.3889
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 74.3069 99.145
      vertex 3 75.323 99.3889
      vertex 3 75.014 99.4379
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 74.3069 99.145
      vertex 3 75.014 99.4379
      vertex 3 74.705 99.3889
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 74.3069 99.145
      vertex 3 74.705 99.3889
      vertex 3 74.4262 99.2469
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 68.2358 93.0739
      vertex 3 76.014 98.4379
      vertex 3 74.3069 99.145
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 67.8182 70.9963
      vertex 3 76.014 98.4379
      vertex 3 68.5894 91.3062
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 76.014 98.4379
      vertex 3 68.014 69.7602
      vertex 3 76.014 3
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 68.014 12
      vertex 3 76.014 3
      vertex 3 68.014 69.7602
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 67.8182 10.7639
      vertex 3 76.014 3
      vertex 3 68.014 12
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 67.25 9.64886
      vertex 3 76.014 3
      vertex 3 67.8182 10.7639
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 66.3651 8.76393
      vertex 3 76.014 3
      vertex 3 67.25 9.64886
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 65.25 8.19577
      vertex 3 76.014 3
      vertex 3 66.3651 8.76393
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 64.014 8
      vertex 3 76.014 3
      vertex 3 65.25 8.19577
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 12 8
      vertex 3 76.014 3
      vertex 3 64.014 8
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 0 3
      vertex 3 8 19.8676
      vertex 3 0 30.2222
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3 0 30.2222
      vertex 3 5.02045 29.8586
      vertex 3 2.82841 32.0506
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 1.4142 32.0506
      vertex 3 2.82841 32.0506
      vertex 3 2.5753 32.2345
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 1.4142 32.0506
      vertex 3 2.5753 32.2345
      vertex 3 2.27774 32.3312
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 1.4142 32.0506
      vertex 3 2.27774 32.3312
      vertex 3 1.96487 32.3312
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 1.4142 32.0506
      vertex 3 1.96487 32.3312
      vertex 3 1.66731 32.2345
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 2.82841 32.0506
      vertex 3 1.4142 32.0506
      vertex 3 0.292892 30.9293
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 2.82841 32.0506
      vertex 3 0.292892 30.9293
      vertex 3 0 30.2222
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 0 30.2222
      vertex 3 0.292892 30.9293
      vertex 3 0.108994 30.6761
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 8 19.8676
      vertex 3 0 3
      vertex 3 8 12
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 12 8
      vertex 3 0 3
      vertex 3 76.014 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 10.7639 8.19577
      vertex 3 0 3
      vertex 3 12 8
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 9.64886 8.76393
      vertex 3 0 3
      vertex 3 10.7639 8.19577
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 8.76393 9.64886
      vertex 3 0 3
      vertex 3 9.64886 8.76393
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 8.19577 10.7639
      vertex 3 0 3
      vertex 3 8.76393 9.64886
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3 8 12
      vertex 3 0 3
      vertex 3 8.19577 10.7639
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 3 76.014 3
      vertex -3 76.014 98.4379
      vertex 3 76.014 98.4379
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -3 76.014 98.4379
      vertex 3 76.014 3
      vertex -3 76.014 3
    endloop
  endfacet
  facet normal 0 0.987659 0.156619
    outer loop
      vertex 3 76.014 98.4379
      vertex -3 75.965 98.7469
      vertex 3 75.965 98.7469
    endloop
  endfacet
  facet normal 0 0.987659 0.156619
    outer loop
      vertex -3 75.965 98.7469
      vertex 3 76.014 98.4379
      vertex -3 76.014 98.4379
    endloop
  endfacet
  facet normal 0 0.891079 0.453849
    outer loop
      vertex 3 75.965 98.7469
      vertex -3 75.823 99.0257
      vertex 3 75.823 99.0257
    endloop
  endfacet
  facet normal 0 0.891079 0.453849
    outer loop
      vertex -3 75.823 99.0257
      vertex 3 75.965 98.7469
      vertex -3 75.965 98.7469
    endloop
  endfacet
  facet normal 0 0.707107 0.707107
    outer loop
      vertex 3 75.823 99.0257
      vertex -3 75.6018 99.2469
      vertex 3 75.6018 99.2469
    endloop
  endfacet
  facet normal 0 0.707107 0.707107
    outer loop
      vertex -3 75.6018 99.2469
      vertex 3 75.823 99.0257
      vertex -3 75.823 99.0257
    endloop
  endfacet
  facet normal -0 0.453849 0.891079
    outer loop
      vertex -3 75.6018 99.2469
      vertex 3 75.323 99.3889
      vertex 3 75.6018 99.2469
    endloop
  endfacet
  facet normal 0 0.453849 0.891079
    outer loop
      vertex 3 75.323 99.3889
      vertex -3 75.6018 99.2469
      vertex -3 75.323 99.3889
    endloop
  endfacet
  facet normal -0 0.156619 0.987659
    outer loop
      vertex -3 75.323 99.3889
      vertex 3 75.014 99.4379
      vertex 3 75.323 99.3889
    endloop
  endfacet
  facet normal 0 0.156619 0.987659
    outer loop
      vertex 3 75.014 99.4379
      vertex -3 75.323 99.3889
      vertex -3 75.014 99.4379
    endloop
  endfacet
  facet normal 0 -0.156619 0.987659
    outer loop
      vertex 3 75.014 99.4379
      vertex 0.612608 74.705 99.3889
      vertex 3 74.705 99.3889
    endloop
  endfacet
  facet normal 0.000136819 -0.15765 0.987495
    outer loop
      vertex 3 75.014 99.4379
      vertex 0.513959 74.7663 99.3987
      vertex 0.612608 74.705 99.3889
    endloop
  endfacet
  facet normal -1.29945e-05 -0.156183 0.987728
    outer loop
      vertex 3 75.014 99.4379
      vertex 0.432621 74.8169 99.4067
      vertex 0.513959 74.7663 99.3987
    endloop
  endfacet
  facet normal -9.05648e-05 -0.155198 0.987883
    outer loop
      vertex 3 75.014 99.4379
      vertex 0.346678 74.8335 99.4093
      vertex 0.432621 74.8169 99.4067
    endloop
  endfacet
  facet normal -2.36452e-05 -0.156157 0.987732
    outer loop
      vertex 3 75.014 99.4379
      vertex 0 74.9006 99.4199
      vertex 0.346678 74.8335 99.4093
    endloop
  endfacet
  facet normal 2.36452e-05 -0.156157 0.987732
    outer loop
      vertex -3 75.014 99.4379
      vertex -0.346678 74.8335 99.4093
      vertex 0 74.9006 99.4199
    endloop
  endfacet
  facet normal 1.29945e-05 -0.156183 0.987728
    outer loop
      vertex -3 75.014 99.4379
      vertex -0.513959 74.7663 99.3987
      vertex -0.432621 74.8169 99.4067
    endloop
  endfacet
  facet normal 0 -0.156768 0.987636
    outer loop
      vertex -3 75.014 99.4379
      vertex 0 74.9006 99.4199
      vertex 3 75.014 99.4379
    endloop
  endfacet
  facet normal 9.05648e-05 -0.155198 0.987883
    outer loop
      vertex -0.346678 74.8335 99.4093
      vertex -3 75.014 99.4379
      vertex -0.432621 74.8169 99.4067
    endloop
  endfacet
  facet normal -0.000136819 -0.15765 0.987495
    outer loop
      vertex -0.513959 74.7663 99.3987
      vertex -3 75.014 99.4379
      vertex -0.612608 74.705 99.3889
    endloop
  endfacet
  facet normal 0 -0.156619 0.987659
    outer loop
      vertex -0.612608 74.705 99.3889
      vertex -3 75.014 99.4379
      vertex -3 74.705 99.3889
    endloop
  endfacet
  facet normal 1.39344e-06 -0.453569 0.891221
    outer loop
      vertex -3 74.705 99.3889
      vertex -0.894594 74.5374 99.3036
      vertex -0.822895 74.6046 99.3378
    endloop
  endfacet
  facet normal 0 -0.453593 0.891209
    outer loop
      vertex -3 74.705 99.3889
      vertex -0.822895 74.6046 99.3378
      vertex -0.612608 74.705 99.3889
    endloop
  endfacet
  facet normal -6.15879e-05 -0.454198 0.890901
    outer loop
      vertex -0.894594 74.5374 99.3036
      vertex -3 74.705 99.3889
      vertex -1.01329 74.4262 99.2469
    endloop
  endfacet
  facet normal 0 -0.453849 0.891079
    outer loop
      vertex -1.01329 74.4262 99.2469
      vertex -3 74.705 99.3889
      vertex -3 74.4262 99.2469
    endloop
  endfacet
  facet normal 0 -0.453849 0.891079
    outer loop
      vertex 3 74.705 99.3889
      vertex 1.01329 74.4262 99.2469
      vertex 3 74.4262 99.2469
    endloop
  endfacet
  facet normal 6.15879e-05 -0.454198 0.890901
    outer loop
      vertex 3 74.705 99.3889
      vertex 0.894594 74.5374 99.3036
      vertex 1.01329 74.4262 99.2469
    endloop
  endfacet
  facet normal -1.39344e-06 -0.453569 0.891221
    outer loop
      vertex 3 74.705 99.3889
      vertex 0.822895 74.6046 99.3378
      vertex 0.894594 74.5374 99.3036
    endloop
  endfacet
  facet normal 0 -0.453593 0.891209
    outer loop
      vertex 0.822895 74.6046 99.3378
      vertex 3 74.705 99.3889
      vertex 0.612608 74.705 99.3889
    endloop
  endfacet
  facet normal 0 -0.649345 0.760494
    outer loop
      vertex -3 74.4262 99.2469
      vertex -1.13262 74.3352 99.1692
      vertex -1.01329 74.4262 99.2469
    endloop
  endfacet
  facet normal -4.58238e-05 -0.649889 0.760029
    outer loop
      vertex -3 74.4262 99.2469
      vertex -1.15153 74.3069 99.145
      vertex -1.13262 74.3352 99.1692
    endloop
  endfacet
  facet normal 0 -0.649478 0.76038
    outer loop
      vertex -1.15153 74.3069 99.145
      vertex -3 74.4262 99.2469
      vertex -3 74.3069 99.145
    endloop
  endfacet
  facet normal 0 -0.649478 0.76038
    outer loop
      vertex 3 74.4262 99.2469
      vertex 1.15153 74.3069 99.145
      vertex 3 74.3069 99.145
    endloop
  endfacet
  facet normal 4.58238e-05 -0.649889 0.760029
    outer loop
      vertex 3 74.4262 99.2469
      vertex 1.13262 74.3352 99.1692
      vertex 1.15153 74.3069 99.145
    endloop
  endfacet
  facet normal 0 -0.649345 0.760494
    outer loop
      vertex 1.13262 74.3352 99.1692
      vertex 3 74.4262 99.2469
      vertex 1.01329 74.4262 99.2469
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex -3 74.3069 99.145
      vertex -1.28297 74.1245 98.9626
      vertex -1.15153 74.3069 99.145
    endloop
  endfacet
  facet normal 0.000103605 -0.706619 0.707594
    outer loop
      vertex -3 74.3069 99.145
      vertex -1.33147 74.0571 98.8953
      vertex -1.28297 74.1245 98.9626
    endloop
  endfacet
  facet normal -4.10042e-05 -0.707102 0.707111
    outer loop
      vertex -3 74.3069 99.145
      vertex -1.39999 73.7512 98.5894
      vertex -1.33147 74.0571 98.8953
    endloop
  endfacet
  facet normal -0.000134953 -0.707237 0.706976
    outer loop
      vertex -3 74.3069 99.145
      vertex -1.33147 73.4453 98.2834
      vertex -1.39999 73.7512 98.5894
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex -3 74.3069 99.145
      vertex -1.13262 73.1694 98.0075
      vertex -1.33147 73.4453 98.2834
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex -3 68.2358 93.0739
      vertex -1.13262 73.1694 98.0075
      vertex -3 74.3069 99.145
    endloop
  endfacet
  facet normal -0.000738331 -0.706967 0.707246
    outer loop
      vertex -1.13262 73.1694 98.0075
      vertex -3 68.2358 93.0739
      vertex -1.05708 73.1159 97.9541
    endloop
  endfacet
  facet normal 0.000152151 -0.707157 0.707056
    outer loop
      vertex -0.432621 72.8097 97.6479
      vertex -3 68.2358 93.0739
      vertex 0 72.7613 97.5994
    endloop
  endfacet
  facet normal -4.63344e-06 -0.707113 0.7071
    outer loop
      vertex -0.52781 72.844 97.6822
      vertex -3 68.2358 93.0739
      vertex -0.432621 72.8097 97.6479
    endloop
  endfacet
  facet normal -0.000205438 -0.707059 0.707154
    outer loop
      vertex -0.822895 72.9504 97.7885
      vertex -3 68.2358 93.0739
      vertex -0.52781 72.844 97.6822
    endloop
  endfacet
  facet normal 0.000227634 -0.707159 0.707054
    outer loop
      vertex -1.05708 73.1159 97.9541
      vertex -3 68.2358 93.0739
      vertex -0.822895 72.9504 97.7885
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex 1.28297 74.1245 98.9626
      vertex 3 74.3069 99.145
      vertex 1.15153 74.3069 99.145
    endloop
  endfacet
  facet normal -0.000103605 -0.706619 0.707594
    outer loop
      vertex 1.33147 74.0571 98.8953
      vertex 3 74.3069 99.145
      vertex 1.28297 74.1245 98.9626
    endloop
  endfacet
  facet normal 4.10042e-05 -0.707102 0.707111
    outer loop
      vertex 1.39999 73.7512 98.5894
      vertex 3 74.3069 99.145
      vertex 1.33147 74.0571 98.8953
    endloop
  endfacet
  facet normal 0.000134953 -0.707237 0.706976
    outer loop
      vertex 1.33147 73.4453 98.2834
      vertex 3 74.3069 99.145
      vertex 1.39999 73.7512 98.5894
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex 1.13262 73.1694 98.0075
      vertex 3 74.3069 99.145
      vertex 1.33147 73.4453 98.2834
    endloop
  endfacet
  facet normal 0.000738331 -0.706967 0.707246
    outer loop
      vertex 3 68.2358 93.0739
      vertex 1.13262 73.1694 98.0075
      vertex 1.05708 73.1159 97.9541
    endloop
  endfacet
  facet normal -0.000227634 -0.707159 0.707054
    outer loop
      vertex 3 68.2358 93.0739
      vertex 1.05708 73.1159 97.9541
      vertex 0.822895 72.9504 97.7885
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex 3 68.2358 93.0739
      vertex 0 72.7613 97.5994
      vertex -3 68.2358 93.0739
    endloop
  endfacet
  facet normal -0.000152151 -0.707157 0.707056
    outer loop
      vertex 0 72.7613 97.5994
      vertex 3 68.2358 93.0739
      vertex 0.432621 72.8097 97.6479
    endloop
  endfacet
  facet normal 4.63344e-06 -0.707113 0.7071
    outer loop
      vertex 0.432621 72.8097 97.6479
      vertex 3 68.2358 93.0739
      vertex 0.52781 72.844 97.6822
    endloop
  endfacet
  facet normal 0.000205438 -0.707059 0.707154
    outer loop
      vertex 0.52781 72.844 97.6822
      vertex 3 68.2358 93.0739
      vertex 0.822895 72.9504 97.7885
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex 1.13262 73.1694 98.0075
      vertex 3 68.2358 93.0739
      vertex 3 74.3069 99.145
    endloop
  endfacet
  facet normal 0 -0.808999 0.587811
    outer loop
      vertex -3 68.0519 92.8208
      vertex 3 68.2358 93.0739
      vertex -3 68.2358 93.0739
    endloop
  endfacet
  facet normal 0 -0.808999 0.587811
    outer loop
      vertex 3 68.2358 93.0739
      vertex -3 68.0519 92.8208
      vertex 3 68.0519 92.8208
    endloop
  endfacet
  facet normal 0 -0.951053 0.309028
    outer loop
      vertex -3 67.9552 92.5232
      vertex 3 68.0519 92.8208
      vertex -3 68.0519 92.8208
    endloop
  endfacet
  facet normal 0 -0.951053 0.309028
    outer loop
      vertex 3 68.0519 92.8208
      vertex -3 67.9552 92.5232
      vertex 3 67.9552 92.5232
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -3 67.9552 92.2104
      vertex 3 67.9552 92.5232
      vertex -3 67.9552 92.5232
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex 3 67.9552 92.5232
      vertex -3 67.9552 92.2104
      vertex 3 67.9552 92.2104
    endloop
  endfacet
  facet normal 0 -0.951053 -0.309028
    outer loop
      vertex -3 68.0519 91.9128
      vertex 3 67.9552 92.2104
      vertex -3 67.9552 92.2104
    endloop
  endfacet
  facet normal 0 -0.951053 -0.309028
    outer loop
      vertex 3 67.9552 92.2104
      vertex -3 68.0519 91.9128
      vertex 3 68.0519 91.9128
    endloop
  endfacet
  facet normal 0 -0.808999 -0.587811
    outer loop
      vertex -3 68.2358 91.6597
      vertex 3 68.0519 91.9128
      vertex -3 68.0519 91.9128
    endloop
  endfacet
  facet normal 0 -0.808999 -0.587811
    outer loop
      vertex 3 68.0519 91.9128
      vertex -3 68.2358 91.6597
      vertex 3 68.2358 91.6597
    endloop
  endfacet
  facet normal 0 -0.707007 -0.707207
    outer loop
      vertex -3 68.2358 91.6597
      vertex 3 68.5894 91.3062
      vertex 3 68.2358 91.6597
    endloop
  endfacet
  facet normal -0 -0.707007 -0.707207
    outer loop
      vertex 3 68.5894 91.3062
      vertex -3 68.2358 91.6597
      vertex -3 68.5894 91.3062
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex -3 14.7078 37.4246
      vertex 3 68.5894 91.3062
      vertex -3 68.5894 91.3062
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex 3 68.5894 91.3062
      vertex -3 14.7078 37.4246
      vertex 3 14.7078 37.4246
    endloop
  endfacet
  facet normal 0 0.707207 0.707007
    outer loop
      vertex 3 14.7078 37.4246
      vertex -3 14.3543 37.7782
      vertex 3 14.3543 37.7782
    endloop
  endfacet
  facet normal 0 0.707207 0.707007
    outer loop
      vertex -3 14.3543 37.7782
      vertex 3 14.7078 37.4246
      vertex -3 14.7078 37.4246
    endloop
  endfacet
  facet normal -0 0.587811 0.808999
    outer loop
      vertex -3 14.3543 37.7782
      vertex 3 14.1012 37.9621
      vertex 3 14.3543 37.7782
    endloop
  endfacet
  facet normal 0 0.587811 0.808999
    outer loop
      vertex 3 14.1012 37.9621
      vertex -3 14.3543 37.7782
      vertex -3 14.1012 37.9621
    endloop
  endfacet
  facet normal -0 0.308739 0.951147
    outer loop
      vertex -3 14.1012 37.9621
      vertex 3 13.8036 38.0587
      vertex 3 14.1012 37.9621
    endloop
  endfacet
  facet normal 0 0.308739 0.951147
    outer loop
      vertex 3 13.8036 38.0587
      vertex -3 14.1012 37.9621
      vertex -3 13.8036 38.0587
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3 13.8036 38.0587
      vertex 3 13.4907 38.0587
      vertex 3 13.8036 38.0587
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 13.4907 38.0587
      vertex -3 13.8036 38.0587
      vertex -3 13.4907 38.0587
    endloop
  endfacet
  facet normal 0 -0.308833 0.951116
    outer loop
      vertex -3 13.4907 38.0587
      vertex 3 13.1932 37.9621
      vertex 3 13.4907 38.0587
    endloop
  endfacet
  facet normal 0 -0.308833 0.951116
    outer loop
      vertex 3 13.1932 37.9621
      vertex -3 13.4907 38.0587
      vertex -3 13.1932 37.9621
    endloop
  endfacet
  facet normal 0 -0.587659 0.809109
    outer loop
      vertex -3 13.1932 37.9621
      vertex 3 12.94 37.7782
      vertex 3 13.1932 37.9621
    endloop
  endfacet
  facet normal 0 -0.587659 0.809109
    outer loop
      vertex 3 12.94 37.7782
      vertex -3 13.1932 37.9621
      vertex -3 12.94 37.7782
    endloop
  endfacet
  facet normal 0 -0.70711 0.707103
    outer loop
      vertex -3 12.94 37.7782
      vertex 0 8.02565 32.8638
      vertex 3 12.94 37.7782
    endloop
  endfacet
  facet normal -0.000142028 -0.707154 0.70706
    outer loop
      vertex -3 12.94 37.7782
      vertex -0.324464 7.98932 32.8274
      vertex 0 8.02565 32.8638
    endloop
  endfacet
  facet normal 0.000126497 -0.707081 0.707132
    outer loop
      vertex -3 12.94 37.7782
      vertex -0.617167 7.88386 32.722
      vertex -0.324464 7.98932 32.8274
    endloop
  endfacet
  facet normal -8.68737e-05 -0.707131 0.707082
    outer loop
      vertex -3 12.94 37.7782
      vertex -0.849458 7.7196 32.5577
      vertex -0.617167 7.88386 32.722
    endloop
  endfacet
  facet normal -7.85374e-05 -0.70713 0.707084
    outer loop
      vertex -3 12.94 37.7782
      vertex -0.998597 7.51263 32.3507
      vertex -0.849458 7.7196 32.5577
    endloop
  endfacet
  facet normal 3.38234e-05 -0.707109 0.707105
    outer loop
      vertex -3 5.02045 29.8586
      vertex -0.998597 7.51263 32.3507
      vertex -3 12.94 37.7782
    endloop
  endfacet
  facet normal -0.000120483 -0.707047 0.707167
    outer loop
      vertex -0.998597 7.51263 32.3507
      vertex -3 5.02045 29.8586
      vertex -1.04999 7.2832 32.1213
    endloop
  endfacet
  facet normal 7.37871e-05 -0.707163 0.70705
    outer loop
      vertex -3 5.02045 29.8586
      vertex -0.0791376 6.54961 31.3877
      vertex -0.324464 6.57708 31.4152
    endloop
  endfacet
  facet normal -0.00043937 -0.706673 0.70754
    outer loop
      vertex -0.0791376 6.54961 31.3877
      vertex -3 5.02045 29.8586
      vertex 0 6.54075 31.3789
    endloop
  endfacet
  facet normal 6.27036e-05 -0.707154 0.70706
    outer loop
      vertex -0.617167 6.68254 31.5207
      vertex -3 5.02045 29.8586
      vertex -0.324464 6.57708 31.4152
    endloop
  endfacet
  facet normal -9.21996e-05 -0.707043 0.707171
    outer loop
      vertex -0.849458 6.8468 31.6849
      vertex -3 5.02045 29.8586
      vertex -0.617167 6.68254 31.5207
    endloop
  endfacet
  facet normal 6.41949e-05 -0.707135 0.707079
    outer loop
      vertex -0.998597 7.05377 31.8919
      vertex -3 5.02045 29.8586
      vertex -0.849458 6.8468 31.6849
    endloop
  endfacet
  facet normal -7.07684e-05 -0.707068 0.707145
    outer loop
      vertex -1.04999 7.2832 32.1213
      vertex -3 5.02045 29.8586
      vertex -0.998597 7.05377 31.8919
    endloop
  endfacet
  facet normal 0.000142028 -0.707154 0.70706
    outer loop
      vertex 0.324464 7.98932 32.8274
      vertex 3 12.94 37.7782
      vertex 0 8.02565 32.8638
    endloop
  endfacet
  facet normal -0.000126497 -0.707081 0.707132
    outer loop
      vertex 0.617167 7.88386 32.722
      vertex 3 12.94 37.7782
      vertex 0.324464 7.98932 32.8274
    endloop
  endfacet
  facet normal 8.68737e-05 -0.707131 0.707082
    outer loop
      vertex 0.849458 7.7196 32.5577
      vertex 3 12.94 37.7782
      vertex 0.617167 7.88386 32.722
    endloop
  endfacet
  facet normal 7.85374e-05 -0.70713 0.707084
    outer loop
      vertex 0.998597 7.51263 32.3507
      vertex 3 12.94 37.7782
      vertex 0.849458 7.7196 32.5577
    endloop
  endfacet
  facet normal 0.000120483 -0.707047 0.707167
    outer loop
      vertex 3 5.02045 29.8586
      vertex 0.998597 7.51263 32.3507
      vertex 1.04999 7.2832 32.1213
    endloop
  endfacet
  facet normal 7.07684e-05 -0.707068 0.707145
    outer loop
      vertex 3 5.02045 29.8586
      vertex 1.04999 7.2832 32.1213
      vertex 0.998597 7.05377 31.8919
    endloop
  endfacet
  facet normal 0.00043937 -0.706673 0.70754
    outer loop
      vertex 3 5.02045 29.8586
      vertex 0.0791376 6.54961 31.3877
      vertex 0 6.54075 31.3789
    endloop
  endfacet
  facet normal 0 -0.707107 0.707107
    outer loop
      vertex 3 5.02045 29.8586
      vertex 0 6.54075 31.3789
      vertex -3 5.02045 29.8586
    endloop
  endfacet
  facet normal -7.37871e-05 -0.707163 0.70705
    outer loop
      vertex 0.0791376 6.54961 31.3877
      vertex 3 5.02045 29.8586
      vertex 0.324464 6.57708 31.4152
    endloop
  endfacet
  facet normal -3.38234e-05 -0.707109 0.707105
    outer loop
      vertex 0.998597 7.51263 32.3507
      vertex 3 5.02045 29.8586
      vertex 3 12.94 37.7782
    endloop
  endfacet
  facet normal -6.41949e-05 -0.707135 0.707079
    outer loop
      vertex 0.849458 6.8468 31.6849
      vertex 3 5.02045 29.8586
      vertex 0.998597 7.05377 31.8919
    endloop
  endfacet
  facet normal 9.21996e-05 -0.707043 0.707171
    outer loop
      vertex 0.617167 6.68254 31.5207
      vertex 3 5.02045 29.8586
      vertex 0.849458 6.8468 31.6849
    endloop
  endfacet
  facet normal -6.27036e-05 -0.707154 0.70706
    outer loop
      vertex 0.324464 6.57708 31.4152
      vertex 3 5.02045 29.8586
      vertex 0.617167 6.68254 31.5207
    endloop
  endfacet
  facet normal 0 0.7071 0.707113
    outer loop
      vertex 3 5.02045 29.8586
      vertex -3 2.82841 32.0506
      vertex 3 2.82841 32.0506
    endloop
  endfacet
  facet normal 0 0.7071 0.707113
    outer loop
      vertex -3 2.82841 32.0506
      vertex 3 5.02045 29.8586
      vertex -3 5.02045 29.8586
    endloop
  endfacet
  facet normal -0 0.587795 0.80901
    outer loop
      vertex -3 2.82841 32.0506
      vertex 3 2.5753 32.2345
      vertex 3 2.82841 32.0506
    endloop
  endfacet
  facet normal 0 0.587795 0.80901
    outer loop
      vertex 3 2.5753 32.2345
      vertex -3 2.82841 32.0506
      vertex -3 2.5753 32.2345
    endloop
  endfacet
  facet normal -0 0.309066 0.951041
    outer loop
      vertex -3 2.5753 32.2345
      vertex 3 2.27774 32.3312
      vertex 3 2.5753 32.2345
    endloop
  endfacet
  facet normal 0 0.309066 0.951041
    outer loop
      vertex 3 2.27774 32.3312
      vertex -3 2.5753 32.2345
      vertex -3 2.27774 32.3312
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3 2.27774 32.3312
      vertex 3 1.96487 32.3312
      vertex 3 2.27774 32.3312
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 1.96487 32.3312
      vertex -3 2.27774 32.3312
      vertex -3 1.96487 32.3312
    endloop
  endfacet
  facet normal 0 -0.309066 0.951041
    outer loop
      vertex -3 1.96487 32.3312
      vertex 3 1.66731 32.2345
      vertex 3 1.96487 32.3312
    endloop
  endfacet
  facet normal 0 -0.309066 0.951041
    outer loop
      vertex 3 1.66731 32.2345
      vertex -3 1.96487 32.3312
      vertex -3 1.66731 32.2345
    endloop
  endfacet
  facet normal 0 -0.587795 0.80901
    outer loop
      vertex -3 1.66731 32.2345
      vertex 3 1.4142 32.0506
      vertex 3 1.66731 32.2345
    endloop
  endfacet
  facet normal 0 -0.587795 0.80901
    outer loop
      vertex 3 1.4142 32.0506
      vertex -3 1.66731 32.2345
      vertex -3 1.4142 32.0506
    endloop
  endfacet
  facet normal 0 -0.707104 0.707109
    outer loop
      vertex -3 0.292892 30.9293
      vertex 3 1.4142 32.0506
      vertex -3 1.4142 32.0506
    endloop
  endfacet
  facet normal 0 -0.707104 0.707109
    outer loop
      vertex 3 1.4142 32.0506
      vertex -3 0.292892 30.9293
      vertex 3 0.292892 30.9293
    endloop
  endfacet
  facet normal 0 -0.809112 0.587654
    outer loop
      vertex -3 0.108994 30.6761
      vertex 3 0.292892 30.9293
      vertex -3 0.292892 30.9293
    endloop
  endfacet
  facet normal 0 -0.809112 0.587654
    outer loop
      vertex 3 0.292892 30.9293
      vertex -3 0.108994 30.6761
      vertex 3 0.108994 30.6761
    endloop
  endfacet
  facet normal 0 -0.972359 0.23349
    outer loop
      vertex -3 0 30.2222
      vertex 3 0.108994 30.6761
      vertex -3 0.108994 30.6761
    endloop
  endfacet
  facet normal 0 -0.972359 0.23349
    outer loop
      vertex 3 0.108994 30.6761
      vertex -3 0 30.2222
      vertex 3 0 30.2222
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -3 0 3
      vertex 3 0 30.2222
      vertex -3 0 30.2222
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex 3 0 30.2222
      vertex -3 0 3
      vertex 3 0 3
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 7 -0.999998 0
      vertex 9 1 0
      vertex 8.90211 0.381974 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 9 1 0
      vertex -9 1 0
      vertex 9 75.014 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 7 -0.999998 0
      vertex 8.90211 0.381974 0
      vertex 8.61803 -0.175566 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -9 75.014 0
      vertex 9 75.014 0
      vertex -9 1 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 7 -0.999998 0
      vertex 8.61803 -0.175566 0
      vertex 8.17557 -0.618025 0
    endloop
  endfacet
  facet normal 0 -0 -1
    outer loop
      vertex 7 77.014 0
      vertex 9 75.014 0
      vertex -9 75.014 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 7 -0.999998 0
      vertex 8.17557 -0.618025 0
      vertex 7.61803 -0.902113 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 9 75.014 0
      vertex 7 77.014 0
      vertex 8.90211 75.632 0
    endloop
  endfacet
  facet normal -0 0 -1
    outer loop
      vertex 9 1 0
      vertex 7 -0.999998 0
      vertex -9 1 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 8.90211 75.632 0
      vertex 7 77.014 0
      vertex 8.61803 76.1895 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -9 1 0
      vertex 7 -0.999998 0
      vertex -7 -0.999998 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 8.61803 76.1895 0
      vertex 7 77.014 0
      vertex 8.17557 76.632 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -9 1 0
      vertex -7 -0.999998 0
      vertex -7.61803 -0.902113 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 8.17557 76.632 0
      vertex 7 77.014 0
      vertex 7.61803 76.9161 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -9 1 0
      vertex -7.61803 -0.902113 0
      vertex -8.17557 -0.618025 0
    endloop
  endfacet
  facet normal -0 0 -1
    outer loop
      vertex 7 77.014 0
      vertex -9 75.014 0
      vertex -7 77.014 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -9 1 0
      vertex -8.17557 -0.618025 0
      vertex -8.61803 -0.175566 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -7 77.014 0
      vertex -9 75.014 0
      vertex -7.61803 76.9161 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -9 1 0
      vertex -8.61803 -0.175566 0
      vertex -8.90211 0.381974 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -7.61803 76.9161 0
      vertex -9 75.014 0
      vertex -8.17557 76.632 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -8.17557 76.632 0
      vertex -9 75.014 0
      vertex -8.61803 76.1895 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -8.61803 76.1895 0
      vertex -9 75.014 0
      vertex -8.90211 75.632 0
    endloop
  endfacet
  facet normal -0 0.156427 0.987689
    outer loop
      vertex -3 12 8
      vertex 3 10.7639 8.19577
      vertex 3 12 8
    endloop
  endfacet
  facet normal 0 0.156427 0.987689
    outer loop
      vertex 3 10.7639 8.19577
      vertex -3 12 8
      vertex -3 10.7639 8.19577
    endloop
  endfacet
  facet normal -0 0.454002 0.891
    outer loop
      vertex -3 10.7639 8.19577
      vertex 3 9.64886 8.76393
      vertex 3 10.7639 8.19577
    endloop
  endfacet
  facet normal 0 0.454002 0.891
    outer loop
      vertex 3 9.64886 8.76393
      vertex -3 10.7639 8.19577
      vertex -3 9.64886 8.76393
    endloop
  endfacet
  facet normal 0 0.707107 0.707107
    outer loop
      vertex 3 9.64886 8.76393
      vertex -3 8.76393 9.64886
      vertex 3 8.76393 9.64886
    endloop
  endfacet
  facet normal 0 0.707107 0.707107
    outer loop
      vertex -3 8.76393 9.64886
      vertex 3 9.64886 8.76393
      vertex -3 9.64886 8.76393
    endloop
  endfacet
  facet normal 0 0.891 0.454002
    outer loop
      vertex 3 8.76393 9.64886
      vertex -3 8.19577 10.7639
      vertex 3 8.19577 10.7639
    endloop
  endfacet
  facet normal 0 0.891 0.454002
    outer loop
      vertex -3 8.19577 10.7639
      vertex 3 8.76393 9.64886
      vertex -3 8.76393 9.64886
    endloop
  endfacet
  facet normal 0 0.987689 0.156427
    outer loop
      vertex 3 8.19577 10.7639
      vertex -3 8 12
      vertex 3 8 12
    endloop
  endfacet
  facet normal 0 0.987689 0.156427
    outer loop
      vertex -3 8 12
      vertex 3 8.19577 10.7639
      vertex -3 8.19577 10.7639
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 3 8 12
      vertex -3 8 19.8676
      vertex 3 8 19.8676
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -3 8 19.8676
      vertex 3 8 12
      vertex -3 8 12
    endloop
  endfacet
  facet normal 0 0.996918 -0.0784533
    outer loop
      vertex 3 8 19.8676
      vertex -3 8.04924 20.4933
      vertex 3 8.04924 20.4933
    endloop
  endfacet
  facet normal 0 0.996918 -0.0784533
    outer loop
      vertex -3 8.04924 20.4933
      vertex 3 8 19.8676
      vertex -3 8 19.8676
    endloop
  endfacet
  facet normal 0 0.951054 -0.309025
    outer loop
      vertex 3 8.04924 20.4933
      vertex -3 8.43597 21.6835
      vertex 3 8.43597 21.6835
    endloop
  endfacet
  facet normal 0 0.951054 -0.309025
    outer loop
      vertex -3 8.43597 21.6835
      vertex 3 8.04924 20.4933
      vertex -3 8.04924 20.4933
    endloop
  endfacet
  facet normal 0 0.809026 -0.587773
    outer loop
      vertex 3 8.43597 21.6835
      vertex -3 9.17157 22.696
      vertex 3 9.17157 22.696
    endloop
  endfacet
  facet normal 0 0.809026 -0.587773
    outer loop
      vertex -3 9.17157 22.696
      vertex 3 8.43597 21.6835
      vertex -3 8.43597 21.6835
    endloop
  endfacet
  facet normal 0 0.7071 -0.707113
    outer loop
      vertex 3 9.17157 22.696
      vertex -3 10.8187 24.3431
      vertex 3 10.8187 24.3431
    endloop
  endfacet
  facet normal 0 0.7071 -0.707113
    outer loop
      vertex -3 10.8187 24.3431
      vertex 3 9.17157 22.696
      vertex -3 9.17157 22.696
    endloop
  endfacet
  facet normal 0 0.587773 -0.809026
    outer loop
      vertex -3 10.8187 24.3431
      vertex 3 11.8312 25.0787
      vertex 3 10.8187 24.3431
    endloop
  endfacet
  facet normal 0 0.587773 -0.809026
    outer loop
      vertex 3 11.8312 25.0787
      vertex -3 10.8187 24.3431
      vertex -3 11.8312 25.0787
    endloop
  endfacet
  facet normal 0 0.309003 -0.951061
    outer loop
      vertex -3 11.8312 25.0787
      vertex 3 13.0214 25.4654
      vertex 3 11.8312 25.0787
    endloop
  endfacet
  facet normal 0 0.309003 -0.951061
    outer loop
      vertex 3 13.0214 25.4654
      vertex -3 11.8312 25.0787
      vertex -3 13.0214 25.4654
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -3 13.0214 25.4654
      vertex 3 14.0623 25.4654
      vertex 3 13.0214 25.4654
    endloop
  endfacet
  facet normal -0 0 -1
    outer loop
      vertex 3 14.0623 25.4654
      vertex -3 13.0214 25.4654
      vertex -3 14.0623 25.4654
    endloop
  endfacet
  facet normal 0 0.707107 -0.707107
    outer loop
      vertex 3 14.0623 25.4654
      vertex -3 61.1855 72.5886
      vertex 3 61.1855 72.5886
    endloop
  endfacet
  facet normal 0 0.707107 -0.707107
    outer loop
      vertex -3 61.1855 72.5886
      vertex 3 14.0623 25.4654
      vertex -3 14.0623 25.4654
    endloop
  endfacet
  facet normal 0 0.649492 -0.760369
    outer loop
      vertex -3 61.1855 72.5886
      vertex 3 61.6628 72.9963
      vertex 3 61.1855 72.5886
    endloop
  endfacet
  facet normal 0 0.649492 -0.760369
    outer loop
      vertex 3 61.6628 72.9963
      vertex -3 61.1855 72.5886
      vertex -3 61.6628 72.9963
    endloop
  endfacet
  facet normal 0 0.453945 -0.89103
    outer loop
      vertex -3 61.6628 72.9963
      vertex 3 62.7779 73.5644
      vertex 3 61.6628 72.9963
    endloop
  endfacet
  facet normal 0 0.453945 -0.89103
    outer loop
      vertex 3 62.7779 73.5644
      vertex -3 61.6628 72.9963
      vertex -3 62.7779 73.5644
    endloop
  endfacet
  facet normal 0 0.156451 -0.987686
    outer loop
      vertex -3 62.7779 73.5644
      vertex 3 64.014 73.7602
      vertex 3 62.7779 73.5644
    endloop
  endfacet
  facet normal 0 0.156451 -0.987686
    outer loop
      vertex 3 64.014 73.7602
      vertex -3 62.7779 73.5644
      vertex -3 64.014 73.7602
    endloop
  endfacet
  facet normal 0 -0.156463 -0.987684
    outer loop
      vertex -3 64.014 73.7602
      vertex 3 65.25 73.5644
      vertex 3 64.014 73.7602
    endloop
  endfacet
  facet normal -0 -0.156463 -0.987684
    outer loop
      vertex 3 65.25 73.5644
      vertex -3 64.014 73.7602
      vertex -3 65.25 73.5644
    endloop
  endfacet
  facet normal 0 -0.453945 -0.89103
    outer loop
      vertex -3 65.25 73.5644
      vertex 3 66.3651 72.9963
      vertex 3 65.25 73.5644
    endloop
  endfacet
  facet normal -0 -0.453945 -0.89103
    outer loop
      vertex 3 66.3651 72.9963
      vertex -3 65.25 73.5644
      vertex -3 66.3651 72.9963
    endloop
  endfacet
  facet normal 0 -0.707147 -0.707067
    outer loop
      vertex -3 67.25 72.1113
      vertex 3 66.3651 72.9963
      vertex -3 66.3651 72.9963
    endloop
  endfacet
  facet normal 0 -0.707147 -0.707067
    outer loop
      vertex 3 66.3651 72.9963
      vertex -3 67.25 72.1113
      vertex 3 67.25 72.1113
    endloop
  endfacet
  facet normal 0 -0.890981 -0.454041
    outer loop
      vertex -3 67.8182 70.9963
      vertex 3 67.25 72.1113
      vertex -3 67.25 72.1113
    endloop
  endfacet
  facet normal 0 -0.890981 -0.454041
    outer loop
      vertex 3 67.25 72.1113
      vertex -3 67.8182 70.9963
      vertex 3 67.8182 70.9963
    endloop
  endfacet
  facet normal 0 -0.987686 -0.156451
    outer loop
      vertex -3 68.014 69.7602
      vertex 3 67.8182 70.9963
      vertex -3 67.8182 70.9963
    endloop
  endfacet
  facet normal 0 -0.987686 -0.156451
    outer loop
      vertex 3 67.8182 70.9963
      vertex -3 68.014 69.7602
      vertex 3 68.014 69.7602
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -3 68.014 12
      vertex 3 68.014 69.7602
      vertex -3 68.014 69.7602
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex 3 68.014 69.7602
      vertex -3 68.014 12
      vertex 3 68.014 12
    endloop
  endfacet
  facet normal 0 -0.987686 0.156451
    outer loop
      vertex -3 67.8182 10.7639
      vertex 3 68.014 12
      vertex -3 68.014 12
    endloop
  endfacet
  facet normal 0 -0.987686 0.156451
    outer loop
      vertex 3 68.014 12
      vertex -3 67.8182 10.7639
      vertex 3 67.8182 10.7639
    endloop
  endfacet
  facet normal 0 -0.890988 0.454028
    outer loop
      vertex -3 67.25 9.64886
      vertex 3 67.8182 10.7639
      vertex -3 67.8182 10.7639
    endloop
  endfacet
  facet normal 0 -0.890988 0.454028
    outer loop
      vertex 3 67.8182 10.7639
      vertex -3 67.25 9.64886
      vertex 3 67.25 9.64886
    endloop
  endfacet
  facet normal 0 -0.707119 0.707095
    outer loop
      vertex -3 66.3651 8.76393
      vertex 3 67.25 9.64886
      vertex -3 67.25 9.64886
    endloop
  endfacet
  facet normal 0 -0.707119 0.707095
    outer loop
      vertex 3 67.25 9.64886
      vertex -3 66.3651 8.76393
      vertex 3 66.3651 8.76393
    endloop
  endfacet
  facet normal 0 -0.453983 0.89101
    outer loop
      vertex -3 66.3651 8.76393
      vertex 3 65.25 8.19577
      vertex 3 66.3651 8.76393
    endloop
  endfacet
  facet normal 0 -0.453983 0.89101
    outer loop
      vertex 3 65.25 8.19577
      vertex -3 66.3651 8.76393
      vertex -3 65.25 8.19577
    endloop
  endfacet
  facet normal 0 -0.15644 0.987687
    outer loop
      vertex -3 65.25 8.19577
      vertex 3 64.014 8
      vertex 3 65.25 8.19577
    endloop
  endfacet
  facet normal 0 -0.15644 0.987687
    outer loop
      vertex 3 64.014 8
      vertex -3 65.25 8.19577
      vertex -3 64.014 8
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3 64.014 8
      vertex 3 12 8
      vertex 3 64.014 8
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 12 8
      vertex -3 64.014 8
      vertex -3 12 8
    endloop
  endfacet
  facet normal 0.156432 -0.987689 0
    outer loop
      vertex 7 -0.999998 0
      vertex 7.61803 -0.902113 3
      vertex 7 -0.999998 3
    endloop
  endfacet
  facet normal 0.156432 -0.987689 0
    outer loop
      vertex 7.61803 -0.902113 3
      vertex 7 -0.999998 0
      vertex 7.61803 -0.902113 0
    endloop
  endfacet
  facet normal -0.454 -0.891002 0
    outer loop
      vertex -8.17557 -0.618025 0
      vertex -7.61803 -0.902113 3
      vertex -8.17557 -0.618025 3
    endloop
  endfacet
  facet normal -0.454 -0.891002 -0
    outer loop
      vertex -7.61803 -0.902113 3
      vertex -8.17557 -0.618025 0
      vertex -7.61803 -0.902113 0
    endloop
  endfacet
  facet normal -0.987686 0.156448 0
    outer loop
      vertex -9 75.014 0
      vertex -8.90211 75.632 3
      vertex -8.90211 75.632 0
    endloop
  endfacet
  facet normal -0.987686 0.156448 0
    outer loop
      vertex -8.90211 75.632 3
      vertex -9 75.014 0
      vertex -9 75.014 3
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -9 1 0
      vertex -9 75.014 3
      vertex -9 75.014 0
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -9 75.014 3
      vertex -9 1 0
      vertex -9 1 3
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 7 77.014 0
      vertex -7 77.014 3
      vertex 7 77.014 3
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -7 77.014 3
      vertex 7 77.014 0
      vertex -7 77.014 0
    endloop
  endfacet
  facet normal -0.987687 -0.156441 0
    outer loop
      vertex -8.90211 0.381974 0
      vertex -9 1 3
      vertex -9 1 0
    endloop
  endfacet
  facet normal -0.987687 -0.156441 0
    outer loop
      vertex -9 1 3
      vertex -8.90211 0.381974 0
      vertex -8.90211 0.381974 3
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 9 1 3
      vertex 9 75.014 0
      vertex 9 75.014 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 9 75.014 0
      vertex 9 1 3
      vertex 9 1 0
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -7 -0.999998 0
      vertex 7 -0.999998 3
      vertex -7 -0.999998 3
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex 7 -0.999998 3
      vertex -7 -0.999998 0
      vertex 7 -0.999998 0
    endloop
  endfacet
  facet normal -0.707139 0.707075 0
    outer loop
      vertex -8.61803 76.1895 0
      vertex -8.17557 76.632 3
      vertex -8.17557 76.632 0
    endloop
  endfacet
  facet normal -0.707139 0.707075 0
    outer loop
      vertex -8.17557 76.632 3
      vertex -8.61803 76.1895 0
      vertex -8.61803 76.1895 3
    endloop
  endfacet
  facet normal -0.156432 -0.987689 0
    outer loop
      vertex -7.61803 -0.902113 0
      vertex -7 -0.999998 3
      vertex -7.61803 -0.902113 3
    endloop
  endfacet
  facet normal -0.156432 -0.987689 -0
    outer loop
      vertex -7 -0.999998 3
      vertex -7.61803 -0.902113 0
      vertex -7 -0.999998 0
    endloop
  endfacet
  facet normal -0.156456 0.987685 0
    outer loop
      vertex -7 77.014 0
      vertex -7.61803 76.9161 3
      vertex -7 77.014 3
    endloop
  endfacet
  facet normal -0.156456 0.987685 0
    outer loop
      vertex -7.61803 76.9161 3
      vertex -7 77.014 0
      vertex -7.61803 76.9161 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.35112 42.0255 3
      vertex -7.74724 42.6098 3
      vertex -7.46899 42.0813 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.74934 42.5378 3
      vertex -7.46899 42.0813 3
      vertex -7.74724 42.6098 3
    endloop
  endfacet
  facet normal -0 -0 1
    outer loop
      vertex -7.74434 42.4482 3
      vertex -7.46899 42.0813 3
      vertex -7.74934 42.5378 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.46899 42.0813 3
      vertex -7.74434 42.4482 3
      vertex -7.72929 42.3695 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.12486 31.3675 3
      vertex -4.32922 31.1185 3
      vertex -4.37354 31.4719 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.17352 31.1879 3
      vertex -4.32922 31.1185 3
      vertex -5.12486 31.3675 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.22876 30.9477 3
      vertex -4.34137 30.9346 3
      vertex -5.17352 31.1879 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.72795 31.7546 3
      vertex -4.37354 31.4719 3
      vertex -4.50644 31.6839 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.32922 31.1185 3
      vertex -5.17352 31.1879 3
      vertex -4.34137 30.9346 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.37776 30.7815 3
      vertex -5.22876 30.9477 3
      vertex -4.43843 30.6593 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.37354 31.4719 3
      vertex -4.72795 31.7546 3
      vertex -5.04128 31.5678 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.34137 30.9346 3
      vertex -5.22876 30.9477 3
      vertex -4.37776 30.7815 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.9942 31.6347 3
      vertex -4.72795 31.7546 3
      vertex -4.80971 31.7471 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.86247 41.8732 3
      vertex -4.65913 41.0401 3
      vertex -4.65913 42.2767 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.86247 41.8732 3
      vertex -5.87196 41.4199 3
      vertex -4.65913 41.0401 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.06551 41.8044 3
      vertex -5.87196 41.4199 3
      vertex -5.86247 41.8732 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.32974 41.7245 3
      vertex -5.87196 41.4199 3
      vertex -6.06551 41.8044 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.32974 41.7245 3
      vertex -6.4297 41.5741 3
      vertex -5.87196 41.4199 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -6.4297 41.5741 3
      vertex -6.32974 41.7245 3
      vertex -6.65518 41.6335 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.76358 43.1131 3
      vertex -4.65913 42.9816 3
      vertex -4.48285 43.2374 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 45.5435 3
      vertex -4.93207 43.7303 3
      vertex -5.19183 45.5162 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.08794 43.6804 3
      vertex -4.93207 43.7303 3
      vertex -5.53967 45.5435 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.08794 43.6804 3
      vertex -5.53967 45.5435 3
      vertex -5.89384 45.5154 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.93207 43.7303 3
      vertex -6.08794 43.6804 3
      vertex -4.76358 43.1131 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.31816 43.0704 3
      vertex -4.76358 43.1131 3
      vertex -6.08794 43.6804 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76358 43.1131 3
      vertex -6.31816 43.0704 3
      vertex -4.65913 42.9816 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.31816 43.0704 3
      vertex -7.20107 41.9658 3
      vertex -4.65913 42.9816 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.61339 43.2222 3
      vertex -7.20107 41.9658 3
      vertex -6.31816 43.0704 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.73035 42.768 3
      vertex -6.61339 43.2222 3
      vertex -6.8535 43.4148 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.73035 42.768 3
      vertex -6.8535 43.4148 3
      vertex -7.0385 43.6483 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.73035 42.768 3
      vertex -7.0385 43.6483 3
      vertex -7.16969 43.9191 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.20505 42.768 3
      vertex -7.16969 43.9191 3
      vertex -7.2484 44.2233 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.20505 42.768 3
      vertex -7.2484 44.2233 3
      vertex -7.27464 44.5609 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -7.35112 42.0255 3
      vertex -6.61339 43.2222 3
      vertex -7.73035 42.768 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3.85942 33.9366 3
      vertex -3.83318 31.1043 3
      vertex -3.83318 34.3047 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.85942 33.9366 3
      vertex -3.85994 31.5034 3
      vertex -3.83318 31.1043 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3.93814 33.617 3
      vertex -3.85994 31.5034 3
      vertex -3.85942 33.9366 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.93814 33.617 3
      vertex -3.94025 31.8337 3
      vertex -3.85994 31.5034 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.06935 33.3459 3
      vertex -3.94025 31.8337 3
      vertex -3.93814 33.617 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.06935 33.3459 3
      vertex -4.07408 32.0952 3
      vertex -3.94025 31.8337 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.25145 33.1236 3
      vertex -4.07408 32.0952 3
      vertex -4.06935 33.3459 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.25145 33.1236 3
      vertex -4.25829 32.2844 3
      vertex -4.07408 32.0952 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.48285 32.9503 3
      vertex -4.25829 32.2844 3
      vertex -4.25145 33.1236 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.48285 32.9503 3
      vertex -4.4897 32.3979 3
      vertex -4.25829 32.2844 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.76358 32.826 3
      vertex -4.4897 32.3979 3
      vertex -4.48285 32.9503 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76358 32.826 3
      vertex -4.76831 32.4358 3
      vertex -4.4897 32.3979 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76358 32.826 3
      vertex -4.88249 32.4306 3
      vertex -4.76831 32.4358 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.17178 32.3546 3
      vertex -4.76358 32.826 3
      vertex -4.93207 33.4432 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76358 32.826 3
      vertex -4.98772 32.4152 3
      vertex -4.88249 32.4306 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3.88301 36.4543 3
      vertex -3.83318 34.3047 3
      vertex -3.705 39.3731 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.88301 36.4543 3
      vertex -3.705 39.3731 3
      vertex -3.88301 37.1545 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.65005 38.2717 3
      vertex -3.705 39.3731 3
      vertex -4.61168 38.5519 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.705 39.3731 3
      vertex -4.66653 38.9079 3
      vertex -4.61168 38.5519 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.68764 39.3731 3
      vertex -4.66653 38.9079 3
      vertex -3.705 39.3731 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.68764 39.3731 3
      vertex -4.83109 39.1816 3
      vertex -4.66653 38.9079 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.10536 39.3826 3
      vertex -4.83109 39.1816 3
      vertex -4.68764 39.3731 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.83109 39.1816 3
      vertex -5.10536 39.3826 3
      vertex -5.10536 39.3731 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3.85942 44.2237 3
      vertex -3.705 40.04 3
      vertex -3.83318 44.5918 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3.93814 43.904 3
      vertex -3.705 40.04 3
      vertex -3.85942 44.2237 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.06935 43.6329 3
      vertex -3.705 40.04 3
      vertex -3.93814 43.904 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.65913 42.2767 3
      vertex -4.06935 43.6329 3
      vertex -4.25145 43.4106 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.65913 42.2767 3
      vertex -4.25145 43.4106 3
      vertex -4.48285 43.2374 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.65913 42.2767 3
      vertex -4.48285 43.2374 3
      vertex -4.65913 42.9816 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.06935 43.6329 3
      vertex -4.65913 42.2767 3
      vertex -3.705 40.04 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.65913 41.0401 3
      vertex -3.705 40.04 3
      vertex -4.65913 42.2767 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.65913 40.3423 3
      vertex -3.705 40.04 3
      vertex -4.65913 41.0401 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.65913 40.3423 3
      vertex -6.64093 40.04 3
      vertex -3.705 40.04 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.36246 41.3582 3
      vertex -6.64093 40.04 3
      vertex -4.65913 40.3423 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.64093 40.04 3
      vertex -7.36246 41.3582 3
      vertex -6.86852 40.0421 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.86852 40.0421 3
      vertex -7.36246 41.3582 3
      vertex -7.06393 40.0485 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.04601 41.7818 3
      vertex -7.22717 39.411 3
      vertex -7.22717 40.059 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 39.411 3
      vertex -8.04601 41.7818 3
      vertex -7.26146 38.7684 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.21478 42.131 3
      vertex -7.22717 36.4543 3
      vertex -8.15149 41.9423 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.88567 41.6372 3
      vertex -7.22717 40.059 3
      vertex -7.65782 41.4959 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.65782 41.4959 3
      vertex -7.22717 40.059 3
      vertex -7.36246 41.3582 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.06393 40.0485 3
      vertex -7.36246 41.3582 3
      vertex -7.22717 40.059 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.83318 34.3047 3
      vertex -3.88301 36.4543 3
      vertex -3.88223 34.8002 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.88301 36.4543 3
      vertex -4.02937 35.2109 3
      vertex -3.88223 34.8002 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.88301 36.4543 3
      vertex -4.27463 35.5366 3
      vertex -4.02937 35.2109 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.88301 36.4543 3
      vertex -4.61139 35.7726 3
      vertex -4.27463 35.5366 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.88301 36.4543 3
      vertex -5.03307 35.9142 3
      vertex -4.61139 35.7726 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.88301 36.4543 3
      vertex -5.53967 35.9614 3
      vertex -5.03307 35.9142 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.22717 36.4543 3
      vertex -5.53967 35.9614 3
      vertex -3.88301 36.4543 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 35.9614 3
      vertex -7.22717 36.4543 3
      vertex -6.04665 35.9125 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 36.4543 3
      vertex -6.47267 35.7657 3
      vertex -6.04665 35.9125 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 36.4543 3
      vertex -6.81775 35.5211 3
      vertex -6.47267 35.7657 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 36.4543 3
      vertex -7.07158 35.1868 3
      vertex -6.81775 35.5211 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 36.4543 3
      vertex -7.22388 34.7711 3
      vertex -7.07158 35.1868 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.15149 41.9423 3
      vertex -7.22717 37.1545 3
      vertex -7.27464 38.5946 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 37.1545 3
      vertex -8.15149 41.9423 3
      vertex -7.22717 36.4543 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 36.4543 3
      vertex -7.27464 34.2739 3
      vertex -7.22388 34.7711 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.705 39.3731 3
      vertex -4.65005 38.2717 3
      vertex -3.88301 37.1545 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.76517 38.0387 3
      vertex -3.88301 37.1545 3
      vertex -4.65005 38.2717 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.95703 37.8529 3
      vertex -3.88301 37.1545 3
      vertex -4.76517 38.0387 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.21901 37.7178 3
      vertex -3.88301 37.1545 3
      vertex -4.95703 37.8529 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.54456 37.6367 3
      vertex -3.88301 37.1545 3
      vertex -5.21901 37.7178 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.93367 37.6096 3
      vertex -3.88301 37.1545 3
      vertex -5.54456 37.6367 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 37.1545 3
      vertex -5.93367 37.6096 3
      vertex -6.32619 37.638 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.93367 37.6096 3
      vertex -7.22717 37.1545 3
      vertex -3.88301 37.1545 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.6557 37.7231 3
      vertex -7.22717 37.1545 3
      vertex -6.32619 37.638 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.9222 37.8648 3
      vertex -7.22717 37.1545 3
      vertex -6.6557 37.7231 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.118 38.0593 3
      vertex -7.22717 37.1545 3
      vertex -6.9222 37.8648 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.27464 38.5946 3
      vertex -7.22717 37.1545 3
      vertex -7.23547 38.3025 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.23547 38.3025 3
      vertex -7.22717 37.1545 3
      vertex -7.118 38.0593 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.90466 45.4344 3
      vertex -4.38383 44.5776 3
      vertex -4.41653 44.8686 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -4.93207 43.7303 3
      vertex -4.38383 44.5776 3
      vertex -5.19183 45.5162 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.90466 45.4344 3
      vertex -4.41653 44.8686 3
      vertex -4.51463 45.1087 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.38383 44.5776 3
      vertex -4.90466 45.4344 3
      vertex -5.19183 45.5162 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.44975 44.1994 3
      vertex -4.93207 43.7303 3
      vertex -4.53217 44.0376 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.90466 45.4344 3
      vertex -4.51463 45.1087 3
      vertex -4.67815 45.2979 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.53217 44.0376 3
      vertex -4.93207 43.7303 3
      vertex -4.64252 43.9016 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.40031 44.3794 3
      vertex -4.93207 43.7303 3
      vertex -4.44975 44.1994 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.64252 43.9016 3
      vertex -4.93207 43.7303 3
      vertex -4.77582 43.7992 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.38383 44.5776 3
      vertex -4.93207 43.7303 3
      vertex -4.40031 44.3794 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.18736 45.4312 3
      vertex -6.08794 43.6804 3
      vertex -5.89384 45.5154 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.69026 44.854 3
      vertex -6.18736 45.4312 3
      vertex -6.42023 45.2908 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.18736 45.4312 3
      vertex -6.72401 44.5609 3
      vertex -6.08794 43.6804 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.69026 44.854 3
      vertex -6.42023 45.2908 3
      vertex -6.589 45.0973 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.08794 43.6804 3
      vertex -6.72401 44.5609 3
      vertex -6.44131 43.8879 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.18736 45.4312 3
      vertex -6.69026 44.854 3
      vertex -6.72401 44.5609 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.44131 43.8879 3
      vertex -6.72401 44.5609 3
      vertex -6.65335 44.1815 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.90466 35.1473 3
      vertex -4.38383 34.2905 3
      vertex -4.41653 34.5815 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -4.93207 33.4432 3
      vertex -4.38383 34.2905 3
      vertex -5.19183 35.2292 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.90466 35.1473 3
      vertex -4.41653 34.5815 3
      vertex -4.51463 34.8216 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.38383 34.2905 3
      vertex -4.90466 35.1473 3
      vertex -5.19183 35.2292 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.44975 33.9123 3
      vertex -4.93207 33.4432 3
      vertex -4.53217 33.7505 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.90466 35.1473 3
      vertex -4.51463 34.8216 3
      vertex -4.67815 35.0108 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.53217 33.7505 3
      vertex -4.93207 33.4432 3
      vertex -4.64252 33.6146 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.40031 34.0923 3
      vertex -4.93207 33.4432 3
      vertex -4.44975 33.9123 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.64252 33.6146 3
      vertex -4.93207 33.4432 3
      vertex -4.77582 33.5121 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.38383 34.2905 3
      vertex -4.93207 33.4432 3
      vertex -4.40031 34.0923 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -5.17178 32.3546 3
      vertex -4.93207 33.4432 3
      vertex -6.08794 33.3933 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76358 32.826 3
      vertex -5.08397 32.3895 3
      vertex -4.98772 32.4152 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 35.2565 3
      vertex -4.93207 33.4432 3
      vertex -5.19183 35.2292 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76358 32.826 3
      vertex -5.17178 32.3546 3
      vertex -5.08397 32.3895 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.17178 32.3546 3
      vertex -6.08794 33.3933 3
      vertex -5.25169 32.3115 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.31816 32.7834 3
      vertex -5.25169 32.3115 3
      vertex -6.08794 33.3933 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.25169 32.3115 3
      vertex -6.31816 32.7834 3
      vertex -5.32368 32.2602 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.32368 32.2602 3
      vertex -6.31816 32.7834 3
      vertex -5.38843 32.2009 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.93207 33.4432 3
      vertex -5.53967 35.2565 3
      vertex -6.08794 33.3933 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.35614 32.5925 3
      vertex -5.38843 32.2009 3
      vertex -6.31816 32.7834 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.38843 32.2009 3
      vertex -6.35614 32.5925 3
      vertex -5.44659 32.1336 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.44659 32.1336 3
      vertex -6.35614 32.5925 3
      vertex -5.49815 32.0585 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -6.24458 31.916 3
      vertex -5.49815 32.0585 3
      vertex -6.35614 32.5925 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.49815 32.0585 3
      vertex -6.24458 31.916 3
      vertex -5.54431 31.9762 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.54431 31.9762 3
      vertex -6.24458 31.916 3
      vertex -5.58624 31.8876 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.58624 31.8876 3
      vertex -6.24458 31.916 3
      vertex -5.62395 31.7926 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.62395 31.7926 3
      vertex -6.24458 31.916 3
      vertex -5.66336 31.6692 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.08794 33.3933 3
      vertex -5.53967 35.2565 3
      vertex -5.89384 35.2284 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.40559 31.8556 3
      vertex -5.76514 31.2704 3
      vertex -6.24458 31.916 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.53415 31.7662 3
      vertex -5.76514 31.2704 3
      vertex -6.40559 31.8556 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.63029 31.6478 3
      vertex -5.76514 31.2704 3
      vertex -6.53415 31.7662 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.75014 31.0948 3
      vertex -5.8208 31.0121 3
      vertex -6.73682 31.3134 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -6.70055 30.6874 3
      vertex -5.87065 30.8163 3
      vertex -6.75014 31.0948 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.18736 35.1441 3
      vertex -6.08794 33.3933 3
      vertex -5.89384 35.2284 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.69026 34.567 3
      vertex -6.18736 35.1441 3
      vertex -6.42023 35.0037 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.18736 35.1441 3
      vertex -6.72401 34.2739 3
      vertex -6.08794 33.3933 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.69026 34.567 3
      vertex -6.42023 35.0037 3
      vertex -6.589 34.8102 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.08794 33.3933 3
      vertex -6.72401 34.2739 3
      vertex -6.44131 33.6009 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.18736 35.1441 3
      vertex -6.69026 34.567 3
      vertex -6.72401 34.2739 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.44131 33.6009 3
      vertex -6.72401 34.2739 3
      vertex -6.65335 33.8944 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.87065 30.8163 3
      vertex -6.70055 30.6874 3
      vertex -5.91469 30.683 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.91469 30.683 3
      vertex -6.70055 30.6874 3
      vertex -5.95926 30.5886 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.95926 30.5886 3
      vertex -6.70055 30.6874 3
      vertex -6.01067 30.5095 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.71042 31.4951 3
      vertex -6.24458 31.916 3
      vertex -5.76514 31.2704 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.66336 31.6692 3
      vertex -6.24458 31.916 3
      vertex -5.71042 31.4951 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.61339 32.9351 3
      vertex -6.35614 32.5925 3
      vertex -6.31816 32.7834 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.61339 32.9351 3
      vertex -6.63857 32.4938 3
      vertex -6.35614 32.5925 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.8535 33.1277 3
      vertex -6.63857 32.4938 3
      vertex -6.61339 32.9351 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.8535 33.1277 3
      vertex -6.86879 32.3372 3
      vertex -6.63857 32.4938 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.0385 33.3613 3
      vertex -6.86879 32.3372 3
      vertex -6.8535 33.1277 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.0385 33.3613 3
      vertex -7.04678 32.1225 3
      vertex -6.86879 32.3372 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.16969 33.632 3
      vertex -7.04678 32.1225 3
      vertex -7.0385 33.3613 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.16969 33.632 3
      vertex -7.17337 31.848 3
      vertex -7.04678 32.1225 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.2484 33.9362 3
      vertex -7.17337 31.848 3
      vertex -7.16969 33.632 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.2484 33.9362 3
      vertex -7.24933 31.5117 3
      vertex -7.17337 31.848 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.27464 34.2739 3
      vertex -7.24933 31.5117 3
      vertex -7.2484 33.9362 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.24933 31.5117 3
      vertex -7.27464 34.2739 3
      vertex -7.27464 31.1138 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.01067 30.5095 3
      vertex -6.30391 30.3614 3
      vertex -6.06895 30.4457 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.76514 31.2704 3
      vertex -6.73682 31.3134 3
      vertex -5.8208 31.0121 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.69687 31.4978 3
      vertex -5.76514 31.2704 3
      vertex -6.63029 31.6478 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -6.55182 30.4429 3
      vertex -6.01067 30.5095 3
      vertex -6.70055 30.6874 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.73682 31.3134 3
      vertex -5.76514 31.2704 3
      vertex -6.69687 31.4978 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.8208 31.0121 3
      vertex -6.75014 31.0948 3
      vertex -5.87065 30.8163 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.06895 30.4457 3
      vertex -6.21451 30.3708 3
      vertex -6.1362 30.3989 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -6.21451 30.3708 3
      vertex -6.06895 30.4457 3
      vertex -6.30391 30.3614 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.01067 30.5095 3
      vertex -6.55182 30.4429 3
      vertex -6.30391 30.3614 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.87645 39.379 3
      vertex -6.81421 39.3731 3
      vertex -6.81421 39.3778 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.87645 39.379 3
      vertex -6.95134 39.2916 3
      vertex -6.81421 39.3731 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.95239 39.3826 3
      vertex -6.95134 39.2916 3
      vertex -6.87645 39.379 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.04207 39.3885 3
      vertex -6.95134 39.2916 3
      vertex -6.95239 39.3826 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.04207 39.3885 3
      vertex -7.06526 39.1895 3
      vertex -6.95134 39.2916 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.12697 39.3958 3
      vertex -7.06526 39.1895 3
      vertex -7.04207 39.3885 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.18867 39.4033 3
      vertex -7.06526 39.1895 3
      vertex -7.12697 39.3958 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.06526 39.1895 3
      vertex -7.18867 39.4033 3
      vertex -7.15599 39.0669 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 39.411 3
      vertex -7.15599 39.0669 3
      vertex -7.18867 39.4033 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.15599 39.0669 3
      vertex -7.22717 39.411 3
      vertex -7.22191 38.9258 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22191 38.9258 3
      vertex -7.22717 39.411 3
      vertex -7.26146 38.7684 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.76358 43.1879 3
      vertex 4.98772 43.5987 3
      vertex 4.88249 43.5833 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.76358 43.1879 3
      vertex 4.88249 43.5833 3
      vertex 4.76831 43.5782 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.98772 43.5987 3
      vertex 4.76358 43.1879 3
      vertex 4.93207 42.5708 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.4897 43.616 3
      vertex 4.76358 43.1879 3
      vertex 4.76831 43.5782 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.4897 43.616 3
      vertex 4.48285 43.0637 3
      vertex 4.76358 43.1879 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.25829 43.7296 3
      vertex 4.48285 43.0637 3
      vertex 4.4897 43.616 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.25829 43.7296 3
      vertex 4.25145 42.8904 3
      vertex 4.48285 43.0637 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.07408 43.9188 3
      vertex 4.25145 42.8904 3
      vertex 4.25829 43.7296 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.07408 43.9188 3
      vertex 4.06935 42.6681 3
      vertex 4.25145 42.8904 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.94025 44.1802 3
      vertex 4.06935 42.6681 3
      vertex 4.07408 43.9188 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.94025 44.1802 3
      vertex 3.93814 42.397 3
      vertex 4.06935 42.6681 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.85994 44.5105 3
      vertex 3.93814 42.397 3
      vertex 3.94025 44.1802 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.85994 44.5105 3
      vertex 3.85942 42.0774 3
      vertex 3.93814 42.397 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.83318 44.9097 3
      vertex 3.85942 42.0774 3
      vertex 3.85994 44.5105 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.85942 42.0774 3
      vertex 3.83318 44.9097 3
      vertex 3.83318 41.7092 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.44131 32.126 3
      vertex 6.72401 31.453 3
      vertex 6.65335 31.8325 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 32.3336 3
      vertex 6.72401 31.453 3
      vertex 6.44131 32.126 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 6.18736 30.5828 3
      vertex 6.72401 31.453 3
      vertex 6.08794 32.3336 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 6.42023 30.7232 3
      vertex 6.69026 31.1599 3
      vertex 6.18736 30.5828 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.69026 31.1599 3
      vertex 6.42023 30.7232 3
      vertex 6.589 30.9167 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.72401 31.453 3
      vertex 6.18736 30.5828 3
      vertex 6.69026 31.1599 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.18736 30.5828 3
      vertex 6.08794 32.3336 3
      vertex 5.89384 30.4985 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.38383 31.4364 3
      vertex 5.19183 30.4977 3
      vertex 4.93207 32.2837 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.53217 31.9764 3
      vertex 4.93207 32.2837 3
      vertex 4.77582 32.2148 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.19183 30.4977 3
      vertex 4.38383 31.4364 3
      vertex 4.90466 30.5796 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.53217 31.9764 3
      vertex 4.77582 32.2148 3
      vertex 4.64252 32.1123 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 32.2837 3
      vertex 4.53217 31.9764 3
      vertex 4.44975 31.8146 3
    endloop
  endfacet
  facet normal -0 -0 1
    outer loop
      vertex 4.41653 31.1454 3
      vertex 4.90466 30.5796 3
      vertex 4.38383 31.4364 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 32.2837 3
      vertex 4.44975 31.8146 3
      vertex 4.40031 31.6346 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.90466 30.5796 3
      vertex 4.41653 31.1454 3
      vertex 4.67815 30.7161 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 32.2837 3
      vertex 4.40031 31.6346 3
      vertex 4.38383 31.4364 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.67815 30.7161 3
      vertex 4.41653 31.1454 3
      vertex 4.51463 30.9053 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.9942 44.3793 3
      vertex 4.72795 44.2594 3
      vertex 4.80971 44.2669 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.22876 45.0663 3
      vertex 4.34137 45.0794 3
      vertex 5.17352 44.8261 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.37776 45.2325 3
      vertex 5.22876 45.0663 3
      vertex 4.43843 45.3547 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.37354 44.5421 3
      vertex 5.12486 44.6465 3
      vertex 4.32922 44.8954 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.34137 45.0794 3
      vertex 5.22876 45.0663 3
      vertex 4.37776 45.2325 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.32922 44.8954 3
      vertex 5.17352 44.8261 3
      vertex 4.34137 45.0794 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.12486 44.6465 3
      vertex 4.37354 44.5421 3
      vertex 4.72795 44.2594 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.17352 44.8261 3
      vertex 4.32922 44.8954 3
      vertex 5.12486 44.6465 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.72795 44.2594 3
      vertex 4.37354 44.5421 3
      vertex 4.50644 44.33 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.4297 34.4398 3
      vertex 6.32974 34.2895 3
      vertex 6.65518 34.3805 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.87196 34.5941 3
      vertex 6.32974 34.2895 3
      vertex 6.4297 34.4398 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.32974 34.2895 3
      vertex 5.87196 34.5941 3
      vertex 6.06551 34.2096 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.87196 34.5941 3
      vertex 5.86247 34.1408 3
      vertex 6.06551 34.2096 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.65913 34.9739 3
      vertex 5.86247 34.1408 3
      vertex 5.87196 34.5941 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.86247 34.1408 3
      vertex 4.65913 34.9739 3
      vertex 4.65913 33.7373 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.46899 33.9327 3
      vertex 7.74934 33.4762 3
      vertex 7.74434 33.5658 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74934 33.4762 3
      vertex 7.46899 33.9327 3
      vertex 7.74724 33.4042 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.35112 33.9885 3
      vertex 7.74724 33.4042 3
      vertex 7.46899 33.9327 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.61774 33.8289 3
      vertex 7.74434 33.5658 3
      vertex 7.72929 33.6445 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7 77.014 3
      vertex 9 75.014 3
      vertex 8.90211 75.632 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 8.23589 33.6661 3
      vertex 9 1 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7 77.014 3
      vertex 8.90211 75.632 3
      vertex 8.61803 76.1895 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 8.23245 33.5129 3
      vertex 9 1 3
      vertex 8.23589 33.6661 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 8.22217 33.3728 3
      vertex 9 1 3
      vertex 8.23245 33.5129 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 8.21478 33.883 3
      vertex 8.23589 33.6661 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7 77.014 3
      vertex 8.61803 76.1895 3
      vertex 8.17557 76.632 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 7.27464 44.9002 3
      vertex 8.21478 33.883 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.27464 41.7401 3
      vertex 8.21478 33.883 3
      vertex 7.27464 44.9002 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.22717 39.5596 3
      vertex 8.21478 33.883 3
      vertex 7.27464 41.7401 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.21478 33.883 3
      vertex 7.22717 39.5596 3
      vertex 8.15149 34.0717 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7 77.014 3
      vertex 8.17557 76.632 3
      vertex 7.61803 76.9161 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.22717 38.8595 3
      vertex 8.15149 34.0717 3
      vertex 7.22717 39.5596 3
    endloop
  endfacet
  facet normal -0 -0 1
    outer loop
      vertex 7.27464 37.4194 3
      vertex 8.15149 34.0717 3
      vertex 7.22717 38.8595 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 7.24576 45.3323 3
      vertex 7.27464 44.9002 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 7.15913 45.6887 3
      vertex 7.24576 45.3323 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 7.01477 45.9694 3
      vertex 7.15913 45.6887 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 7 77.014 3
      vertex 3 76.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 6.81578 46.1718 3
      vertex 7.01477 45.9694 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 6.56538 46.2932 3
      vertex 6.81578 46.1718 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.67101 46.2459 3
      vertex 9 75.014 3
      vertex 3 76.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 6.26357 46.3337 3
      vertex 6.56538 46.2932 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 6.12973 46.3266 3
      vertex 6.26357 46.3337 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 75.014 3
      vertex 4.67101 46.2459 3
      vertex 6.12973 46.3266 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.12973 46.3266 3
      vertex 4.67101 46.2459 3
      vertex 6.00673 46.3053 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.00673 46.3053 3
      vertex 4.67101 46.2459 3
      vertex 5.89453 46.2697 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.89453 46.2697 3
      vertex 4.67101 46.2459 3
      vertex 5.79272 46.2206 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.79272 46.2206 3
      vertex 4.67101 46.2459 3
      vertex 5.70094 46.1589 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.61919 46.0845 3
      vertex 4.67101 46.2459 3
      vertex 5.54561 45.9942 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.54561 45.9942 3
      vertex 4.67101 46.2459 3
      vertex 5.47836 45.8846 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.47836 45.8846 3
      vertex 4.67101 46.2459 3
      vertex 5.41745 45.7558 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.76358 45.5671 3
      vertex 5.41745 45.7558 3
      vertex 4.67101 46.2459 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.41745 45.7558 3
      vertex 4.76358 45.5671 3
      vertex 5.35799 45.5869 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.35799 45.5869 3
      vertex 4.76358 45.5671 3
      vertex 5.29509 45.3571 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.29509 45.3571 3
      vertex 4.76358 45.5671 3
      vertex 5.22876 45.0663 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.63145 45.5203 3
      vertex 5.22876 45.0663 3
      vertex 4.76358 45.5671 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.52307 45.4495 3
      vertex 5.22876 45.0663 3
      vertex 4.63145 45.5203 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.43843 45.3547 3
      vertex 5.22876 45.0663 3
      vertex 4.52307 45.4495 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.72795 44.2594 3
      vertex 5.08281 44.5275 3
      vertex 5.12486 44.6465 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.72795 44.2594 3
      vertex 4.9942 44.3793 3
      vertex 5.04128 44.4462 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.9942 44.3793 3
      vertex 4.80971 44.2669 3
      vertex 4.94159 44.327 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.94159 44.327 3
      vertex 4.80971 44.2669 3
      vertex 4.88092 44.2894 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.72795 44.2594 3
      vertex 5.04128 44.4462 3
      vertex 5.08281 44.5275 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.70094 46.1589 3
      vertex 4.67101 46.2459 3
      vertex 5.61919 46.0845 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.67101 46.2459 3
      vertex 3 76.014 3
      vertex 4.40016 46.1611 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.40016 46.1611 3
      vertex 3 76.014 3
      vertex 4.18576 46.027 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.18576 46.027 3
      vertex 3 76.014 3
      vertex 4.02782 45.8436 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.02782 45.8436 3
      vertex 3 76.014 3
      vertex 3.91968 45.6011 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.83318 44.9097 3
      vertex 3.705 36.6409 3
      vertex 3.83318 41.7092 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.705 36.6409 3
      vertex 3 76.014 3
      vertex 3.705 35.9739 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.83318 44.9097 3
      vertex 3 76.014 3
      vertex 3.705 36.6409 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.8548 45.2898 3
      vertex 3 76.014 3
      vertex 3.83318 44.9097 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.91968 45.6011 3
      vertex 3 76.014 3
      vertex 3.8548 45.2898 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7 77.014 3
      vertex -3 76.014 3
      vertex 3 76.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 76.014 3
      vertex -3.705 40.04 3
      vertex -3 0 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 76.014 3
      vertex -3.83318 44.5918 3
      vertex -3.705 40.04 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 76.014 3
      vertex -3.88223 45.0873 3
      vertex -3.83318 44.5918 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 76.014 3
      vertex -4.02937 45.4979 3
      vertex -3.88223 45.0873 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 76.014 3
      vertex -4.27463 45.8236 3
      vertex -4.02937 45.4979 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 76.014 3
      vertex -4.61139 46.0596 3
      vertex -4.27463 45.8236 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 76.014 3
      vertex -5.03307 46.2013 3
      vertex -4.61139 46.0596 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -9 75.014 3
      vertex -5.03307 46.2013 3
      vertex -3 76.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.03307 46.2013 3
      vertex -9 75.014 3
      vertex -5.53967 46.2485 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 46.2485 3
      vertex -9 75.014 3
      vertex -6.04665 46.1996 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.04665 46.1996 3
      vertex -9 75.014 3
      vertex -6.47267 46.0528 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7 77.014 3
      vertex -3 76.014 3
      vertex 7 77.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 75.014 3
      vertex -3 76.014 3
      vertex -7 77.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.47267 46.0528 3
      vertex -9 75.014 3
      vertex -6.81775 45.8082 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.81775 45.8082 3
      vertex -9 75.014 3
      vertex -7.07158 45.4739 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -8.20505 42.768 3
      vertex -7.07158 45.4739 3
      vertex -9 75.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.07158 45.4739 3
      vertex -8.20505 42.768 3
      vertex -7.22388 45.0582 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.61339 43.2222 3
      vertex -7.35112 42.0255 3
      vertex -7.20107 41.9658 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.74091 42.6865 3
      vertex -7.35112 42.0255 3
      vertex -7.73035 42.768 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.74724 42.6098 3
      vertex -7.35112 42.0255 3
      vertex -7.74091 42.6865 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 75.014 3
      vertex -7 77.014 3
      vertex -7.61803 76.9161 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.46899 42.0813 3
      vertex -7.72929 42.3695 3
      vertex -7.5547 42.1331 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.5547 42.1331 3
      vertex -7.72929 42.3695 3
      vertex -7.61774 42.185 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.61774 42.185 3
      vertex -7.72929 42.3695 3
      vertex -7.66759 42.2412 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.66759 42.2412 3
      vertex -7.72929 42.3695 3
      vertex -7.70422 42.3016 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 75.014 3
      vertex -7.61803 76.9161 3
      vertex -8.17557 76.632 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22388 45.0582 3
      vertex -8.20505 42.768 3
      vertex -7.27464 44.5609 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.16969 43.9191 3
      vertex -8.20505 42.768 3
      vertex -7.73035 42.768 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.20505 42.768 3
      vertex -9 75.014 3
      vertex -8.22217 42.6411 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.22217 42.6411 3
      vertex -9 75.014 3
      vertex -8.23245 42.5011 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 75.014 3
      vertex -8.17557 76.632 3
      vertex -8.61803 76.1895 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 8.20505 33.246 3
      vertex 9 1 3
      vertex 8.22217 33.3728 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.07158 30.5401 3
      vertex 9 1 3
      vertex 8.20505 33.246 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.81775 30.2058 3
      vertex 9 1 3
      vertex 7.07158 30.5401 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.47267 29.9612 3
      vertex 9 1 3
      vertex 6.81775 30.2058 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.16969 32.0949 3
      vertex 8.20505 33.246 3
      vertex 7.73035 33.246 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.61774 33.8289 3
      vertex 7.72929 33.6445 3
      vertex 7.70422 33.7124 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74724 33.4042 3
      vertex 7.35112 33.9885 3
      vertex 7.74091 33.3275 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.61774 33.8289 3
      vertex 7.70422 33.7124 3
      vertex 7.66759 33.7728 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.07158 30.5401 3
      vertex 8.20505 33.246 3
      vertex 7.22388 30.9558 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74434 33.5658 3
      vertex 7.61774 33.8289 3
      vertex 7.5547 33.8809 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74434 33.5658 3
      vertex 7.5547 33.8809 3
      vertex 7.46899 33.9327 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74091 33.3275 3
      vertex 7.35112 33.9885 3
      vertex 7.73035 33.246 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.73035 33.246 3
      vertex 7.35112 33.9885 3
      vertex 6.61339 32.7918 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.20505 33.246 3
      vertex 7.27464 31.453 3
      vertex 7.22388 30.9558 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.04665 29.8144 3
      vertex 9 1 3
      vertex 6.47267 29.9612 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.53967 29.7655 3
      vertex 9 1 3
      vertex 6.04665 29.8144 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.03307 29.8127 3
      vertex 9 1 3
      vertex 5.53967 29.7655 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 7 -0.999998 3
      vertex 9 1 3
      vertex 3 0 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.90211 0.381974 3
      vertex 7 -0.999998 3
      vertex 8.61803 -0.175566 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.61803 -0.175566 3
      vertex 7 -0.999998 3
      vertex 8.17557 -0.618025 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 1 3
      vertex 7 -0.999998 3
      vertex 8.90211 0.381974 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 9 1 3
      vertex 5.03307 29.8127 3
      vertex 3 0 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 0 3
      vertex 5.03307 29.8127 3
      vertex 4.61139 29.9543 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 0 3
      vertex 4.61139 29.9543 3
      vertex 4.27463 30.1903 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 0 3
      vertex 4.27463 30.1903 3
      vertex 4.02937 30.516 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 0 3
      vertex 4.02937 30.516 3
      vertex 3.88223 30.9267 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 0 3
      vertex 3.88223 30.9267 3
      vertex 3.83318 31.4222 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 0 3
      vertex 3.705 35.9739 3
      vertex 3 76.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3 0 3
      vertex 3.83318 31.4222 3
      vertex 3.705 35.9739 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.17557 -0.618025 3
      vertex 7 -0.999998 3
      vertex 7.61803 -0.902113 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3 0 3
      vertex 7 -0.999998 3
      vertex 3 0 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3.705 39.3731 3
      vertex -3 0 3
      vertex -3.705 40.04 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.83318 31.1043 3
      vertex -3.705 39.3731 3
      vertex -3.83318 34.3047 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.705 39.3731 3
      vertex -3.83318 31.1043 3
      vertex -3 0 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3.8548 30.7242 3
      vertex -3 0 3
      vertex -3.83318 31.1043 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -3.91968 30.4129 3
      vertex -3 0 3
      vertex -3.8548 30.7242 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.02782 30.1704 3
      vertex -3 0 3
      vertex -3.91968 30.4129 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.18576 29.987 3
      vertex -3 0 3
      vertex -4.02782 30.1704 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.40016 29.8528 3
      vertex -3 0 3
      vertex -4.18576 29.987 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.67101 29.7681 3
      vertex -3 0 3
      vertex -4.40016 29.8528 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.41745 30.2582 3
      vertex -4.67101 29.7681 3
      vertex -4.76358 30.4469 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.94159 31.687 3
      vertex -4.80971 31.7471 3
      vertex -4.88092 31.7246 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.43843 30.6593 3
      vertex -5.22876 30.9477 3
      vertex -4.52307 30.5645 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.80971 31.7471 3
      vertex -4.94159 31.687 3
      vertex -4.9942 31.6347 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.72795 31.7546 3
      vertex -4.9942 31.6347 3
      vertex -5.04128 31.5678 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.37354 31.4719 3
      vertex -5.04128 31.5678 3
      vertex -5.08281 31.4865 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.37354 31.4719 3
      vertex -5.08281 31.4865 3
      vertex -5.12486 31.3675 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.52307 30.5645 3
      vertex -5.22876 30.9477 3
      vertex -4.63145 30.4937 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.63145 30.4937 3
      vertex -5.22876 30.9477 3
      vertex -4.76358 30.4469 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76358 30.4469 3
      vertex -5.22876 30.9477 3
      vertex -5.29509 30.6569 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76358 30.4469 3
      vertex -5.29509 30.6569 3
      vertex -5.35799 30.4271 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.41745 30.2582 3
      vertex -4.76358 30.4469 3
      vertex -5.35799 30.4271 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.67101 29.7681 3
      vertex -5.41745 30.2582 3
      vertex -5.47836 30.1294 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.67101 29.7681 3
      vertex -5.47836 30.1294 3
      vertex -5.54561 30.0198 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.67101 29.7681 3
      vertex -5.54561 30.0198 3
      vertex -5.61919 29.9295 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.67101 29.7681 3
      vertex -5.61919 29.9295 3
      vertex -5.70094 29.8551 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.79272 29.7934 3
      vertex -4.67101 29.7681 3
      vertex -5.70094 29.8551 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.89453 29.7443 3
      vertex -4.67101 29.7681 3
      vertex -5.79272 29.7934 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.00673 29.7087 3
      vertex -4.67101 29.7681 3
      vertex -5.89453 29.7443 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.12973 29.6874 3
      vertex -4.67101 29.7681 3
      vertex -6.00673 29.7087 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -4.67101 29.7681 3
      vertex -6.12973 29.6874 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -6.12973 29.6874 3
      vertex -6.26357 29.6802 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -6.26357 29.6802 3
      vertex -6.56538 29.7207 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -6.56538 29.7207 3
      vertex -6.81578 29.8422 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 0 3
      vertex -7 -0.999998 3
      vertex 7 -0.999998 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.67101 29.7681 3
      vertex -9 1 3
      vertex -3 0 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -6.81578 29.8422 3
      vertex -7.01477 30.0446 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -7.01477 30.0446 3
      vertex -7.15913 30.3253 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -7.15913 30.3253 3
      vertex -7.24576 30.6817 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -7.24576 30.6817 3
      vertex -7.27464 31.1138 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.04601 41.7818 3
      vertex -7.22717 40.059 3
      vertex -7.88567 41.6372 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3 0 3
      vertex -9 1 3
      vertex -7 -0.999998 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.26146 38.7684 3
      vertex -8.04601 41.7818 3
      vertex -7.27464 38.5946 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.15149 41.9423 3
      vertex -7.27464 38.5946 3
      vertex -8.04601 41.7818 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 36.4543 3
      vertex -8.21478 42.131 3
      vertex -7.27464 34.2739 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.27464 34.2739 3
      vertex -8.21478 42.131 3
      vertex -7.27464 31.1138 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7 -0.999998 3
      vertex -9 1 3
      vertex -7.61803 -0.902113 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.27464 31.1138 3
      vertex -8.21478 42.131 3
      vertex -9 1 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -8.21478 42.131 3
      vertex -8.23589 42.3479 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.23245 42.5011 3
      vertex -9 75.014 3
      vertex -8.23589 42.3479 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 1 3
      vertex -8.23589 42.3479 3
      vertex -9 75.014 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -9 75.014 3
      vertex -8.61803 76.1895 3
      vertex -8.90211 75.632 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.61803 -0.902113 3
      vertex -9 1 3
      vertex -8.17557 -0.618025 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.17557 -0.618025 3
      vertex -9 1 3
      vertex -8.61803 -0.175566 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.61803 -0.175566 3
      vertex -9 1 3
      vertex -8.90211 0.381974 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.83109 36.8324 3
      vertex 5.10536 36.6314 3
      vertex 5.10536 36.6409 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.83109 36.8324 3
      vertex 4.68764 36.6409 3
      vertex 5.10536 36.6314 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.66653 37.1061 3
      vertex 4.68764 36.6409 3
      vertex 4.83109 36.8324 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.705 36.6409 3
      vertex 4.66653 37.1061 3
      vertex 4.61168 37.4621 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.65005 37.7423 3
      vertex 3.705 36.6409 3
      vertex 4.61168 37.4621 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.705 36.6409 3
      vertex 3.88301 39.5596 3
      vertex 3.83318 41.7092 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.66653 37.1061 3
      vertex 3.705 36.6409 3
      vertex 4.68764 36.6409 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.88301 39.5596 3
      vertex 3.705 36.6409 3
      vertex 3.88301 38.8595 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.87065 45.1976 3
      vertex 6.75014 44.9192 3
      vertex 6.70055 45.3266 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.8208 45.0018 3
      vertex 6.75014 44.9192 3
      vertex 5.87065 45.1976 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.76514 44.7435 3
      vertex 6.73682 44.7005 3
      vertex 5.8208 45.0018 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.01067 45.5045 3
      vertex 6.70055 45.3266 3
      vertex 6.55182 45.5711 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.75014 44.9192 3
      vertex 5.8208 45.0018 3
      vertex 6.73682 44.7005 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.69687 44.5162 3
      vertex 5.76514 44.7435 3
      vertex 6.63029 44.3661 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.01067 45.5045 3
      vertex 6.55182 45.5711 3
      vertex 6.30391 45.6526 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.73682 44.7005 3
      vertex 5.76514 44.7435 3
      vertex 6.69687 44.5162 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.01067 45.5045 3
      vertex 6.30391 45.6526 3
      vertex 6.21451 45.6432 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.22191 37.0882 3
      vertex 7.22717 36.6029 3
      vertex 7.26146 37.2456 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.15599 36.9471 3
      vertex 7.22717 36.6029 3
      vertex 7.22191 37.0882 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22717 36.6029 3
      vertex 7.15599 36.9471 3
      vertex 7.18867 36.6107 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.06526 36.8244 3
      vertex 7.18867 36.6107 3
      vertex 7.15599 36.9471 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.18867 36.6107 3
      vertex 7.06526 36.8244 3
      vertex 7.12697 36.6182 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.06526 36.8244 3
      vertex 7.04207 36.6255 3
      vertex 7.12697 36.6182 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.95134 36.7224 3
      vertex 7.04207 36.6255 3
      vertex 7.06526 36.8244 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.04207 36.6255 3
      vertex 6.95134 36.7224 3
      vertex 6.95239 36.6314 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.95134 36.7224 3
      vertex 6.87645 36.635 3
      vertex 6.95239 36.6314 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.81421 36.6409 3
      vertex 6.87645 36.635 3
      vertex 6.95134 36.7224 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.87645 36.635 3
      vertex 6.81421 36.6409 3
      vertex 6.81421 36.6361 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.20505 33.246 3
      vertex 7.2484 31.7907 3
      vertex 7.27464 31.453 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.61339 32.7918 3
      vertex 7.35112 33.9885 3
      vertex 7.20107 34.0482 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.20505 33.246 3
      vertex 7.16969 32.0949 3
      vertex 7.2484 31.7907 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.73035 33.246 3
      vertex 7.0385 32.3656 3
      vertex 7.16969 32.0949 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.73035 33.246 3
      vertex 6.8535 32.5992 3
      vertex 7.0385 32.3656 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.73035 33.246 3
      vertex 6.61339 32.7918 3
      vertex 6.8535 32.5992 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.20107 34.0482 3
      vertex 6.31816 32.9435 3
      vertex 6.61339 32.7918 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 32.3336 3
      vertex 5.53967 30.4704 3
      vertex 5.89384 30.4985 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.93207 32.2837 3
      vertex 5.53967 30.4704 3
      vertex 6.08794 32.3336 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.76358 32.9008 3
      vertex 6.08794 32.3336 3
      vertex 6.31816 32.9435 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.53967 30.4704 3
      vertex 4.93207 32.2837 3
      vertex 5.19183 30.4977 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.65913 33.0324 3
      vertex 6.31816 32.9435 3
      vertex 7.20107 34.0482 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 32.3336 3
      vertex 4.76358 32.9008 3
      vertex 4.93207 32.2837 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.31816 32.9435 3
      vertex 4.65913 33.0324 3
      vertex 4.76358 32.9008 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.76358 32.9008 3
      vertex 4.65913 33.0324 3
      vertex 4.48285 32.7766 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.26146 37.2456 3
      vertex 8.04601 34.2321 3
      vertex 7.27464 37.4194 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.22717 36.6029 3
      vertex 8.04601 34.2321 3
      vertex 7.26146 37.2456 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.22388 41.2429 3
      vertex 7.22717 39.5596 3
      vertex 7.27464 41.7401 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.07158 40.8271 3
      vertex 7.22717 39.5596 3
      vertex 7.22388 41.2429 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.81775 40.4929 3
      vertex 7.22717 39.5596 3
      vertex 7.07158 40.8271 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.47267 40.2483 3
      vertex 7.22717 39.5596 3
      vertex 6.81775 40.4929 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.04665 40.1015 3
      vertex 7.22717 39.5596 3
      vertex 6.47267 40.2483 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.53967 40.0526 3
      vertex 7.22717 39.5596 3
      vertex 6.04665 40.1015 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.88301 39.5596 3
      vertex 5.53967 40.0526 3
      vertex 5.03307 40.0998 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.53967 40.0526 3
      vertex 3.88301 39.5596 3
      vertex 7.22717 39.5596 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.61139 40.2414 3
      vertex 3.88301 39.5596 3
      vertex 5.03307 40.0998 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 40.4774 3
      vertex 3.88301 39.5596 3
      vertex 4.61139 40.2414 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.02937 40.8031 3
      vertex 3.88301 39.5596 3
      vertex 4.27463 40.4774 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.83318 41.7092 3
      vertex 3.88301 39.5596 3
      vertex 3.88223 41.2137 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.88223 41.2137 3
      vertex 3.88301 39.5596 3
      vertex 4.02937 40.8031 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.24933 44.5022 3
      vertex 7.27464 41.7401 3
      vertex 7.27464 44.9002 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.24933 44.5022 3
      vertex 7.2484 42.0778 3
      vertex 7.27464 41.7401 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.17337 44.166 3
      vertex 7.2484 42.0778 3
      vertex 7.24933 44.5022 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.17337 44.166 3
      vertex 7.16969 42.382 3
      vertex 7.2484 42.0778 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.04678 43.8915 3
      vertex 7.16969 42.382 3
      vertex 7.17337 44.166 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.04678 43.8915 3
      vertex 7.0385 42.6527 3
      vertex 7.16969 42.382 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.86879 43.6768 3
      vertex 7.0385 42.6527 3
      vertex 7.04678 43.8915 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.86879 43.6768 3
      vertex 6.8535 42.8862 3
      vertex 7.0385 42.6527 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.63857 43.5202 3
      vertex 6.8535 42.8862 3
      vertex 6.86879 43.6768 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.63857 43.5202 3
      vertex 6.61339 43.0789 3
      vertex 6.8535 42.8862 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.35614 43.4215 3
      vertex 6.61339 43.0789 3
      vertex 6.63857 43.5202 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.35614 43.4215 3
      vertex 6.31816 43.2306 3
      vertex 6.61339 43.0789 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.49815 43.9555 3
      vertex 6.35614 43.4215 3
      vertex 6.24458 44.098 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.06895 45.5683 3
      vertex 6.21451 45.6432 3
      vertex 6.1362 45.6151 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.44659 43.8804 3
      vertex 6.35614 43.4215 3
      vertex 5.49815 43.9555 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.63029 44.3661 3
      vertex 5.76514 44.7435 3
      vertex 6.53415 44.2477 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.21451 45.6432 3
      vertex 6.06895 45.5683 3
      vertex 6.01067 45.5045 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.15149 34.0717 3
      vertex 7.27464 37.4194 3
      vertex 8.04601 34.2321 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.22717 35.955 3
      vertex 8.04601 34.2321 3
      vertex 7.22717 36.6029 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.04601 34.2321 3
      vertex 7.22717 35.955 3
      vertex 7.88567 34.3768 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.88567 34.3768 3
      vertex 7.22717 35.955 3
      vertex 7.65782 34.518 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.65782 34.518 3
      vertex 7.22717 35.955 3
      vertex 7.36246 34.6558 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.06393 35.9655 3
      vertex 7.36246 34.6558 3
      vertex 7.22717 35.955 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.86852 35.9718 3
      vertex 7.36246 34.6558 3
      vertex 7.06393 35.9655 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.64093 35.9739 3
      vertex 7.36246 34.6558 3
      vertex 6.86852 35.9718 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.64093 35.9739 3
      vertex 4.65913 35.6717 3
      vertex 7.36246 34.6558 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.705 35.9739 3
      vertex 4.65913 34.9739 3
      vertex 4.65913 35.6717 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.65913 34.9739 3
      vertex 3.705 35.9739 3
      vertex 4.65913 33.7373 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.06935 32.381 3
      vertex 4.65913 33.7373 3
      vertex 3.705 35.9739 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.48285 32.7766 3
      vertex 4.65913 33.7373 3
      vertex 4.25145 32.6033 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.65913 33.7373 3
      vertex 4.48285 32.7766 3
      vertex 4.65913 33.0324 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.65913 33.7373 3
      vertex 4.06935 32.381 3
      vertex 4.25145 32.6033 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.06935 32.381 3
      vertex 3.705 35.9739 3
      vertex 3.93814 32.1099 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.85942 31.7903 3
      vertex 3.705 35.9739 3
      vertex 3.83318 31.4222 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.93814 32.1099 3
      vertex 3.705 35.9739 3
      vertex 3.85942 31.7903 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 3.705 35.9739 3
      vertex 4.65913 35.6717 3
      vertex 6.64093 35.9739 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.27464 37.4194 3
      vertex 7.22717 38.8595 3
      vertex 7.23547 37.7114 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22717 38.8595 3
      vertex 7.118 37.9547 3
      vertex 7.23547 37.7114 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22717 38.8595 3
      vertex 6.9222 38.1492 3
      vertex 7.118 37.9547 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22717 38.8595 3
      vertex 6.6557 38.2909 3
      vertex 6.9222 38.1492 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22717 38.8595 3
      vertex 6.32619 38.376 3
      vertex 6.6557 38.2909 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22717 38.8595 3
      vertex 5.93367 38.4043 3
      vertex 6.32619 38.376 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 3.88301 38.8595 3
      vertex 5.93367 38.4043 3
      vertex 7.22717 38.8595 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.93367 38.4043 3
      vertex 3.88301 38.8595 3
      vertex 5.54456 38.3773 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.705 36.6409 3
      vertex 4.65005 37.7423 3
      vertex 3.88301 38.8595 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.76517 37.9753 3
      vertex 3.88301 38.8595 3
      vertex 4.65005 37.7423 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.95703 38.161 3
      vertex 3.88301 38.8595 3
      vertex 4.76517 37.9753 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.21901 38.2962 3
      vertex 3.88301 38.8595 3
      vertex 4.95703 38.161 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.54456 38.3773 3
      vertex 3.88301 38.8595 3
      vertex 5.21901 38.2962 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.44131 42.4131 3
      vertex 6.72401 41.7401 3
      vertex 6.65335 42.1196 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 42.6207 3
      vertex 6.72401 41.7401 3
      vertex 6.44131 42.4131 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 6.18736 40.8699 3
      vertex 6.72401 41.7401 3
      vertex 6.08794 42.6207 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 6.42023 41.0103 3
      vertex 6.69026 41.447 3
      vertex 6.18736 40.8699 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.69026 41.447 3
      vertex 6.42023 41.0103 3
      vertex 6.589 41.2037 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.72401 41.7401 3
      vertex 6.18736 40.8699 3
      vertex 6.69026 41.447 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.70055 45.3266 3
      vertex 6.01067 45.5045 3
      vertex 5.95926 45.4254 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.70055 45.3266 3
      vertex 5.95926 45.4254 3
      vertex 5.91469 45.3309 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.70055 45.3266 3
      vertex 5.91469 45.3309 3
      vertex 5.87065 45.1976 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.40559 44.1583 3
      vertex 5.76514 44.7435 3
      vertex 6.24458 44.098 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.66336 44.3448 3
      vertex 6.24458 44.098 3
      vertex 5.71042 44.5188 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.53415 44.2477 3
      vertex 5.76514 44.7435 3
      vertex 6.40559 44.1583 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.71042 44.5188 3
      vertex 6.24458 44.098 3
      vertex 5.76514 44.7435 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.62395 44.2213 3
      vertex 6.24458 44.098 3
      vertex 5.66336 44.3448 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.58624 44.1264 3
      vertex 6.24458 44.098 3
      vertex 5.62395 44.2213 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.54431 44.0378 3
      vertex 6.24458 44.098 3
      vertex 5.58624 44.1264 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.49815 43.9555 3
      vertex 6.24458 44.098 3
      vertex 5.54431 44.0378 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.38843 43.8131 3
      vertex 6.35614 43.4215 3
      vertex 5.44659 43.8804 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.35614 43.4215 3
      vertex 5.38843 43.8131 3
      vertex 6.31816 43.2306 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.32368 43.7538 3
      vertex 6.31816 43.2306 3
      vertex 5.38843 43.8131 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.25169 43.7025 3
      vertex 6.31816 43.2306 3
      vertex 5.32368 43.7538 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 42.6207 3
      vertex 5.89384 40.7856 3
      vertex 6.18736 40.8699 3
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 5.53967 40.7575 3
      vertex 6.08794 42.6207 3
      vertex 4.93207 42.5708 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.31816 43.2306 3
      vertex 5.25169 43.7025 3
      vertex 6.08794 42.6207 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.17178 43.6594 3
      vertex 6.08794 42.6207 3
      vertex 5.25169 43.7025 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 42.6207 3
      vertex 5.53967 40.7575 3
      vertex 5.89384 40.7856 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 42.6207 3
      vertex 5.17178 43.6594 3
      vertex 4.93207 42.5708 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 42.5708 3
      vertex 5.17178 43.6594 3
      vertex 5.08397 43.6245 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 42.5708 3
      vertex 5.08397 43.6245 3
      vertex 4.98772 43.5987 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.53967 40.7575 3
      vertex 4.93207 42.5708 3
      vertex 5.19183 40.7848 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.38383 41.7235 3
      vertex 5.19183 40.7848 3
      vertex 4.93207 42.5708 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.53217 42.2635 3
      vertex 4.93207 42.5708 3
      vertex 4.77582 42.5019 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.19183 40.7848 3
      vertex 4.38383 41.7235 3
      vertex 4.90466 40.8667 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.53217 42.2635 3
      vertex 4.77582 42.5019 3
      vertex 4.64252 42.3994 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 42.5708 3
      vertex 4.53217 42.2635 3
      vertex 4.44975 42.1017 3
    endloop
  endfacet
  facet normal -0 -0 1
    outer loop
      vertex 4.41653 41.4325 3
      vertex 4.90466 40.8667 3
      vertex 4.38383 41.7235 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 42.5708 3
      vertex 4.44975 42.1017 3
      vertex 4.40031 41.9217 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.90466 40.8667 3
      vertex 4.41653 41.4325 3
      vertex 4.67815 41.0032 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 42.5708 3
      vertex 4.40031 41.9217 3
      vertex 4.38383 41.7235 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.67815 41.0032 3
      vertex 4.41653 41.4325 3
      vertex 4.51463 41.1924 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.30115 39.2414 3
      vertex -5.07448 38.8296 3
      vertex -5.09967 38.9956 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.07448 38.8296 3
      vertex -5.28575 38.4332 3
      vertex -5.09796 38.6663 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.30115 39.2414 3
      vertex -5.09967 38.9956 3
      vertex -5.17522 39.1328 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.09796 38.6663 3
      vertex -5.28575 38.4332 3
      vertex -5.16838 38.5342 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.07448 38.8296 3
      vertex -5.30115 39.2414 3
      vertex -5.28575 38.4332 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.30115 39.2414 3
      vertex -5.45161 38.362 3
      vertex -5.28575 38.4332 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.47453 39.3198 3
      vertex -5.45161 38.362 3
      vertex -5.30115 39.2414 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.47453 39.3198 3
      vertex -5.66759 38.3193 3
      vertex -5.45161 38.362 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.69249 39.3669 3
      vertex -5.66759 38.3193 3
      vertex -5.47453 39.3198 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.69249 39.3669 3
      vertex -5.93367 38.3051 3
      vertex -5.66759 38.3193 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.95502 39.3826 3
      vertex -5.93367 38.3051 3
      vertex -5.69249 39.3669 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.20712 39.3672 3
      vertex -5.93367 38.3051 3
      vertex -5.95502 39.3826 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.42548 38.3639 3
      vertex -6.20712 39.3672 3
      vertex -6.41914 39.3209 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.20712 39.3672 3
      vertex -6.42548 38.3639 3
      vertex -5.93367 38.3051 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.59109 39.2437 3
      vertex -6.42548 38.3639 3
      vertex -6.41914 39.3209 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.81894 38.8343 3
      vertex -6.59109 39.2437 3
      vertex -6.71767 39.1366 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.59109 39.2437 3
      vertex -6.81894 38.8343 3
      vertex -6.42548 38.3639 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.81894 38.8343 3
      vertex -6.71767 39.1366 3
      vertex -6.79362 39.0001 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.42548 38.3639 3
      vertex -6.81894 38.8343 3
      vertex -6.72058 38.5403 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.42548 37.6501 3
      vertex 6.81894 37.1797 3
      vertex 6.72058 37.4737 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.81894 37.1797 3
      vertex 6.59109 36.7702 3
      vertex 6.79362 37.0139 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.79362 37.0139 3
      vertex 6.59109 36.7702 3
      vertex 6.71767 36.8774 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.81894 37.1797 3
      vertex 6.42548 37.6501 3
      vertex 6.59109 36.7702 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.42548 37.6501 3
      vertex 6.41914 36.6931 3
      vertex 6.59109 36.7702 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.42548 37.6501 3
      vertex 6.20712 36.6468 3
      vertex 6.41914 36.6931 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.93367 37.7089 3
      vertex 6.20712 36.6468 3
      vertex 6.42548 37.6501 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.20712 36.6468 3
      vertex 5.93367 37.7089 3
      vertex 5.95502 36.6314 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.93367 37.7089 3
      vertex 5.69249 36.6471 3
      vertex 5.95502 36.6314 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.66759 37.6947 3
      vertex 5.69249 36.6471 3
      vertex 5.93367 37.7089 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.66759 37.6947 3
      vertex 5.47453 36.6942 3
      vertex 5.69249 36.6471 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.45161 37.652 3
      vertex 5.47453 36.6942 3
      vertex 5.66759 37.6947 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.45161 37.652 3
      vertex 5.30115 36.7726 3
      vertex 5.47453 36.6942 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.28575 37.5808 3
      vertex 5.30115 36.7726 3
      vertex 5.45161 37.652 3
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.07448 37.1844 3
      vertex 5.30115 36.7726 3
      vertex 5.28575 37.5808 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.09796 37.3476 3
      vertex 5.28575 37.5808 3
      vertex 5.16838 37.4798 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.30115 36.7726 3
      vertex 5.07448 37.1844 3
      vertex 5.17522 36.8811 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.28575 37.5808 3
      vertex 5.09796 37.3476 3
      vertex 5.07448 37.1844 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.17522 36.8811 3
      vertex 5.07448 37.1844 3
      vertex 5.09967 37.0184 3
    endloop
  endfacet
  facet normal -0.454015 0.890994 0
    outer loop
      vertex -7.61803 76.9161 0
      vertex -8.17557 76.632 3
      vertex -7.61803 76.9161 3
    endloop
  endfacet
  facet normal -0.454015 0.890994 0
    outer loop
      vertex -8.17557 76.632 3
      vertex -7.61803 76.9161 0
      vertex -8.17557 76.632 0
    endloop
  endfacet
  facet normal 0.156456 0.987685 -0
    outer loop
      vertex 7.61803 76.9161 0
      vertex 7 77.014 3
      vertex 7.61803 76.9161 3
    endloop
  endfacet
  facet normal 0.156456 0.987685 0
    outer loop
      vertex 7 77.014 3
      vertex 7.61803 76.9161 0
      vertex 7 77.014 0
    endloop
  endfacet
  facet normal -0.707106 -0.707108 0
    outer loop
      vertex -8.17557 -0.618025 0
      vertex -8.61803 -0.175566 3
      vertex -8.61803 -0.175566 0
    endloop
  endfacet
  facet normal -0.707106 -0.707108 0
    outer loop
      vertex -8.61803 -0.175566 3
      vertex -8.17557 -0.618025 0
      vertex -8.17557 -0.618025 3
    endloop
  endfacet
  facet normal 0.987686 0.156448 0
    outer loop
      vertex 9 75.014 3
      vertex 8.90211 75.632 0
      vertex 8.90211 75.632 3
    endloop
  endfacet
  facet normal 0.987686 0.156448 0
    outer loop
      vertex 8.90211 75.632 0
      vertex 9 75.014 3
      vertex 9 75.014 0
    endloop
  endfacet
  facet normal 0.707139 0.707075 0
    outer loop
      vertex 8.61803 76.1895 3
      vertex 8.17557 76.632 0
      vertex 8.17557 76.632 3
    endloop
  endfacet
  facet normal 0.707139 0.707075 0
    outer loop
      vertex 8.17557 76.632 0
      vertex 8.61803 76.1895 3
      vertex 8.61803 76.1895 0
    endloop
  endfacet
  facet normal -0.891007 -0.453989 0
    outer loop
      vertex -8.61803 -0.175566 0
      vertex -8.90211 0.381974 3
      vertex -8.90211 0.381974 0
    endloop
  endfacet
  facet normal -0.891007 -0.453989 0
    outer loop
      vertex -8.90211 0.381974 3
      vertex -8.61803 -0.175566 0
      vertex -8.61803 -0.175566 3
    endloop
  endfacet
  facet normal 0.987687 -0.156441 0
    outer loop
      vertex 8.90211 0.381974 3
      vertex 9 1 0
      vertex 9 1 3
    endloop
  endfacet
  facet normal 0.987687 -0.156441 0
    outer loop
      vertex 9 1 0
      vertex 8.90211 0.381974 3
      vertex 8.90211 0.381974 0
    endloop
  endfacet
  facet normal 0.890994 0.454015 0
    outer loop
      vertex 8.90211 75.632 3
      vertex 8.61803 76.1895 0
      vertex 8.61803 76.1895 3
    endloop
  endfacet
  facet normal 0.890994 0.454015 0
    outer loop
      vertex 8.61803 76.1895 0
      vertex 8.90211 75.632 3
      vertex 8.90211 75.632 0
    endloop
  endfacet
  facet normal 0.454 -0.891002 0
    outer loop
      vertex 7.61803 -0.902113 0
      vertex 8.17557 -0.618025 3
      vertex 7.61803 -0.902113 3
    endloop
  endfacet
  facet normal 0.454 -0.891002 0
    outer loop
      vertex 8.17557 -0.618025 3
      vertex 7.61803 -0.902113 0
      vertex 8.17557 -0.618025 0
    endloop
  endfacet
  facet normal 0.891007 -0.453989 0
    outer loop
      vertex 8.61803 -0.175566 3
      vertex 8.90211 0.381974 0
      vertex 8.90211 0.381974 3
    endloop
  endfacet
  facet normal 0.891007 -0.453989 0
    outer loop
      vertex 8.90211 0.381974 0
      vertex 8.61803 -0.175566 3
      vertex 8.61803 -0.175566 0
    endloop
  endfacet
  facet normal -0.890994 0.454015 0
    outer loop
      vertex -8.90211 75.632 0
      vertex -8.61803 76.1895 3
      vertex -8.61803 76.1895 0
    endloop
  endfacet
  facet normal -0.890994 0.454015 0
    outer loop
      vertex -8.61803 76.1895 3
      vertex -8.90211 75.632 0
      vertex -8.90211 75.632 3
    endloop
  endfacet
  facet normal 0.454015 0.890994 -0
    outer loop
      vertex 8.17557 76.632 0
      vertex 7.61803 76.9161 3
      vertex 8.17557 76.632 3
    endloop
  endfacet
  facet normal 0.454015 0.890994 0
    outer loop
      vertex 7.61803 76.9161 3
      vertex 8.17557 76.632 0
      vertex 7.61803 76.9161 0
    endloop
  endfacet
  facet normal 0.707106 -0.707108 0
    outer loop
      vertex 8.17557 -0.618025 3
      vertex 8.61803 -0.175566 0
      vertex 8.61803 -0.175566 3
    endloop
  endfacet
  facet normal 0.707106 -0.707108 0
    outer loop
      vertex 8.61803 -0.175566 0
      vertex 8.17557 -0.618025 3
      vertex 8.17557 -0.618025 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.705 40.04 2.4
      vertex -4.68764 39.3731 2.4
      vertex -3.705 39.3731 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.705 40.04 2.4
      vertex -5.10536 39.3826 2.4
      vertex -4.68764 39.3731 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.30115 39.2414 2.4
      vertex -5.10536 39.3731 2.4
      vertex -5.10536 39.3826 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.10536 39.3731 2.4
      vertex -5.30115 39.2414 2.4
      vertex -5.17522 39.1328 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.10536 39.3826 2.4
      vertex -5.47453 39.3198 2.4
      vertex -5.30115 39.2414 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.64093 40.04 2.4
      vertex -5.10536 39.3826 2.4
      vertex -3.705 40.04 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -5.69249 39.3669 2.4
      vertex -5.10536 39.3826 2.4
      vertex -6.64093 40.04 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.10536 39.3826 2.4
      vertex -5.69249 39.3669 2.4
      vertex -5.47453 39.3198 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.69249 39.3669 2.4
      vertex -6.64093 40.04 2.4
      vertex -5.95502 39.3826 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.95502 39.3826 2.4
      vertex -6.64093 40.04 2.4
      vertex -6.20712 39.3672 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.20712 39.3672 2.4
      vertex -6.64093 40.04 2.4
      vertex -6.41914 39.3209 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.81421 39.3778 2.4
      vertex -6.41914 39.3209 2.4
      vertex -6.64093 40.04 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.41914 39.3209 2.4
      vertex -6.81421 39.3778 2.4
      vertex -6.59109 39.2437 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.81421 39.3731 2.4
      vertex -6.59109 39.2437 2.4
      vertex -6.81421 39.3778 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.59109 39.2437 2.4
      vertex -6.81421 39.3731 2.4
      vertex -6.71767 39.1366 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.86852 40.0421 2.4
      vertex -6.81421 39.3778 2.4
      vertex -6.64093 40.04 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.86852 40.0421 2.4
      vertex -6.87645 39.379 2.4
      vertex -6.81421 39.3778 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.86852 40.0421 2.4
      vertex -6.95239 39.3826 2.4
      vertex -6.87645 39.379 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.86852 40.0421 2.4
      vertex -7.04207 39.3885 2.4
      vertex -6.95239 39.3826 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.06393 40.0485 2.4
      vertex -7.04207 39.3885 2.4
      vertex -6.86852 40.0421 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.06393 40.0485 2.4
      vertex -7.12697 39.3958 2.4
      vertex -7.04207 39.3885 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.06393 40.0485 2.4
      vertex -7.18867 39.4033 2.4
      vertex -7.12697 39.3958 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22717 39.411 2.4
      vertex -7.06393 40.0485 2.4
      vertex -7.22717 40.059 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.06393 40.0485 2.4
      vertex -7.22717 39.411 2.4
      vertex -7.18867 39.4033 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.09796 38.6663 2.4
      vertex -4.61168 38.5519 2.4
      vertex -4.66653 38.9079 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.16838 38.5342 2.4
      vertex -4.61168 38.5519 2.4
      vertex -5.09796 38.6663 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.09967 38.9956 2.4
      vertex -4.66653 38.9079 2.4
      vertex -4.83109 39.1816 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.61168 38.5519 2.4
      vertex -5.16838 38.5342 2.4
      vertex -4.65005 38.2717 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.66653 38.9079 2.4
      vertex -5.07448 38.8296 2.4
      vertex -5.09796 38.6663 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.66653 38.9079 2.4
      vertex -5.09967 38.9956 2.4
      vertex -5.07448 38.8296 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.17522 39.1328 2.4
      vertex -4.83109 39.1816 2.4
      vertex -5.10536 39.3731 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.83109 39.1816 2.4
      vertex -5.17522 39.1328 2.4
      vertex -5.09967 38.9956 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.65005 38.2717 2.4
      vertex -5.16838 38.5342 2.4
      vertex -4.76517 38.0387 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.28575 38.4332 2.4
      vertex -4.76517 38.0387 2.4
      vertex -5.16838 38.5342 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76517 38.0387 2.4
      vertex -5.28575 38.4332 2.4
      vertex -4.95703 37.8529 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.45161 38.362 2.4
      vertex -4.95703 37.8529 2.4
      vertex -5.28575 38.4332 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.95703 37.8529 2.4
      vertex -5.45161 38.362 2.4
      vertex -5.21901 37.7178 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.45161 38.362 2.4
      vertex -5.54456 37.6367 2.4
      vertex -5.21901 37.7178 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.66759 38.3193 2.4
      vertex -5.54456 37.6367 2.4
      vertex -5.45161 38.362 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.93367 37.6096 2.4
      vertex -5.66759 38.3193 2.4
      vertex -5.93367 38.3051 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.66759 38.3193 2.4
      vertex -5.93367 37.6096 2.4
      vertex -5.54456 37.6367 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.93367 38.3051 2.4
      vertex -6.32619 37.638 2.4
      vertex -5.93367 37.6096 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.42548 38.3639 2.4
      vertex -6.32619 37.638 2.4
      vertex -5.93367 38.3051 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.42548 38.3639 2.4
      vertex -6.6557 37.7231 2.4
      vertex -6.32619 37.638 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.9222 37.8648 2.4
      vertex -6.42548 38.3639 2.4
      vertex -6.72058 38.5403 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.27464 38.5946 2.4
      vertex -6.72058 38.5403 2.4
      vertex -6.81894 38.8343 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.42548 38.3639 2.4
      vertex -6.9222 37.8648 2.4
      vertex -6.6557 37.7231 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.95134 39.2916 2.4
      vertex -6.71767 39.1366 2.4
      vertex -6.81421 39.3731 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.71767 39.1366 2.4
      vertex -6.95134 39.2916 2.4
      vertex -6.79362 39.0001 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.06526 39.1895 2.4
      vertex -6.79362 39.0001 2.4
      vertex -6.95134 39.2916 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.15599 39.0669 2.4
      vertex -6.79362 39.0001 2.4
      vertex -7.06526 39.1895 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.79362 39.0001 2.4
      vertex -7.15599 39.0669 2.4
      vertex -6.81894 38.8343 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.72058 38.5403 2.4
      vertex -7.27464 38.5946 2.4
      vertex -7.23547 38.3025 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.81894 38.8343 2.4
      vertex -7.15599 39.0669 2.4
      vertex -7.22191 38.9258 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.81894 38.8343 2.4
      vertex -7.22191 38.9258 2.4
      vertex -7.26146 38.7684 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.72058 38.5403 2.4
      vertex -7.23547 38.3025 2.4
      vertex -7.118 38.0593 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.81894 38.8343 2.4
      vertex -7.26146 38.7684 2.4
      vertex -7.27464 38.5946 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.72058 38.5403 2.4
      vertex -7.118 38.0593 2.4
      vertex -6.9222 37.8648 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.83318 44.5918 2.4
      vertex -4.41653 44.8686 2.4
      vertex -4.38383 44.5776 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.02937 45.4979 2.4
      vertex -4.51463 45.1087 2.4
      vertex -4.41653 44.8686 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.90466 45.4344 2.4
      vertex -4.27463 45.8236 2.4
      vertex -4.61139 46.0596 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.02937 45.4979 2.4
      vertex -4.67815 45.2979 2.4
      vertex -4.51463 45.1087 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.27463 45.8236 2.4
      vertex -4.90466 45.4344 2.4
      vertex -4.67815 45.2979 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.03307 46.2013 2.4
      vertex -4.90466 45.4344 2.4
      vertex -4.61139 46.0596 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.03307 46.2013 2.4
      vertex -5.19183 45.5162 2.4
      vertex -4.90466 45.4344 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 46.2485 2.4
      vertex -5.19183 45.5162 2.4
      vertex -5.03307 46.2013 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 46.2485 2.4
      vertex -5.53967 45.5435 2.4
      vertex -5.19183 45.5162 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 46.2485 2.4
      vertex -5.89384 45.5154 2.4
      vertex -5.53967 45.5435 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.04665 46.1996 2.4
      vertex -5.89384 45.5154 2.4
      vertex -5.53967 46.2485 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.04665 46.1996 2.4
      vertex -6.18736 45.4312 2.4
      vertex -5.89384 45.5154 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.47267 46.0528 2.4
      vertex -6.18736 45.4312 2.4
      vertex -6.04665 46.1996 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.81775 45.8082 2.4
      vertex -6.18736 45.4312 2.4
      vertex -6.47267 46.0528 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.18736 45.4312 2.4
      vertex -6.81775 45.8082 2.4
      vertex -6.42023 45.2908 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.07158 45.4739 2.4
      vertex -6.42023 45.2908 2.4
      vertex -6.81775 45.8082 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22388 45.0582 2.4
      vertex -6.589 45.0973 2.4
      vertex -7.07158 45.4739 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.42023 45.2908 2.4
      vertex -7.07158 45.4739 2.4
      vertex -6.589 45.0973 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.41653 44.8686 2.4
      vertex -3.83318 44.5918 2.4
      vertex -3.88223 45.0873 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.40031 44.3794 2.4
      vertex -3.83318 44.5918 2.4
      vertex -4.38383 44.5776 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.41653 44.8686 2.4
      vertex -3.88223 45.0873 2.4
      vertex -4.02937 45.4979 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.83318 44.5918 2.4
      vertex -4.40031 44.3794 2.4
      vertex -3.85942 44.2237 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.44975 44.1994 2.4
      vertex -3.85942 44.2237 2.4
      vertex -4.40031 44.3794 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.67815 45.2979 2.4
      vertex -4.02937 45.4979 2.4
      vertex -4.27463 45.8236 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.85942 44.2237 2.4
      vertex -4.44975 44.1994 2.4
      vertex -3.93814 43.904 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.53217 44.0376 2.4
      vertex -3.93814 43.904 2.4
      vertex -4.44975 44.1994 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.93814 43.904 2.4
      vertex -4.53217 44.0376 2.4
      vertex -4.06935 43.6329 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.64252 43.9016 2.4
      vertex -4.06935 43.6329 2.4
      vertex -4.53217 44.0376 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.06935 43.6329 2.4
      vertex -4.64252 43.9016 2.4
      vertex -4.25145 43.4106 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.77582 43.7992 2.4
      vertex -4.25145 43.4106 2.4
      vertex -4.64252 43.9016 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.25145 43.4106 2.4
      vertex -4.77582 43.7992 2.4
      vertex -4.48285 43.2374 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.93207 43.7303 2.4
      vertex -4.48285 43.2374 2.4
      vertex -4.77582 43.7992 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.48285 43.2374 2.4
      vertex -4.93207 43.7303 2.4
      vertex -4.76358 43.1131 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.61339 43.2222 2.4
      vertex -6.08794 43.6804 2.4
      vertex -6.44131 43.8879 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.08794 43.6804 2.4
      vertex -6.61339 43.2222 2.4
      vertex -6.31816 43.0704 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.0385 43.6483 2.4
      vertex -6.44131 43.8879 2.4
      vertex -6.65335 44.1815 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.2484 44.2233 2.4
      vertex -6.65335 44.1815 2.4
      vertex -6.72401 44.5609 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.44131 43.8879 2.4
      vertex -6.8535 43.4148 2.4
      vertex -6.61339 43.2222 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.589 45.0973 2.4
      vertex -7.22388 45.0582 2.4
      vertex -6.69026 44.854 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -7.2484 44.2233 2.4
      vertex -6.72401 44.5609 2.4
      vertex -7.27464 44.5609 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.27464 44.5609 2.4
      vertex -6.69026 44.854 2.4
      vertex -7.22388 45.0582 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.65335 44.1815 2.4
      vertex -7.2484 44.2233 2.4
      vertex -7.16969 43.9191 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.69026 44.854 2.4
      vertex -7.27464 44.5609 2.4
      vertex -6.72401 44.5609 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.65335 44.1815 2.4
      vertex -7.16969 43.9191 2.4
      vertex -7.0385 43.6483 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.44131 43.8879 2.4
      vertex -7.0385 43.6483 2.4
      vertex -6.8535 43.4148 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.63857 32.4938 2.4
      vertex -6.24458 31.916 2.4
      vertex -6.35614 32.5925 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.24458 31.916 2.4
      vertex -6.63857 32.4938 2.4
      vertex -6.40559 31.8556 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.86879 32.3372 2.4
      vertex -6.40559 31.8556 2.4
      vertex -6.63857 32.4938 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.40559 31.8556 2.4
      vertex -6.86879 32.3372 2.4
      vertex -6.53415 31.7662 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.04678 32.1225 2.4
      vertex -6.53415 31.7662 2.4
      vertex -6.86879 32.3372 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.53415 31.7662 2.4
      vertex -7.04678 32.1225 2.4
      vertex -6.63029 31.6478 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.17337 31.848 2.4
      vertex -6.63029 31.6478 2.4
      vertex -7.04678 32.1225 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.63029 31.6478 2.4
      vertex -7.17337 31.848 2.4
      vertex -6.69687 31.4978 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.24933 31.5117 2.4
      vertex -6.69687 31.4978 2.4
      vertex -7.17337 31.848 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -7.24576 30.6817 2.4
      vertex -6.75014 31.0948 2.4
      vertex -7.27464 31.1138 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.69687 31.4978 2.4
      vertex -7.24933 31.5117 2.4
      vertex -6.73682 31.3134 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -7.15913 30.3253 2.4
      vertex -6.75014 31.0948 2.4
      vertex -7.24576 30.6817 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.27464 31.1138 2.4
      vertex -6.73682 31.3134 2.4
      vertex -7.24933 31.5117 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -7.01477 30.0446 2.4
      vertex -6.75014 31.0948 2.4
      vertex -7.15913 30.3253 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.73682 31.3134 2.4
      vertex -7.27464 31.1138 2.4
      vertex -6.75014 31.0948 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.75014 31.0948 2.4
      vertex -7.01477 30.0446 2.4
      vertex -6.81578 29.8422 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.85994 31.5034 2.4
      vertex -4.37354 31.4719 2.4
      vertex -4.32922 31.1185 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.72795 31.7546 2.4
      vertex -4.25829 32.2844 2.4
      vertex -4.4897 32.3979 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.07408 32.0952 2.4
      vertex -4.50644 31.6839 2.4
      vertex -4.37354 31.4719 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.25829 32.2844 2.4
      vertex -4.72795 31.7546 2.4
      vertex -4.50644 31.6839 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76831 32.4358 2.4
      vertex -4.72795 31.7546 2.4
      vertex -4.4897 32.3979 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.76831 32.4358 2.4
      vertex -4.80971 31.7471 2.4
      vertex -4.72795 31.7546 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.88249 32.4306 2.4
      vertex -4.80971 31.7471 2.4
      vertex -4.76831 32.4358 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.98772 32.4152 2.4
      vertex -4.80971 31.7471 2.4
      vertex -4.88249 32.4306 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.08397 32.3895 2.4
      vertex -4.80971 31.7471 2.4
      vertex -4.98772 32.4152 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.80971 31.7471 2.4
      vertex -5.08397 32.3895 2.4
      vertex -4.88092 31.7246 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.17178 32.3546 2.4
      vertex -4.88092 31.7246 2.4
      vertex -5.08397 32.3895 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.25169 32.3115 2.4
      vertex -4.88092 31.7246 2.4
      vertex -5.17178 32.3546 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.32368 32.2602 2.4
      vertex -4.88092 31.7246 2.4
      vertex -5.25169 32.3115 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.88092 31.7246 2.4
      vertex -5.32368 32.2602 2.4
      vertex -4.94159 31.687 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.38843 32.2009 2.4
      vertex -4.94159 31.687 2.4
      vertex -5.32368 32.2602 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.44659 32.1336 2.4
      vertex -4.94159 31.687 2.4
      vertex -5.38843 32.2009 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.49815 32.0585 2.4
      vertex -4.94159 31.687 2.4
      vertex -5.44659 32.1336 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.94159 31.687 2.4
      vertex -5.49815 32.0585 2.4
      vertex -4.9942 31.6347 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.54431 31.9762 2.4
      vertex -4.9942 31.6347 2.4
      vertex -5.49815 32.0585 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.04128 31.5678 2.4
      vertex -5.62395 31.7926 2.4
      vertex -5.08281 31.4865 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.58624 31.8876 2.4
      vertex -4.9942 31.6347 2.4
      vertex -5.54431 31.9762 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.71042 31.4951 2.4
      vertex -5.12486 31.3675 2.4
      vertex -5.66336 31.6692 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.9942 31.6347 2.4
      vertex -5.58624 31.8876 2.4
      vertex -5.04128 31.5678 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.17352 31.1879 2.4
      vertex -5.76514 31.2704 2.4
      vertex -5.22876 30.9477 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.62395 31.7926 2.4
      vertex -5.04128 31.5678 2.4
      vertex -5.58624 31.8876 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.8208 31.0121 2.4
      vertex -5.22876 30.9477 2.4
      vertex -5.76514 31.2704 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.66336 31.6692 2.4
      vertex -5.08281 31.4865 2.4
      vertex -5.62395 31.7926 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.08281 31.4865 2.4
      vertex -5.66336 31.6692 2.4
      vertex -5.12486 31.3675 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.22876 30.9477 2.4
      vertex -5.8208 31.0121 2.4
      vertex -5.29509 30.6569 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.12486 31.3675 2.4
      vertex -5.71042 31.4951 2.4
      vertex -5.17352 31.1879 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.87065 30.8163 2.4
      vertex -5.29509 30.6569 2.4
      vertex -5.8208 31.0121 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.76514 31.2704 2.4
      vertex -5.17352 31.1879 2.4
      vertex -5.71042 31.4951 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.91469 30.683 2.4
      vertex -5.29509 30.6569 2.4
      vertex -5.87065 30.8163 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.29509 30.6569 2.4
      vertex -5.91469 30.683 2.4
      vertex -5.35799 30.4271 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -5.95926 30.5886 2.4
      vertex -5.35799 30.4271 2.4
      vertex -5.91469 30.683 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.35799 30.4271 2.4
      vertex -5.95926 30.5886 2.4
      vertex -5.41745 30.2582 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.01067 30.5095 2.4
      vertex -5.41745 30.2582 2.4
      vertex -5.95926 30.5886 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.41745 30.2582 2.4
      vertex -6.01067 30.5095 2.4
      vertex -5.47836 30.1294 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.06895 30.4457 2.4
      vertex -5.47836 30.1294 2.4
      vertex -6.01067 30.5095 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.47836 30.1294 2.4
      vertex -6.06895 30.4457 2.4
      vertex -5.54561 30.0198 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.54561 30.0198 2.4
      vertex -6.06895 30.4457 2.4
      vertex -5.61919 29.9295 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.61919 29.9295 2.4
      vertex -6.06895 30.4457 2.4
      vertex -5.70094 29.8551 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.1362 30.3989 2.4
      vertex -5.70094 29.8551 2.4
      vertex -6.06895 30.4457 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.70094 29.8551 2.4
      vertex -6.1362 30.3989 2.4
      vertex -5.79272 29.7934 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.79272 29.7934 2.4
      vertex -6.1362 30.3989 2.4
      vertex -5.89453 29.7443 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.89453 29.7443 2.4
      vertex -6.1362 30.3989 2.4
      vertex -6.00673 29.7087 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.21451 30.3708 2.4
      vertex -6.00673 29.7087 2.4
      vertex -6.1362 30.3989 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.00673 29.7087 2.4
      vertex -6.21451 30.3708 2.4
      vertex -6.12973 29.6874 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.21451 30.3708 2.4
      vertex -6.26357 29.6802 2.4
      vertex -6.12973 29.6874 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.30391 30.3614 2.4
      vertex -6.26357 29.6802 2.4
      vertex -6.21451 30.3708 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.56538 29.7207 2.4
      vertex -6.30391 30.3614 2.4
      vertex -6.55182 30.4429 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.30391 30.3614 2.4
      vertex -6.56538 29.7207 2.4
      vertex -6.26357 29.6802 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.81578 29.8422 2.4
      vertex -6.55182 30.4429 2.4
      vertex -6.70055 30.6874 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.55182 30.4429 2.4
      vertex -6.81578 29.8422 2.4
      vertex -6.56538 29.7207 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.81578 29.8422 2.4
      vertex -6.70055 30.6874 2.4
      vertex -6.75014 31.0948 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.32922 31.1185 2.4
      vertex -3.83318 31.1043 2.4
      vertex -3.85994 31.5034 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.34137 30.9346 2.4
      vertex -3.83318 31.1043 2.4
      vertex -4.32922 31.1185 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.37354 31.4719 2.4
      vertex -3.85994 31.5034 2.4
      vertex -3.94025 31.8337 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.83318 31.1043 2.4
      vertex -4.34137 30.9346 2.4
      vertex -3.8548 30.7242 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.37354 31.4719 2.4
      vertex -3.94025 31.8337 2.4
      vertex -4.07408 32.0952 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.37776 30.7815 2.4
      vertex -3.8548 30.7242 2.4
      vertex -4.34137 30.9346 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.50644 31.6839 2.4
      vertex -4.07408 32.0952 2.4
      vertex -4.25829 32.2844 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.8548 30.7242 2.4
      vertex -4.37776 30.7815 2.4
      vertex -3.91968 30.4129 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.43843 30.6593 2.4
      vertex -3.91968 30.4129 2.4
      vertex -4.37776 30.7815 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.91968 30.4129 2.4
      vertex -4.43843 30.6593 2.4
      vertex -4.02782 30.1704 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.52307 30.5645 2.4
      vertex -4.02782 30.1704 2.4
      vertex -4.43843 30.6593 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.02782 30.1704 2.4
      vertex -4.52307 30.5645 2.4
      vertex -4.18576 29.987 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.63145 30.4937 2.4
      vertex -4.18576 29.987 2.4
      vertex -4.52307 30.5645 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.18576 29.987 2.4
      vertex -4.63145 30.4937 2.4
      vertex -4.40016 29.8528 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.76358 30.4469 2.4
      vertex -4.40016 29.8528 2.4
      vertex -4.63145 30.4937 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.40016 29.8528 2.4
      vertex -4.76358 30.4469 2.4
      vertex -4.67101 29.7681 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.22717 37.1545 2.4
      vertex -3.88301 36.4543 2.4
      vertex -3.88301 37.1545 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.88301 36.4543 2.4
      vertex -7.22717 37.1545 2.4
      vertex -7.22717 36.4543 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.83318 34.3047 2.4
      vertex -4.41653 34.5815 2.4
      vertex -4.38383 34.2905 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.02937 35.2109 2.4
      vertex -4.51463 34.8216 2.4
      vertex -4.41653 34.5815 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.90466 35.1473 2.4
      vertex -4.27463 35.5366 2.4
      vertex -4.61139 35.7726 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.02937 35.2109 2.4
      vertex -4.67815 35.0108 2.4
      vertex -4.51463 34.8216 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.27463 35.5366 2.4
      vertex -4.90466 35.1473 2.4
      vertex -4.67815 35.0108 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.03307 35.9142 2.4
      vertex -4.90466 35.1473 2.4
      vertex -4.61139 35.7726 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.03307 35.9142 2.4
      vertex -5.19183 35.2292 2.4
      vertex -4.90466 35.1473 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 35.9614 2.4
      vertex -5.19183 35.2292 2.4
      vertex -5.03307 35.9142 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 35.9614 2.4
      vertex -5.53967 35.2565 2.4
      vertex -5.19183 35.2292 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.53967 35.9614 2.4
      vertex -5.89384 35.2284 2.4
      vertex -5.53967 35.2565 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.04665 35.9125 2.4
      vertex -5.89384 35.2284 2.4
      vertex -5.53967 35.9614 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.04665 35.9125 2.4
      vertex -6.18736 35.1441 2.4
      vertex -5.89384 35.2284 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.47267 35.7657 2.4
      vertex -6.18736 35.1441 2.4
      vertex -6.04665 35.9125 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -6.81775 35.5211 2.4
      vertex -6.18736 35.1441 2.4
      vertex -6.47267 35.7657 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.18736 35.1441 2.4
      vertex -6.81775 35.5211 2.4
      vertex -6.42023 35.0037 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.07158 35.1868 2.4
      vertex -6.42023 35.0037 2.4
      vertex -6.81775 35.5211 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.22388 34.7711 2.4
      vertex -6.589 34.8102 2.4
      vertex -7.07158 35.1868 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.42023 35.0037 2.4
      vertex -7.07158 35.1868 2.4
      vertex -6.589 34.8102 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.41653 34.5815 2.4
      vertex -3.83318 34.3047 2.4
      vertex -3.88223 34.8002 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.40031 34.0923 2.4
      vertex -3.83318 34.3047 2.4
      vertex -4.38383 34.2905 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.41653 34.5815 2.4
      vertex -3.88223 34.8002 2.4
      vertex -4.02937 35.2109 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.83318 34.3047 2.4
      vertex -4.40031 34.0923 2.4
      vertex -3.85942 33.9366 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.44975 33.9123 2.4
      vertex -3.85942 33.9366 2.4
      vertex -4.40031 34.0923 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.67815 35.0108 2.4
      vertex -4.02937 35.2109 2.4
      vertex -4.27463 35.5366 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.85942 33.9366 2.4
      vertex -4.44975 33.9123 2.4
      vertex -3.93814 33.617 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.53217 33.7505 2.4
      vertex -3.93814 33.617 2.4
      vertex -4.44975 33.9123 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -3.93814 33.617 2.4
      vertex -4.53217 33.7505 2.4
      vertex -4.06935 33.3459 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.64252 33.6146 2.4
      vertex -4.06935 33.3459 2.4
      vertex -4.53217 33.7505 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.06935 33.3459 2.4
      vertex -4.64252 33.6146 2.4
      vertex -4.25145 33.1236 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.77582 33.5121 2.4
      vertex -4.25145 33.1236 2.4
      vertex -4.64252 33.6146 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.25145 33.1236 2.4
      vertex -4.77582 33.5121 2.4
      vertex -4.48285 32.9503 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -4.93207 33.4432 2.4
      vertex -4.48285 32.9503 2.4
      vertex -4.77582 33.5121 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.48285 32.9503 2.4
      vertex -4.93207 33.4432 2.4
      vertex -4.76358 32.826 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.61339 32.9351 2.4
      vertex -6.08794 33.3933 2.4
      vertex -6.44131 33.6009 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.08794 33.3933 2.4
      vertex -6.61339 32.9351 2.4
      vertex -6.31816 32.7834 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.0385 33.3613 2.4
      vertex -6.44131 33.6009 2.4
      vertex -6.65335 33.8944 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.2484 33.9362 2.4
      vertex -6.65335 33.8944 2.4
      vertex -6.72401 34.2739 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.44131 33.6009 2.4
      vertex -6.8535 33.1277 2.4
      vertex -6.61339 32.9351 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.589 34.8102 2.4
      vertex -7.22388 34.7711 2.4
      vertex -6.69026 34.567 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex -7.2484 33.9362 2.4
      vertex -6.72401 34.2739 2.4
      vertex -7.27464 34.2739 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.27464 34.2739 2.4
      vertex -6.69026 34.567 2.4
      vertex -7.22388 34.7711 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.65335 33.8944 2.4
      vertex -7.2484 33.9362 2.4
      vertex -7.16969 33.632 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.69026 34.567 2.4
      vertex -7.27464 34.2739 2.4
      vertex -6.72401 34.2739 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.65335 33.8944 2.4
      vertex -7.16969 33.632 2.4
      vertex -7.0385 33.3613 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.44131 33.6009 2.4
      vertex -7.0385 33.3613 2.4
      vertex -6.8535 33.1277 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -4.65913 42.9816 2.4
      vertex -5.86247 41.8732 2.4
      vertex -4.65913 42.2767 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -7.20107 41.9658 2.4
      vertex -5.86247 41.8732 2.4
      vertex -4.65913 42.9816 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.86247 41.8732 2.4
      vertex -7.20107 41.9658 2.4
      vertex -6.06551 41.8044 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.06551 41.8044 2.4
      vertex -7.20107 41.9658 2.4
      vertex -6.32974 41.7245 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -6.32974 41.7245 2.4
      vertex -7.20107 41.9658 2.4
      vertex -6.65518 41.6335 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.87196 41.4199 2.4
      vertex -4.65913 40.3423 2.4
      vertex -4.65913 41.0401 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.36246 41.3582 2.4
      vertex -5.87196 41.4199 2.4
      vertex -6.4297 41.5741 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.36246 41.3582 2.4
      vertex -6.4297 41.5741 2.4
      vertex -6.65518 41.6335 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.36246 41.3582 2.4
      vertex -6.65518 41.6335 2.4
      vertex -7.20107 41.9658 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.65782 41.4959 2.4
      vertex -7.20107 41.9658 2.4
      vertex -7.35112 42.0255 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -5.87196 41.4199 2.4
      vertex -7.36246 41.3582 2.4
      vertex -4.65913 40.3423 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.65782 41.4959 2.4
      vertex -7.35112 42.0255 2.4
      vertex -7.46899 42.0813 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.88567 41.6372 2.4
      vertex -7.46899 42.0813 2.4
      vertex -7.5547 42.1331 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.04601 41.7818 2.4
      vertex -7.5547 42.1331 2.4
      vertex -7.61774 42.185 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.20107 41.9658 2.4
      vertex -7.65782 41.4959 2.4
      vertex -7.36246 41.3582 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.04601 41.7818 2.4
      vertex -7.61774 42.185 2.4
      vertex -7.66759 42.2412 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.15149 41.9423 2.4
      vertex -7.66759 42.2412 2.4
      vertex -7.70422 42.3016 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.21478 42.131 2.4
      vertex -7.70422 42.3016 2.4
      vertex -7.72929 42.3695 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.23589 42.3479 2.4
      vertex -7.72929 42.3695 2.4
      vertex -7.74434 42.4482 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.46899 42.0813 2.4
      vertex -7.88567 41.6372 2.4
      vertex -7.65782 41.4959 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -8.23245 42.5011 2.4
      vertex -7.74434 42.4482 2.4
      vertex -7.74934 42.5378 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -8.22217 42.6411 2.4
      vertex -7.74934 42.5378 2.4
      vertex -7.74724 42.6098 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -8.22217 42.6411 2.4
      vertex -7.74724 42.6098 2.4
      vertex -7.74091 42.6865 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex -8.20505 42.768 2.4
      vertex -7.74091 42.6865 2.4
      vertex -7.73035 42.768 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.5547 42.1331 2.4
      vertex -8.04601 41.7818 2.4
      vertex -7.88567 41.6372 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.66759 42.2412 2.4
      vertex -8.15149 41.9423 2.4
      vertex -8.04601 41.7818 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.74091 42.6865 2.4
      vertex -8.20505 42.768 2.4
      vertex -8.22217 42.6411 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.74934 42.5378 2.4
      vertex -8.22217 42.6411 2.4
      vertex -8.23245 42.5011 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.74434 42.4482 2.4
      vertex -8.23245 42.5011 2.4
      vertex -8.23589 42.3479 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.72929 42.3695 2.4
      vertex -8.23589 42.3479 2.4
      vertex -8.21478 42.131 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -7.70422 42.3016 2.4
      vertex -8.21478 42.131 2.4
      vertex -8.15149 41.9423 2.4
    endloop
  endfacet
  facet normal 0.90046 0.434939 0
    outer loop
      vertex -7.118 38.0593 3
      vertex -7.23547 38.3025 2.4
      vertex -7.23547 38.3025 3
    endloop
  endfacet
  facet normal 0.90046 0.434939 0
    outer loop
      vertex -7.23547 38.3025 2.4
      vertex -7.118 38.0593 3
      vertex -7.118 38.0593 2.4
    endloop
  endfacet
  facet normal 0.704748 0.709458 -0
    outer loop
      vertex -6.9222 37.8648 2.4
      vertex -7.118 38.0593 3
      vertex -6.9222 37.8648 3
    endloop
  endfacet
  facet normal 0.704748 0.709458 0
    outer loop
      vertex -7.118 38.0593 3
      vertex -6.9222 37.8648 2.4
      vertex -7.118 38.0593 2.4
    endloop
  endfacet
  facet normal 0.46947 0.882948 -0
    outer loop
      vertex -6.6557 37.7231 2.4
      vertex -6.9222 37.8648 3
      vertex -6.6557 37.7231 3
    endloop
  endfacet
  facet normal 0.46947 0.882948 0
    outer loop
      vertex -6.9222 37.8648 3
      vertex -6.6557 37.7231 2.4
      vertex -6.9222 37.8648 2.4
    endloop
  endfacet
  facet normal 0.250058 0.968231 -0
    outer loop
      vertex -6.32619 37.638 2.4
      vertex -6.6557 37.7231 3
      vertex -6.32619 37.638 3
    endloop
  endfacet
  facet normal 0.250058 0.968231 0
    outer loop
      vertex -6.6557 37.7231 3
      vertex -6.32619 37.638 2.4
      vertex -6.6557 37.7231 2.4
    endloop
  endfacet
  facet normal 0.0721644 0.997393 -0
    outer loop
      vertex -5.93367 37.6096 2.4
      vertex -6.32619 37.638 3
      vertex -5.93367 37.6096 3
    endloop
  endfacet
  facet normal 0.0721644 0.997393 0
    outer loop
      vertex -6.32619 37.638 3
      vertex -5.93367 37.6096 2.4
      vertex -6.32619 37.638 2.4
    endloop
  endfacet
  facet normal -0.0694778 0.997583 0
    outer loop
      vertex -5.54456 37.6367 2.4
      vertex -5.93367 37.6096 3
      vertex -5.54456 37.6367 3
    endloop
  endfacet
  facet normal -0.0694778 0.997583 0
    outer loop
      vertex -5.93367 37.6096 3
      vertex -5.54456 37.6367 2.4
      vertex -5.93367 37.6096 2.4
    endloop
  endfacet
  facet normal -0.241729 0.970344 0
    outer loop
      vertex -5.21901 37.7178 2.4
      vertex -5.54456 37.6367 3
      vertex -5.21901 37.7178 3
    endloop
  endfacet
  facet normal -0.241729 0.970344 0
    outer loop
      vertex -5.54456 37.6367 3
      vertex -5.21901 37.7178 2.4
      vertex -5.54456 37.6367 2.4
    endloop
  endfacet
  facet normal -0.458334 0.88878 0
    outer loop
      vertex -4.95703 37.8529 2.4
      vertex -5.21901 37.7178 3
      vertex -4.95703 37.8529 3
    endloop
  endfacet
  facet normal -0.458334 0.88878 0
    outer loop
      vertex -5.21901 37.7178 3
      vertex -4.95703 37.8529 2.4
      vertex -5.21901 37.7178 2.4
    endloop
  endfacet
  facet normal -0.695671 0.718361 0
    outer loop
      vertex -4.76517 38.0387 2.4
      vertex -4.95703 37.8529 3
      vertex -4.76517 38.0387 3
    endloop
  endfacet
  facet normal -0.695671 0.718361 0
    outer loop
      vertex -4.95703 37.8529 3
      vertex -4.76517 38.0387 2.4
      vertex -4.95703 37.8529 2.4
    endloop
  endfacet
  facet normal -0.896541 0.442961 0
    outer loop
      vertex -4.76517 38.0387 2.4
      vertex -4.65005 38.2717 3
      vertex -4.65005 38.2717 2.4
    endloop
  endfacet
  facet normal -0.896541 0.442961 0
    outer loop
      vertex -4.65005 38.2717 3
      vertex -4.76517 38.0387 2.4
      vertex -4.76517 38.0387 3
    endloop
  endfacet
  facet normal -0.990754 0.135672 0
    outer loop
      vertex -4.65005 38.2717 2.4
      vertex -4.61168 38.5519 3
      vertex -4.61168 38.5519 2.4
    endloop
  endfacet
  facet normal -0.990754 0.135672 0
    outer loop
      vertex -4.61168 38.5519 3
      vertex -4.65005 38.2717 2.4
      vertex -4.65005 38.2717 3
    endloop
  endfacet
  facet normal -0.988338 -0.152276 0
    outer loop
      vertex -4.61168 38.5519 2.4
      vertex -4.66653 38.9079 3
      vertex -4.66653 38.9079 2.4
    endloop
  endfacet
  facet normal -0.988338 -0.152276 0
    outer loop
      vertex -4.66653 38.9079 3
      vertex -4.61168 38.5519 2.4
      vertex -4.61168 38.5519 3
    endloop
  endfacet
  facet normal -0.857023 -0.515278 0
    outer loop
      vertex -4.66653 38.9079 2.4
      vertex -4.83109 39.1816 3
      vertex -4.83109 39.1816 2.4
    endloop
  endfacet
  facet normal -0.857023 -0.515278 0
    outer loop
      vertex -4.83109 39.1816 3
      vertex -4.66653 38.9079 2.4
      vertex -4.66653 38.9079 3
    endloop
  endfacet
  facet normal -0.572481 -0.819918 0
    outer loop
      vertex -5.10536 39.3731 2.4
      vertex -4.83109 39.1816 3
      vertex -5.10536 39.3731 3
    endloop
  endfacet
  facet normal -0.572481 -0.819918 -0
    outer loop
      vertex -4.83109 39.1816 3
      vertex -5.10536 39.3731 2.4
      vertex -4.83109 39.1816 2.4
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -5.10536 39.3731 2.4
      vertex -5.10536 39.3826 3
      vertex -5.10536 39.3826 2.4
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -5.10536 39.3826 3
      vertex -5.10536 39.3731 2.4
      vertex -5.10536 39.3731 3
    endloop
  endfacet
  facet normal 0.0227366 0.999741 -0
    outer loop
      vertex -4.68764 39.3731 2.4
      vertex -5.10536 39.3826 3
      vertex -4.68764 39.3731 3
    endloop
  endfacet
  facet normal 0.0227366 0.999741 0
    outer loop
      vertex -5.10536 39.3826 3
      vertex -4.68764 39.3731 2.4
      vertex -5.10536 39.3826 2.4
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex -3.705 39.3731 2.4
      vertex -4.68764 39.3731 3
      vertex -3.705 39.3731 3
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -4.68764 39.3731 3
      vertex -3.705 39.3731 2.4
      vertex -4.68764 39.3731 2.4
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3.705 39.3731 2.4
      vertex -3.705 40.04 3
      vertex -3.705 40.04 2.4
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3.705 40.04 3
      vertex -3.705 39.3731 2.4
      vertex -3.705 39.3731 3
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -6.64093 40.04 2.4
      vertex -3.705 40.04 3
      vertex -6.64093 40.04 3
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex -3.705 40.04 3
      vertex -6.64093 40.04 2.4
      vertex -3.705 40.04 2.4
    endloop
  endfacet
  facet normal -0.00922673 -0.999957 0
    outer loop
      vertex -6.86852 40.0421 2.4
      vertex -6.64093 40.04 3
      vertex -6.86852 40.0421 3
    endloop
  endfacet
  facet normal -0.00922673 -0.999957 -0
    outer loop
      vertex -6.64093 40.04 3
      vertex -6.86852 40.0421 2.4
      vertex -6.64093 40.04 2.4
    endloop
  endfacet
  facet normal -0.0327341 -0.999464 0
    outer loop
      vertex -7.06393 40.0485 2.4
      vertex -6.86852 40.0421 3
      vertex -7.06393 40.0485 3
    endloop
  endfacet
  facet normal -0.0327341 -0.999464 -0
    outer loop
      vertex -6.86852 40.0421 3
      vertex -7.06393 40.0485 2.4
      vertex -6.86852 40.0421 2.4
    endloop
  endfacet
  facet normal -0.0641898 -0.997938 0
    outer loop
      vertex -7.22717 40.059 2.4
      vertex -7.06393 40.0485 3
      vertex -7.22717 40.059 3
    endloop
  endfacet
  facet normal -0.0641898 -0.997938 -0
    outer loop
      vertex -7.06393 40.0485 3
      vertex -7.22717 40.059 2.4
      vertex -7.06393 40.0485 2.4
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex -7.22717 39.411 3
      vertex -7.22717 40.059 2.4
      vertex -7.22717 40.059 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -7.22717 40.059 2.4
      vertex -7.22717 39.411 3
      vertex -7.22717 39.411 2.4
    endloop
  endfacet
  facet normal 0.196116 0.980581 -0
    outer loop
      vertex -7.18867 39.4033 2.4
      vertex -7.22717 39.411 3
      vertex -7.18867 39.4033 3
    endloop
  endfacet
  facet normal 0.196116 0.980581 0
    outer loop
      vertex -7.22717 39.411 3
      vertex -7.18867 39.4033 2.4
      vertex -7.22717 39.411 2.4
    endloop
  endfacet
  facet normal 0.120668 0.992693 -0
    outer loop
      vertex -7.12697 39.3958 2.4
      vertex -7.18867 39.4033 3
      vertex -7.12697 39.3958 3
    endloop
  endfacet
  facet normal 0.120668 0.992693 0
    outer loop
      vertex -7.18867 39.4033 3
      vertex -7.12697 39.3958 2.4
      vertex -7.18867 39.4033 2.4
    endloop
  endfacet
  facet normal 0.0856674 0.996324 -0
    outer loop
      vertex -7.04207 39.3885 2.4
      vertex -7.12697 39.3958 3
      vertex -7.04207 39.3885 3
    endloop
  endfacet
  facet normal 0.0856674 0.996324 0
    outer loop
      vertex -7.12697 39.3958 3
      vertex -7.04207 39.3885 2.4
      vertex -7.12697 39.3958 2.4
    endloop
  endfacet
  facet normal 0.0656476 0.997843 -0
    outer loop
      vertex -6.95239 39.3826 2.4
      vertex -7.04207 39.3885 3
      vertex -6.95239 39.3826 3
    endloop
  endfacet
  facet normal 0.0656476 0.997843 0
    outer loop
      vertex -7.04207 39.3885 3
      vertex -6.95239 39.3826 2.4
      vertex -7.04207 39.3885 2.4
    endloop
  endfacet
  facet normal 0.0473527 0.998878 -0
    outer loop
      vertex -6.87645 39.379 2.4
      vertex -6.95239 39.3826 3
      vertex -6.87645 39.379 3
    endloop
  endfacet
  facet normal 0.0473527 0.998878 0
    outer loop
      vertex -6.95239 39.3826 3
      vertex -6.87645 39.379 2.4
      vertex -6.95239 39.3826 2.4
    endloop
  endfacet
  facet normal 0.0192766 0.999814 -0
    outer loop
      vertex -6.81421 39.3778 2.4
      vertex -6.87645 39.379 3
      vertex -6.81421 39.3778 3
    endloop
  endfacet
  facet normal 0.0192766 0.999814 0
    outer loop
      vertex -6.87645 39.379 3
      vertex -6.81421 39.3778 2.4
      vertex -6.87645 39.379 2.4
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex -6.81421 39.3731 3
      vertex -6.81421 39.3778 2.4
      vertex -6.81421 39.3778 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -6.81421 39.3778 2.4
      vertex -6.81421 39.3731 3
      vertex -6.81421 39.3731 2.4
    endloop
  endfacet
  facet normal 0.510905 -0.859637 0
    outer loop
      vertex -6.95134 39.2916 2.4
      vertex -6.81421 39.3731 3
      vertex -6.95134 39.2916 3
    endloop
  endfacet
  facet normal 0.510905 -0.859637 0
    outer loop
      vertex -6.81421 39.3731 3
      vertex -6.95134 39.2916 2.4
      vertex -6.81421 39.3731 2.4
    endloop
  endfacet
  facet normal 0.667418 -0.744684 0
    outer loop
      vertex -7.06526 39.1895 2.4
      vertex -6.95134 39.2916 3
      vertex -7.06526 39.1895 3
    endloop
  endfacet
  facet normal 0.667418 -0.744684 0
    outer loop
      vertex -6.95134 39.2916 3
      vertex -7.06526 39.1895 2.4
      vertex -6.95134 39.2916 2.4
    endloop
  endfacet
  facet normal 0.803823 -0.594868 0
    outer loop
      vertex -7.15599 39.0669 3
      vertex -7.06526 39.1895 2.4
      vertex -7.06526 39.1895 3
    endloop
  endfacet
  facet normal 0.803823 -0.594868 0
    outer loop
      vertex -7.06526 39.1895 2.4
      vertex -7.15599 39.0669 3
      vertex -7.15599 39.0669 2.4
    endloop
  endfacet
  facet normal 0.906003 -0.423272 0
    outer loop
      vertex -7.22191 38.9258 3
      vertex -7.15599 39.0669 2.4
      vertex -7.15599 39.0669 3
    endloop
  endfacet
  facet normal 0.906003 -0.423272 0
    outer loop
      vertex -7.15599 39.0669 2.4
      vertex -7.22191 38.9258 3
      vertex -7.22191 38.9258 2.4
    endloop
  endfacet
  facet normal 0.969852 -0.243695 0
    outer loop
      vertex -7.26146 38.7684 3
      vertex -7.22191 38.9258 2.4
      vertex -7.22191 38.9258 3
    endloop
  endfacet
  facet normal 0.969852 -0.243695 0
    outer loop
      vertex -7.22191 38.9258 2.4
      vertex -7.26146 38.7684 3
      vertex -7.26146 38.7684 2.4
    endloop
  endfacet
  facet normal 0.997137 -0.0756172 0
    outer loop
      vertex -7.27464 38.5946 3
      vertex -7.26146 38.7684 2.4
      vertex -7.26146 38.7684 3
    endloop
  endfacet
  facet normal 0.997137 -0.0756172 0
    outer loop
      vertex -7.26146 38.7684 2.4
      vertex -7.27464 38.5946 3
      vertex -7.27464 38.5946 2.4
    endloop
  endfacet
  facet normal 0.991128 0.132908 0
    outer loop
      vertex -7.23547 38.3025 3
      vertex -7.27464 38.5946 2.4
      vertex -7.27464 38.5946 3
    endloop
  endfacet
  facet normal 0.991128 0.132908 0
    outer loop
      vertex -7.27464 38.5946 2.4
      vertex -7.23547 38.3025 3
      vertex -7.23547 38.3025 2.4
    endloop
  endfacet
  facet normal -0.87384 0.486214 0
    outer loop
      vertex -6.79362 39.0001 2.4
      vertex -6.71767 39.1366 3
      vertex -6.71767 39.1366 2.4
    endloop
  endfacet
  facet normal -0.87384 0.486214 0
    outer loop
      vertex -6.71767 39.1366 3
      vertex -6.79362 39.0001 2.4
      vertex -6.79362 39.0001 3
    endloop
  endfacet
  facet normal -0.645921 0.763405 0
    outer loop
      vertex -6.59109 39.2437 2.4
      vertex -6.71767 39.1366 3
      vertex -6.59109 39.2437 3
    endloop
  endfacet
  facet normal -0.645921 0.763405 0
    outer loop
      vertex -6.71767 39.1366 3
      vertex -6.59109 39.2437 2.4
      vertex -6.71767 39.1366 2.4
    endloop
  endfacet
  facet normal -0.409581 0.912274 0
    outer loop
      vertex -6.41914 39.3209 2.4
      vertex -6.59109 39.2437 3
      vertex -6.41914 39.3209 3
    endloop
  endfacet
  facet normal -0.409581 0.912274 0
    outer loop
      vertex -6.59109 39.2437 3
      vertex -6.41914 39.3209 2.4
      vertex -6.59109 39.2437 2.4
    endloop
  endfacet
  facet normal -0.213348 0.976976 0
    outer loop
      vertex -6.20712 39.3672 2.4
      vertex -6.41914 39.3209 3
      vertex -6.20712 39.3672 3
    endloop
  endfacet
  facet normal -0.213348 0.976976 0
    outer loop
      vertex -6.41914 39.3209 3
      vertex -6.20712 39.3672 2.4
      vertex -6.41914 39.3209 2.4
    endloop
  endfacet
  facet normal -0.0609732 0.998139 0
    outer loop
      vertex -5.95502 39.3826 2.4
      vertex -6.20712 39.3672 3
      vertex -5.95502 39.3826 3
    endloop
  endfacet
  facet normal -0.0609732 0.998139 0
    outer loop
      vertex -6.20712 39.3672 3
      vertex -5.95502 39.3826 2.4
      vertex -6.20712 39.3672 2.4
    endloop
  endfacet
  facet normal 0.059696 0.998217 -0
    outer loop
      vertex -5.69249 39.3669 2.4
      vertex -5.95502 39.3826 3
      vertex -5.69249 39.3669 3
    endloop
  endfacet
  facet normal 0.059696 0.998217 0
    outer loop
      vertex -5.95502 39.3826 3
      vertex -5.69249 39.3669 2.4
      vertex -5.95502 39.3826 2.4
    endloop
  endfacet
  facet normal 0.211219 0.977439 -0
    outer loop
      vertex -5.47453 39.3198 2.4
      vertex -5.69249 39.3669 3
      vertex -5.47453 39.3198 3
    endloop
  endfacet
  facet normal 0.211219 0.977439 0
    outer loop
      vertex -5.69249 39.3669 3
      vertex -5.47453 39.3198 2.4
      vertex -5.69249 39.3669 2.4
    endloop
  endfacet
  facet normal 0.41202 0.911175 -0
    outer loop
      vertex -5.30115 39.2414 2.4
      vertex -5.47453 39.3198 3
      vertex -5.30115 39.2414 3
    endloop
  endfacet
  facet normal 0.41202 0.911175 0
    outer loop
      vertex -5.47453 39.3198 3
      vertex -5.30115 39.2414 2.4
      vertex -5.47453 39.3198 2.4
    endloop
  endfacet
  facet normal 0.653076 0.757292 -0
    outer loop
      vertex -5.17522 39.1328 2.4
      vertex -5.30115 39.2414 3
      vertex -5.17522 39.1328 3
    endloop
  endfacet
  facet normal 0.653076 0.757292 0
    outer loop
      vertex -5.30115 39.2414 3
      vertex -5.17522 39.1328 2.4
      vertex -5.30115 39.2414 2.4
    endloop
  endfacet
  facet normal 0.875973 0.48236 0
    outer loop
      vertex -5.09967 38.9956 3
      vertex -5.17522 39.1328 2.4
      vertex -5.17522 39.1328 3
    endloop
  endfacet
  facet normal 0.875973 0.48236 0
    outer loop
      vertex -5.17522 39.1328 2.4
      vertex -5.09967 38.9956 3
      vertex -5.09967 38.9956 2.4
    endloop
  endfacet
  facet normal 0.988682 0.150029 0
    outer loop
      vertex -5.07448 38.8296 3
      vertex -5.09967 38.9956 2.4
      vertex -5.09967 38.9956 3
    endloop
  endfacet
  facet normal 0.988682 0.150029 0
    outer loop
      vertex -5.09967 38.9956 2.4
      vertex -5.07448 38.8296 3
      vertex -5.07448 38.8296 2.4
    endloop
  endfacet
  facet normal 0.989821 -0.142321 0
    outer loop
      vertex -5.09796 38.6663 3
      vertex -5.07448 38.8296 2.4
      vertex -5.07448 38.8296 3
    endloop
  endfacet
  facet normal 0.989821 -0.142321 0
    outer loop
      vertex -5.07448 38.8296 2.4
      vertex -5.09796 38.6663 3
      vertex -5.09796 38.6663 2.4
    endloop
  endfacet
  facet normal 0.882445 -0.470415 0
    outer loop
      vertex -5.16838 38.5342 3
      vertex -5.09796 38.6663 2.4
      vertex -5.09796 38.6663 3
    endloop
  endfacet
  facet normal 0.882445 -0.470415 0
    outer loop
      vertex -5.09796 38.6663 2.4
      vertex -5.16838 38.5342 3
      vertex -5.16838 38.5342 2.4
    endloop
  endfacet
  facet normal 0.652269 -0.757988 0
    outer loop
      vertex -5.28575 38.4332 2.4
      vertex -5.16838 38.5342 3
      vertex -5.28575 38.4332 3
    endloop
  endfacet
  facet normal 0.652269 -0.757988 0
    outer loop
      vertex -5.16838 38.5342 3
      vertex -5.28575 38.4332 2.4
      vertex -5.16838 38.5342 2.4
    endloop
  endfacet
  facet normal 0.394468 -0.91891 0
    outer loop
      vertex -5.45161 38.362 2.4
      vertex -5.28575 38.4332 3
      vertex -5.45161 38.362 3
    endloop
  endfacet
  facet normal 0.394468 -0.91891 0
    outer loop
      vertex -5.28575 38.4332 3
      vertex -5.45161 38.362 2.4
      vertex -5.28575 38.4332 2.4
    endloop
  endfacet
  facet normal 0.193949 -0.981012 0
    outer loop
      vertex -5.66759 38.3193 2.4
      vertex -5.45161 38.362 3
      vertex -5.66759 38.3193 3
    endloop
  endfacet
  facet normal 0.193949 -0.981012 0
    outer loop
      vertex -5.45161 38.362 3
      vertex -5.66759 38.3193 2.4
      vertex -5.45161 38.362 2.4
    endloop
  endfacet
  facet normal 0.0532916 -0.998579 0
    outer loop
      vertex -5.93367 38.3051 2.4
      vertex -5.66759 38.3193 3
      vertex -5.93367 38.3051 3
    endloop
  endfacet
  facet normal 0.0532916 -0.998579 0
    outer loop
      vertex -5.66759 38.3193 3
      vertex -5.93367 38.3051 2.4
      vertex -5.66759 38.3193 2.4
    endloop
  endfacet
  facet normal -0.118713 -0.992929 0
    outer loop
      vertex -6.42548 38.3639 2.4
      vertex -5.93367 38.3051 3
      vertex -6.42548 38.3639 3
    endloop
  endfacet
  facet normal -0.118713 -0.992929 -0
    outer loop
      vertex -5.93367 38.3051 3
      vertex -6.42548 38.3639 2.4
      vertex -5.93367 38.3051 2.4
    endloop
  endfacet
  facet normal -0.513084 -0.858339 0
    outer loop
      vertex -6.72058 38.5403 2.4
      vertex -6.42548 38.3639 3
      vertex -6.72058 38.5403 3
    endloop
  endfacet
  facet normal -0.513084 -0.858339 -0
    outer loop
      vertex -6.42548 38.3639 3
      vertex -6.72058 38.5403 2.4
      vertex -6.42548 38.3639 2.4
    endloop
  endfacet
  facet normal -0.948334 -0.317273 0
    outer loop
      vertex -6.72058 38.5403 2.4
      vertex -6.81894 38.8343 3
      vertex -6.81894 38.8343 2.4
    endloop
  endfacet
  facet normal -0.948334 -0.317273 0
    outer loop
      vertex -6.81894 38.8343 3
      vertex -6.72058 38.5403 2.4
      vertex -6.72058 38.5403 3
    endloop
  endfacet
  facet normal -0.988539 0.150964 0
    outer loop
      vertex -6.81894 38.8343 2.4
      vertex -6.79362 39.0001 3
      vertex -6.79362 39.0001 2.4
    endloop
  endfacet
  facet normal -0.988539 0.150964 0
    outer loop
      vertex -6.79362 39.0001 3
      vertex -6.81894 38.8343 2.4
      vertex -6.81894 38.8343 3
    endloop
  endfacet
  facet normal 0.968118 0.250495 0
    outer loop
      vertex -7.16969 43.9191 3
      vertex -7.2484 44.2233 2.4
      vertex -7.2484 44.2233 3
    endloop
  endfacet
  facet normal 0.968118 0.250495 0
    outer loop
      vertex -7.2484 44.2233 2.4
      vertex -7.16969 43.9191 3
      vertex -7.16969 43.9191 2.4
    endloop
  endfacet
  facet normal 0.899954 0.435986 0
    outer loop
      vertex -7.0385 43.6483 3
      vertex -7.16969 43.9191 2.4
      vertex -7.16969 43.9191 3
    endloop
  endfacet
  facet normal 0.899954 0.435986 0
    outer loop
      vertex -7.16969 43.9191 2.4
      vertex -7.0385 43.6483 3
      vertex -7.0385 43.6483 2.4
    endloop
  endfacet
  facet normal 0.783808 0.621004 0
    outer loop
      vertex -6.8535 43.4148 3
      vertex -7.0385 43.6483 2.4
      vertex -7.0385 43.6483 3
    endloop
  endfacet
  facet normal 0.783808 0.621004 0
    outer loop
      vertex -7.0385 43.6483 2.4
      vertex -6.8535 43.4148 3
      vertex -6.8535 43.4148 2.4
    endloop
  endfacet
  facet normal 0.625709 0.780057 -0
    outer loop
      vertex -6.61339 43.2222 2.4
      vertex -6.8535 43.4148 3
      vertex -6.61339 43.2222 3
    endloop
  endfacet
  facet normal 0.625709 0.780057 0
    outer loop
      vertex -6.8535 43.4148 3
      vertex -6.61339 43.2222 2.4
      vertex -6.8535 43.4148 2.4
    endloop
  endfacet
  facet normal 0.45727 0.889328 -0
    outer loop
      vertex -6.31816 43.0704 2.4
      vertex -6.61339 43.2222 3
      vertex -6.31816 43.0704 3
    endloop
  endfacet
  facet normal 0.45727 0.889328 0
    outer loop
      vertex -6.61339 43.2222 3
      vertex -6.31816 43.0704 2.4
      vertex -6.61339 43.2222 2.4
    endloop
  endfacet
  facet normal -0.935586 0.353099 0
    outer loop
      vertex -6.31816 43.0704 2.4
      vertex -6.08794 43.6804 3
      vertex -6.08794 43.6804 2.4
    endloop
  endfacet
  facet normal -0.935586 0.353099 0
    outer loop
      vertex -6.08794 43.6804 3
      vertex -6.31816 43.0704 2.4
      vertex -6.31816 43.0704 3
    endloop
  endfacet
  facet normal -0.506359 -0.862323 0
    outer loop
      vertex -6.44131 43.8879 2.4
      vertex -6.08794 43.6804 3
      vertex -6.44131 43.8879 3
    endloop
  endfacet
  facet normal -0.506359 -0.862323 -0
    outer loop
      vertex -6.08794 43.6804 3
      vertex -6.44131 43.8879 2.4
      vertex -6.08794 43.6804 2.4
    endloop
  endfacet
  facet normal -0.810685 -0.585482 0
    outer loop
      vertex -6.44131 43.8879 2.4
      vertex -6.65335 44.1815 3
      vertex -6.65335 44.1815 2.4
    endloop
  endfacet
  facet normal -0.810685 -0.585482 0
    outer loop
      vertex -6.65335 44.1815 3
      vertex -6.44131 43.8879 2.4
      vertex -6.44131 43.8879 3
    endloop
  endfacet
  facet normal -0.983096 -0.183093 0
    outer loop
      vertex -6.65335 44.1815 2.4
      vertex -6.72401 44.5609 3
      vertex -6.72401 44.5609 2.4
    endloop
  endfacet
  facet normal -0.983096 -0.183093 0
    outer loop
      vertex -6.72401 44.5609 3
      vertex -6.65335 44.1815 2.4
      vertex -6.65335 44.1815 3
    endloop
  endfacet
  facet normal -0.993436 0.114393 0
    outer loop
      vertex -6.72401 44.5609 2.4
      vertex -6.69026 44.854 3
      vertex -6.69026 44.854 2.4
    endloop
  endfacet
  facet normal -0.993436 0.114393 0
    outer loop
      vertex -6.69026 44.854 3
      vertex -6.72401 44.5609 2.4
      vertex -6.72401 44.5609 3
    endloop
  endfacet
  facet normal -0.923232 0.384244 0
    outer loop
      vertex -6.69026 44.854 2.4
      vertex -6.589 45.0973 3
      vertex -6.589 45.0973 2.4
    endloop
  endfacet
  facet normal -0.923232 0.384244 0
    outer loop
      vertex -6.589 45.0973 3
      vertex -6.69026 44.854 2.4
      vertex -6.69026 44.854 3
    endloop
  endfacet
  facet normal -0.753623 0.657307 0
    outer loop
      vertex -6.589 45.0973 2.4
      vertex -6.42023 45.2908 3
      vertex -6.42023 45.2908 2.4
    endloop
  endfacet
  facet normal -0.753623 0.657307 0
    outer loop
      vertex -6.42023 45.2908 3
      vertex -6.589 45.0973 2.4
      vertex -6.589 45.0973 3
    endloop
  endfacet
  facet normal -0.516328 0.856391 0
    outer loop
      vertex -6.18736 45.4312 2.4
      vertex -6.42023 45.2908 3
      vertex -6.18736 45.4312 3
    endloop
  endfacet
  facet normal -0.516328 0.856391 0
    outer loop
      vertex -6.42023 45.2908 3
      vertex -6.18736 45.4312 2.4
      vertex -6.42023 45.2908 2.4
    endloop
  endfacet
  facet normal -0.275742 0.961232 0
    outer loop
      vertex -5.89384 45.5154 2.4
      vertex -6.18736 45.4312 3
      vertex -5.89384 45.5154 3
    endloop
  endfacet
  facet normal -0.275742 0.961232 0
    outer loop
      vertex -6.18736 45.4312 3
      vertex -5.89384 45.5154 2.4
      vertex -6.18736 45.4312 2.4
    endloop
  endfacet
  facet normal -0.0790919 0.996867 0
    outer loop
      vertex -5.53967 45.5435 2.4
      vertex -5.89384 45.5154 3
      vertex -5.53967 45.5435 3
    endloop
  endfacet
  facet normal -0.0790919 0.996867 0
    outer loop
      vertex -5.89384 45.5154 3
      vertex -5.53967 45.5435 2.4
      vertex -5.89384 45.5154 2.4
    endloop
  endfacet
  facet normal 0.0782437 0.996934 -0
    outer loop
      vertex -5.19183 45.5162 2.4
      vertex -5.53967 45.5435 3
      vertex -5.19183 45.5162 3
    endloop
  endfacet
  facet normal 0.0782437 0.996934 0
    outer loop
      vertex -5.53967 45.5435 3
      vertex -5.19183 45.5162 2.4
      vertex -5.53967 45.5435 2.4
    endloop
  endfacet
  facet normal 0.273951 0.961744 -0
    outer loop
      vertex -4.90466 45.4344 2.4
      vertex -5.19183 45.5162 3
      vertex -4.90466 45.4344 3
    endloop
  endfacet
  facet normal 0.273951 0.961744 0
    outer loop
      vertex -5.19183 45.5162 3
      vertex -4.90466 45.4344 2.4
      vertex -5.19183 45.5162 2.4
    endloop
  endfacet
  facet normal 0.516146 0.8565 -0
    outer loop
      vertex -4.67815 45.2979 2.4
      vertex -4.90466 45.4344 3
      vertex -4.67815 45.2979 3
    endloop
  endfacet
  facet normal 0.516146 0.8565 0
    outer loop
      vertex -4.90466 45.4344 3
      vertex -4.67815 45.2979 2.4
      vertex -4.90466 45.4344 2.4
    endloop
  endfacet
  facet normal 0.756586 0.653895 0
    outer loop
      vertex -4.51463 45.1087 3
      vertex -4.67815 45.2979 2.4
      vertex -4.67815 45.2979 3
    endloop
  endfacet
  facet normal 0.756586 0.653895 0
    outer loop
      vertex -4.67815 45.2979 2.4
      vertex -4.51463 45.1087 3
      vertex -4.51463 45.1087 2.4
    endloop
  endfacet
  facet normal 0.925713 0.378227 0
    outer loop
      vertex -4.41653 44.8686 3
      vertex -4.51463 45.1087 2.4
      vertex -4.51463 45.1087 3
    endloop
  endfacet
  facet normal 0.925713 0.378227 0
    outer loop
      vertex -4.51463 45.1087 2.4
      vertex -4.41653 44.8686 3
      vertex -4.41653 44.8686 2.4
    endloop
  endfacet
  facet normal 0.993746 0.111668 0
    outer loop
      vertex -4.38383 44.5776 3
      vertex -4.41653 44.8686 2.4
      vertex -4.41653 44.8686 3
    endloop
  endfacet
  facet normal 0.993746 0.111668 0
    outer loop
      vertex -4.41653 44.8686 2.4
      vertex -4.38383 44.5776 3
      vertex -4.38383 44.5776 2.4
    endloop
  endfacet
  facet normal 0.996561 -0.0828624 0
    outer loop
      vertex -4.40031 44.3794 3
      vertex -4.38383 44.5776 2.4
      vertex -4.38383 44.5776 3
    endloop
  endfacet
  facet normal 0.996561 -0.0828624 0
    outer loop
      vertex -4.38383 44.5776 2.4
      vertex -4.40031 44.3794 3
      vertex -4.40031 44.3794 2.4
    endloop
  endfacet
  facet normal 0.964288 -0.264858 0
    outer loop
      vertex -4.44975 44.1994 3
      vertex -4.40031 44.3794 2.4
      vertex -4.40031 44.3794 3
    endloop
  endfacet
  facet normal 0.964288 -0.264858 0
    outer loop
      vertex -4.40031 44.3794 2.4
      vertex -4.44975 44.1994 3
      vertex -4.44975 44.1994 2.4
    endloop
  endfacet
  facet normal 0.891054 -0.453898 0
    outer loop
      vertex -4.53217 44.0376 3
      vertex -4.44975 44.1994 2.4
      vertex -4.44975 44.1994 3
    endloop
  endfacet
  facet normal 0.891054 -0.453898 0
    outer loop
      vertex -4.44975 44.1994 2.4
      vertex -4.53217 44.0376 3
      vertex -4.53217 44.0376 2.4
    endloop
  endfacet
  facet normal 0.776533 -0.630077 0
    outer loop
      vertex -4.64252 43.9016 3
      vertex -4.53217 44.0376 2.4
      vertex -4.53217 44.0376 3
    endloop
  endfacet
  facet normal 0.776533 -0.630077 0
    outer loop
      vertex -4.53217 44.0376 2.4
      vertex -4.64252 43.9016 3
      vertex -4.64252 43.9016 2.4
    endloop
  endfacet
  facet normal 0.609193 -0.793022 0
    outer loop
      vertex -4.77582 43.7992 2.4
      vertex -4.64252 43.9016 3
      vertex -4.77582 43.7992 3
    endloop
  endfacet
  facet normal 0.609193 -0.793022 0
    outer loop
      vertex -4.64252 43.9016 3
      vertex -4.77582 43.7992 2.4
      vertex -4.64252 43.9016 2.4
    endloop
  endfacet
  facet normal 0.403474 -0.914991 0
    outer loop
      vertex -4.93207 43.7303 2.4
      vertex -4.77582 43.7992 3
      vertex -4.93207 43.7303 3
    endloop
  endfacet
  facet normal 0.403474 -0.914991 0
    outer loop
      vertex -4.77582 43.7992 3
      vertex -4.93207 43.7303 2.4
      vertex -4.77582 43.7992 2.4
    endloop
  endfacet
  facet normal 0.964699 0.263354 0
    outer loop
      vertex -4.76358 43.1131 3
      vertex -4.93207 43.7303 2.4
      vertex -4.93207 43.7303 3
    endloop
  endfacet
  facet normal 0.964699 0.263354 0
    outer loop
      vertex -4.93207 43.7303 2.4
      vertex -4.76358 43.1131 3
      vertex -4.76358 43.1131 2.4
    endloop
  endfacet
  facet normal -0.404863 0.914377 0
    outer loop
      vertex -4.48285 43.2374 2.4
      vertex -4.76358 43.1131 3
      vertex -4.48285 43.2374 3
    endloop
  endfacet
  facet normal -0.404863 0.914377 0
    outer loop
      vertex -4.76358 43.1131 3
      vertex -4.48285 43.2374 2.4
      vertex -4.76358 43.1131 2.4
    endloop
  endfacet
  facet normal -0.599225 0.800581 0
    outer loop
      vertex -4.25145 43.4106 2.4
      vertex -4.48285 43.2374 3
      vertex -4.25145 43.4106 3
    endloop
  endfacet
  facet normal -0.599225 0.800581 0
    outer loop
      vertex -4.48285 43.2374 3
      vertex -4.25145 43.4106 2.4
      vertex -4.48285 43.2374 2.4
    endloop
  endfacet
  facet normal -0.773585 0.633692 0
    outer loop
      vertex -4.25145 43.4106 2.4
      vertex -4.06935 43.6329 3
      vertex -4.06935 43.6329 2.4
    endloop
  endfacet
  facet normal -0.773585 0.633692 0
    outer loop
      vertex -4.06935 43.6329 3
      vertex -4.25145 43.4106 2.4
      vertex -4.25145 43.4106 3
    endloop
  endfacet
  facet normal -0.900117 0.435649 0
    outer loop
      vertex -4.06935 43.6329 2.4
      vertex -3.93814 43.904 3
      vertex -3.93814 43.904 2.4
    endloop
  endfacet
  facet normal -0.900117 0.435649 0
    outer loop
      vertex -3.93814 43.904 3
      vertex -4.06935 43.6329 2.4
      vertex -4.06935 43.6329 3
    endloop
  endfacet
  facet normal -0.970998 0.23909 0
    outer loop
      vertex -3.93814 43.904 2.4
      vertex -3.85942 44.2237 3
      vertex -3.85942 44.2237 2.4
    endloop
  endfacet
  facet normal -0.970998 0.23909 0
    outer loop
      vertex -3.85942 44.2237 3
      vertex -3.93814 43.904 2.4
      vertex -3.93814 43.904 3
    endloop
  endfacet
  facet normal -0.997469 0.0711045 0
    outer loop
      vertex -3.85942 44.2237 2.4
      vertex -3.83318 44.5918 3
      vertex -3.83318 44.5918 2.4
    endloop
  endfacet
  facet normal -0.997469 0.0711045 0
    outer loop
      vertex -3.83318 44.5918 3
      vertex -3.85942 44.2237 2.4
      vertex -3.85942 44.2237 3
    endloop
  endfacet
  facet normal -0.995136 -0.0985094 0
    outer loop
      vertex -3.83318 44.5918 2.4
      vertex -3.88223 45.0873 3
      vertex -3.88223 45.0873 2.4
    endloop
  endfacet
  facet normal -0.995136 -0.0985094 0
    outer loop
      vertex -3.88223 45.0873 3
      vertex -3.83318 44.5918 2.4
      vertex -3.83318 44.5918 3
    endloop
  endfacet
  facet normal -0.94138 -0.337347 0
    outer loop
      vertex -3.88223 45.0873 2.4
      vertex -4.02937 45.4979 3
      vertex -4.02937 45.4979 2.4
    endloop
  endfacet
  facet normal -0.94138 -0.337347 0
    outer loop
      vertex -4.02937 45.4979 3
      vertex -3.88223 45.0873 2.4
      vertex -3.88223 45.0873 3
    endloop
  endfacet
  facet normal -0.798839 -0.601545 0
    outer loop
      vertex -4.02937 45.4979 2.4
      vertex -4.27463 45.8236 3
      vertex -4.27463 45.8236 2.4
    endloop
  endfacet
  facet normal -0.798839 -0.601545 0
    outer loop
      vertex -4.27463 45.8236 3
      vertex -4.02937 45.4979 2.4
      vertex -4.02937 45.4979 3
    endloop
  endfacet
  facet normal -0.5739 -0.818926 0
    outer loop
      vertex -4.61139 46.0596 2.4
      vertex -4.27463 45.8236 3
      vertex -4.61139 46.0596 3
    endloop
  endfacet
  facet normal -0.5739 -0.818926 -0
    outer loop
      vertex -4.27463 45.8236 3
      vertex -4.61139 46.0596 2.4
      vertex -4.27463 45.8236 2.4
    endloop
  endfacet
  facet normal -0.318533 -0.947912 0
    outer loop
      vertex -5.03307 46.2013 2.4
      vertex -4.61139 46.0596 3
      vertex -5.03307 46.2013 3
    endloop
  endfacet
  facet normal -0.318533 -0.947912 -0
    outer loop
      vertex -4.61139 46.0596 3
      vertex -5.03307 46.2013 2.4
      vertex -4.61139 46.0596 2.4
    endloop
  endfacet
  facet normal -0.0927684 -0.995688 0
    outer loop
      vertex -5.53967 46.2485 2.4
      vertex -5.03307 46.2013 3
      vertex -5.53967 46.2485 3
    endloop
  endfacet
  facet normal -0.0927684 -0.995688 -0
    outer loop
      vertex -5.03307 46.2013 3
      vertex -5.53967 46.2485 2.4
      vertex -5.03307 46.2013 2.4
    endloop
  endfacet
  facet normal 0.0960079 -0.995381 0
    outer loop
      vertex -6.04665 46.1996 2.4
      vertex -5.53967 46.2485 3
      vertex -6.04665 46.1996 3
    endloop
  endfacet
  facet normal 0.0960079 -0.995381 0
    outer loop
      vertex -5.53967 46.2485 3
      vertex -6.04665 46.1996 2.4
      vertex -5.53967 46.2485 2.4
    endloop
  endfacet
  facet normal 0.325785 -0.945444 0
    outer loop
      vertex -6.47267 46.0528 2.4
      vertex -6.04665 46.1996 3
      vertex -6.47267 46.0528 3
    endloop
  endfacet
  facet normal 0.325785 -0.945444 0
    outer loop
      vertex -6.04665 46.1996 3
      vertex -6.47267 46.0528 2.4
      vertex -6.04665 46.1996 2.4
    endloop
  endfacet
  facet normal 0.578282 -0.815837 0
    outer loop
      vertex -6.81775 45.8082 2.4
      vertex -6.47267 46.0528 3
      vertex -6.81775 45.8082 3
    endloop
  endfacet
  facet normal 0.578282 -0.815837 0
    outer loop
      vertex -6.47267 46.0528 3
      vertex -6.81775 45.8082 2.4
      vertex -6.47267 46.0528 2.4
    endloop
  endfacet
  facet normal 0.796435 -0.604724 0
    outer loop
      vertex -7.07158 45.4739 3
      vertex -6.81775 45.8082 2.4
      vertex -6.81775 45.8082 3
    endloop
  endfacet
  facet normal 0.796435 -0.604724 0
    outer loop
      vertex -6.81775 45.8082 2.4
      vertex -7.07158 45.4739 3
      vertex -7.07158 45.4739 2.4
    endloop
  endfacet
  facet normal 0.938966 -0.344009 0
    outer loop
      vertex -7.22388 45.0582 3
      vertex -7.07158 45.4739 2.4
      vertex -7.07158 45.4739 3
    endloop
  endfacet
  facet normal 0.938966 -0.344009 0
    outer loop
      vertex -7.07158 45.4739 2.4
      vertex -7.22388 45.0582 3
      vertex -7.22388 45.0582 2.4
    endloop
  endfacet
  facet normal 0.994831 -0.101544 0
    outer loop
      vertex -7.27464 44.5609 3
      vertex -7.22388 45.0582 2.4
      vertex -7.22388 45.0582 3
    endloop
  endfacet
  facet normal 0.994831 -0.101544 0
    outer loop
      vertex -7.22388 45.0582 2.4
      vertex -7.27464 44.5609 3
      vertex -7.27464 44.5609 2.4
    endloop
  endfacet
  facet normal 0.996993 0.0774914 0
    outer loop
      vertex -7.2484 44.2233 3
      vertex -7.27464 44.5609 2.4
      vertex -7.27464 44.5609 3
    endloop
  endfacet
  facet normal 0.996993 0.0774914 0
    outer loop
      vertex -7.27464 44.5609 2.4
      vertex -7.2484 44.2233 3
      vertex -7.2484 44.2233 2.4
    endloop
  endfacet
  facet normal 0.971706 0.236192 0
    outer loop
      vertex -7.15913 30.3253 3
      vertex -7.24576 30.6817 2.4
      vertex -7.24576 30.6817 3
    endloop
  endfacet
  facet normal 0.971706 0.236192 0
    outer loop
      vertex -7.24576 30.6817 2.4
      vertex -7.15913 30.3253 3
      vertex -7.15913 30.3253 2.4
    endloop
  endfacet
  facet normal 0.889288 0.457348 0
    outer loop
      vertex -7.01477 30.0446 3
      vertex -7.15913 30.3253 2.4
      vertex -7.15913 30.3253 3
    endloop
  endfacet
  facet normal 0.889288 0.457348 0
    outer loop
      vertex -7.15913 30.3253 2.4
      vertex -7.01477 30.0446 3
      vertex -7.01477 30.0446 2.4
    endloop
  endfacet
  facet normal 0.713088 0.701074 0
    outer loop
      vertex -6.81578 29.8422 3
      vertex -7.01477 30.0446 2.4
      vertex -7.01477 30.0446 3
    endloop
  endfacet
  facet normal 0.713088 0.701074 0
    outer loop
      vertex -7.01477 30.0446 2.4
      vertex -6.81578 29.8422 3
      vertex -6.81578 29.8422 2.4
    endloop
  endfacet
  facet normal 0.436547 0.899682 -0
    outer loop
      vertex -6.56538 29.7207 2.4
      vertex -6.81578 29.8422 3
      vertex -6.56538 29.7207 3
    endloop
  endfacet
  facet normal 0.436547 0.899682 0
    outer loop
      vertex -6.81578 29.8422 3
      vertex -6.56538 29.7207 2.4
      vertex -6.81578 29.8422 2.4
    endloop
  endfacet
  facet normal 0.132998 0.991116 -0
    outer loop
      vertex -6.26357 29.6802 2.4
      vertex -6.56538 29.7207 3
      vertex -6.26357 29.6802 3
    endloop
  endfacet
  facet normal 0.132998 0.991116 0
    outer loop
      vertex -6.56538 29.7207 3
      vertex -6.26357 29.6802 2.4
      vertex -6.56538 29.7207 2.4
    endloop
  endfacet
  facet normal -0.0537179 0.998556 0
    outer loop
      vertex -6.12973 29.6874 2.4
      vertex -6.26357 29.6802 3
      vertex -6.12973 29.6874 3
    endloop
  endfacet
  facet normal -0.0537179 0.998556 0
    outer loop
      vertex -6.26357 29.6802 3
      vertex -6.12973 29.6874 2.4
      vertex -6.26357 29.6802 2.4
    endloop
  endfacet
  facet normal -0.170631 0.985335 0
    outer loop
      vertex -6.00673 29.7087 2.4
      vertex -6.12973 29.6874 3
      vertex -6.00673 29.7087 3
    endloop
  endfacet
  facet normal -0.170631 0.985335 0
    outer loop
      vertex -6.12973 29.6874 3
      vertex -6.00673 29.7087 2.4
      vertex -6.12973 29.6874 2.4
    endloop
  endfacet
  facet normal -0.302432 0.953171 0
    outer loop
      vertex -5.89453 29.7443 2.4
      vertex -6.00673 29.7087 3
      vertex -5.89453 29.7443 3
    endloop
  endfacet
  facet normal -0.302432 0.953171 0
    outer loop
      vertex -6.00673 29.7087 3
      vertex -5.89453 29.7443 2.4
      vertex -6.00673 29.7087 2.4
    endloop
  endfacet
  facet normal -0.434393 0.900724 0
    outer loop
      vertex -5.79272 29.7934 2.4
      vertex -5.89453 29.7443 3
      vertex -5.79272 29.7934 3
    endloop
  endfacet
  facet normal -0.434393 0.900724 0
    outer loop
      vertex -5.89453 29.7443 3
      vertex -5.79272 29.7934 2.4
      vertex -5.89453 29.7443 2.4
    endloop
  endfacet
  facet normal -0.55791 0.829902 0
    outer loop
      vertex -5.70094 29.8551 2.4
      vertex -5.79272 29.7934 3
      vertex -5.70094 29.8551 3
    endloop
  endfacet
  facet normal -0.55791 0.829902 0
    outer loop
      vertex -5.79272 29.7934 3
      vertex -5.70094 29.8551 2.4
      vertex -5.79272 29.7934 2.4
    endloop
  endfacet
  facet normal -0.673078 0.739572 0
    outer loop
      vertex -5.61919 29.9295 2.4
      vertex -5.70094 29.8551 3
      vertex -5.61919 29.9295 3
    endloop
  endfacet
  facet normal -0.673078 0.739572 0
    outer loop
      vertex -5.70094 29.8551 3
      vertex -5.61919 29.9295 2.4
      vertex -5.70094 29.8551 2.4
    endloop
  endfacet
  facet normal -0.775226 0.631684 0
    outer loop
      vertex -5.61919 29.9295 2.4
      vertex -5.54561 30.0198 3
      vertex -5.54561 30.0198 2.4
    endloop
  endfacet
  facet normal -0.775226 0.631684 0
    outer loop
      vertex -5.54561 30.0198 3
      vertex -5.61919 29.9295 2.4
      vertex -5.61919 29.9295 3
    endloop
  endfacet
  facet normal -0.852338 0.522991 0
    outer loop
      vertex -5.54561 30.0198 2.4
      vertex -5.47836 30.1294 3
      vertex -5.47836 30.1294 2.4
    endloop
  endfacet
  facet normal -0.852338 0.522991 0
    outer loop
      vertex -5.47836 30.1294 3
      vertex -5.54561 30.0198 2.4
      vertex -5.54561 30.0198 3
    endloop
  endfacet
  facet normal -0.904011 0.42751 0
    outer loop
      vertex -5.47836 30.1294 2.4
      vertex -5.41745 30.2582 3
      vertex -5.41745 30.2582 2.4
    endloop
  endfacet
  facet normal -0.904011 0.42751 0
    outer loop
      vertex -5.41745 30.2582 3
      vertex -5.47836 30.1294 2.4
      vertex -5.47836 30.1294 3
    endloop
  endfacet
  facet normal -0.943256 0.332066 0
    outer loop
      vertex -5.41745 30.2582 2.4
      vertex -5.35799 30.4271 3
      vertex -5.35799 30.4271 2.4
    endloop
  endfacet
  facet normal -0.943256 0.332066 0
    outer loop
      vertex -5.35799 30.4271 3
      vertex -5.41745 30.2582 2.4
      vertex -5.41745 30.2582 3
    endloop
  endfacet
  facet normal -0.964521 0.264005 0
    outer loop
      vertex -5.35799 30.4271 2.4
      vertex -5.29509 30.6569 3
      vertex -5.29509 30.6569 2.4
    endloop
  endfacet
  facet normal -0.964521 0.264005 0
    outer loop
      vertex -5.29509 30.6569 3
      vertex -5.35799 30.4271 2.4
      vertex -5.35799 30.4271 3
    endloop
  endfacet
  facet normal -0.974959 0.222383 0
    outer loop
      vertex -5.29509 30.6569 2.4
      vertex -5.22876 30.9477 3
      vertex -5.22876 30.9477 2.4
    endloop
  endfacet
  facet normal -0.974959 0.222383 0
    outer loop
      vertex -5.22876 30.9477 3
      vertex -5.29509 30.6569 2.4
      vertex -5.29509 30.6569 3
    endloop
  endfacet
  facet normal -0.974561 0.224125 0
    outer loop
      vertex -5.22876 30.9477 2.4
      vertex -5.17352 31.1879 3
      vertex -5.17352 31.1879 2.4
    endloop
  endfacet
  facet normal -0.974561 0.224125 0
    outer loop
      vertex -5.17352 31.1879 3
      vertex -5.22876 30.9477 2.4
      vertex -5.22876 30.9477 3
    endloop
  endfacet
  facet normal -0.965202 0.261507 0
    outer loop
      vertex -5.17352 31.1879 2.4
      vertex -5.12486 31.3675 3
      vertex -5.12486 31.3675 2.4
    endloop
  endfacet
  facet normal -0.965202 0.261507 0
    outer loop
      vertex -5.12486 31.3675 3
      vertex -5.17352 31.1879 2.4
      vertex -5.17352 31.1879 3
    endloop
  endfacet
  facet normal -0.942866 0.333172 0
    outer loop
      vertex -5.12486 31.3675 2.4
      vertex -5.08281 31.4865 3
      vertex -5.08281 31.4865 2.4
    endloop
  endfacet
  facet normal -0.942866 0.333172 0
    outer loop
      vertex -5.08281 31.4865 3
      vertex -5.12486 31.3675 2.4
      vertex -5.12486 31.3675 3
    endloop
  endfacet
  facet normal -0.890538 0.454908 0
    outer loop
      vertex -5.08281 31.4865 2.4
      vertex -5.04128 31.5678 3
      vertex -5.04128 31.5678 2.4
    endloop
  endfacet
  facet normal -0.890538 0.454908 0
    outer loop
      vertex -5.04128 31.5678 3
      vertex -5.08281 31.4865 2.4
      vertex -5.08281 31.4865 3
    endloop
  endfacet
  facet normal -0.817794 0.575512 0
    outer loop
      vertex -5.04128 31.5678 2.4
      vertex -4.9942 31.6347 3
      vertex -4.9942 31.6347 2.4
    endloop
  endfacet
  facet normal -0.817794 0.575512 0
    outer loop
      vertex -4.9942 31.6347 3
      vertex -5.04128 31.5678 2.4
      vertex -5.04128 31.5678 3
    endloop
  endfacet
  facet normal -0.705014 0.709193 0
    outer loop
      vertex -4.94159 31.687 2.4
      vertex -4.9942 31.6347 3
      vertex -4.94159 31.687 3
    endloop
  endfacet
  facet normal -0.705014 0.709193 0
    outer loop
      vertex -4.9942 31.6347 3
      vertex -4.94159 31.687 2.4
      vertex -4.9942 31.6347 2.4
    endloop
  endfacet
  facet normal -0.526784 0.849999 0
    outer loop
      vertex -4.88092 31.7246 2.4
      vertex -4.94159 31.687 3
      vertex -4.88092 31.7246 3
    endloop
  endfacet
  facet normal -0.526784 0.849999 0
    outer loop
      vertex -4.94159 31.687 3
      vertex -4.88092 31.7246 2.4
      vertex -4.94159 31.687 2.4
    endloop
  endfacet
  facet normal -0.301285 0.953534 0
    outer loop
      vertex -4.80971 31.7471 2.4
      vertex -4.88092 31.7246 3
      vertex -4.80971 31.7471 3
    endloop
  endfacet
  facet normal -0.301285 0.953534 0
    outer loop
      vertex -4.88092 31.7246 3
      vertex -4.80971 31.7471 2.4
      vertex -4.88092 31.7246 2.4
    endloop
  endfacet
  facet normal -0.0913484 0.995819 0
    outer loop
      vertex -4.72795 31.7546 2.4
      vertex -4.80971 31.7471 3
      vertex -4.72795 31.7546 3
    endloop
  endfacet
  facet normal -0.0913484 0.995819 0
    outer loop
      vertex -4.80971 31.7471 3
      vertex -4.72795 31.7546 2.4
      vertex -4.80971 31.7471 2.4
    endloop
  endfacet
  facet normal 0.304061 0.952653 -0
    outer loop
      vertex -4.50644 31.6839 2.4
      vertex -4.72795 31.7546 3
      vertex -4.50644 31.6839 3
    endloop
  endfacet
  facet normal 0.304061 0.952653 0
    outer loop
      vertex -4.72795 31.7546 3
      vertex -4.50644 31.6839 2.4
      vertex -4.72795 31.7546 2.4
    endloop
  endfacet
  facet normal 0.847279 0.531148 0
    outer loop
      vertex -4.37354 31.4719 3
      vertex -4.50644 31.6839 2.4
      vertex -4.50644 31.6839 3
    endloop
  endfacet
  facet normal 0.847279 0.531148 0
    outer loop
      vertex -4.50644 31.6839 2.4
      vertex -4.37354 31.4719 3
      vertex -4.37354 31.4719 2.4
    endloop
  endfacet
  facet normal 0.992228 0.124436 0
    outer loop
      vertex -4.32922 31.1185 3
      vertex -4.37354 31.4719 2.4
      vertex -4.37354 31.4719 3
    endloop
  endfacet
  facet normal 0.992228 0.124436 0
    outer loop
      vertex -4.37354 31.4719 2.4
      vertex -4.32922 31.1185 3
      vertex -4.32922 31.1185 2.4
    endloop
  endfacet
  facet normal 0.997825 -0.0659248 0
    outer loop
      vertex -4.34137 30.9346 3
      vertex -4.32922 31.1185 2.4
      vertex -4.32922 31.1185 3
    endloop
  endfacet
  facet normal 0.997825 -0.0659248 0
    outer loop
      vertex -4.32922 31.1185 2.4
      vertex -4.34137 30.9346 3
      vertex -4.34137 30.9346 2.4
    endloop
  endfacet
  facet normal 0.972895 -0.231245 0
    outer loop
      vertex -4.37776 30.7815 3
      vertex -4.34137 30.9346 2.4
      vertex -4.34137 30.9346 3
    endloop
  endfacet
  facet normal 0.972895 -0.231245 0
    outer loop
      vertex -4.34137 30.9346 2.4
      vertex -4.37776 30.7815 3
      vertex -4.37776 30.7815 2.4
    endloop
  endfacet
  facet normal 0.895684 -0.44469 0
    outer loop
      vertex -4.43843 30.6593 3
      vertex -4.37776 30.7815 2.4
      vertex -4.37776 30.7815 3
    endloop
  endfacet
  facet normal 0.895684 -0.44469 0
    outer loop
      vertex -4.37776 30.7815 2.4
      vertex -4.43843 30.6593 3
      vertex -4.43843 30.6593 2.4
    endloop
  endfacet
  facet normal 0.745949 -0.666003 0
    outer loop
      vertex -4.52307 30.5645 3
      vertex -4.43843 30.6593 2.4
      vertex -4.43843 30.6593 3
    endloop
  endfacet
  facet normal 0.745949 -0.666003 0
    outer loop
      vertex -4.43843 30.6593 2.4
      vertex -4.52307 30.5645 3
      vertex -4.52307 30.5645 2.4
    endloop
  endfacet
  facet normal 0.546904 -0.837195 0
    outer loop
      vertex -4.63145 30.4937 2.4
      vertex -4.52307 30.5645 3
      vertex -4.63145 30.4937 3
    endloop
  endfacet
  facet normal 0.546904 -0.837195 0
    outer loop
      vertex -4.52307 30.5645 3
      vertex -4.63145 30.4937 2.4
      vertex -4.52307 30.5645 2.4
    endloop
  endfacet
  facet normal 0.333872 -0.942618 0
    outer loop
      vertex -4.76358 30.4469 2.4
      vertex -4.63145 30.4937 3
      vertex -4.76358 30.4469 3
    endloop
  endfacet
  facet normal 0.333872 -0.942618 0
    outer loop
      vertex -4.63145 30.4937 3
      vertex -4.76358 30.4469 2.4
      vertex -4.63145 30.4937 2.4
    endloop
  endfacet
  facet normal 0.990829 0.135122 0
    outer loop
      vertex -4.67101 29.7681 3
      vertex -4.76358 30.4469 2.4
      vertex -4.76358 30.4469 3
    endloop
  endfacet
  facet normal 0.990829 0.135122 0
    outer loop
      vertex -4.76358 30.4469 2.4
      vertex -4.67101 29.7681 3
      vertex -4.67101 29.7681 2.4
    endloop
  endfacet
  facet normal -0.298466 0.95442 0
    outer loop
      vertex -4.40016 29.8528 2.4
      vertex -4.67101 29.7681 3
      vertex -4.40016 29.8528 3
    endloop
  endfacet
  facet normal -0.298466 0.95442 0
    outer loop
      vertex -4.67101 29.7681 3
      vertex -4.40016 29.8528 2.4
      vertex -4.67101 29.7681 2.4
    endloop
  endfacet
  facet normal -0.530567 0.847643 0
    outer loop
      vertex -4.18576 29.987 2.4
      vertex -4.40016 29.8528 3
      vertex -4.18576 29.987 3
    endloop
  endfacet
  facet normal -0.530567 0.847643 0
    outer loop
      vertex -4.40016 29.8528 3
      vertex -4.18576 29.987 2.4
      vertex -4.40016 29.8528 2.4
    endloop
  endfacet
  facet normal -0.757744 0.652552 0
    outer loop
      vertex -4.18576 29.987 2.4
      vertex -4.02782 30.1704 3
      vertex -4.02782 30.1704 2.4
    endloop
  endfacet
  facet normal -0.757744 0.652552 0
    outer loop
      vertex -4.02782 30.1704 3
      vertex -4.18576 29.987 2.4
      vertex -4.18576 29.987 3
    endloop
  endfacet
  facet normal -0.913305 0.407277 0
    outer loop
      vertex -4.02782 30.1704 2.4
      vertex -3.91968 30.4129 3
      vertex -3.91968 30.4129 2.4
    endloop
  endfacet
  facet normal -0.913305 0.407277 0
    outer loop
      vertex -3.91968 30.4129 3
      vertex -4.02782 30.1704 2.4
      vertex -4.02782 30.1704 3
    endloop
  endfacet
  facet normal -0.978964 0.204032 0
    outer loop
      vertex -3.91968 30.4129 2.4
      vertex -3.8548 30.7242 3
      vertex -3.8548 30.7242 2.4
    endloop
  endfacet
  facet normal -0.978964 0.204032 0
    outer loop
      vertex -3.8548 30.7242 3
      vertex -3.91968 30.4129 2.4
      vertex -3.91968 30.4129 3
    endloop
  endfacet
  facet normal -0.998386 0.056788 0
    outer loop
      vertex -3.8548 30.7242 2.4
      vertex -3.83318 31.1043 3
      vertex -3.83318 31.1043 2.4
    endloop
  endfacet
  facet normal -0.998386 0.056788 0
    outer loop
      vertex -3.83318 31.1043 3
      vertex -3.8548 30.7242 2.4
      vertex -3.8548 30.7242 3
    endloop
  endfacet
  facet normal -0.99776 -0.0669006 0
    outer loop
      vertex -3.83318 31.1043 2.4
      vertex -3.85994 31.5034 3
      vertex -3.85994 31.5034 2.4
    endloop
  endfacet
  facet normal -0.99776 -0.0669006 0
    outer loop
      vertex -3.85994 31.5034 3
      vertex -3.83318 31.1043 2.4
      vertex -3.83318 31.1043 3
    endloop
  endfacet
  facet normal -0.97169 -0.236259 0
    outer loop
      vertex -3.85994 31.5034 2.4
      vertex -3.94025 31.8337 3
      vertex -3.94025 31.8337 2.4
    endloop
  endfacet
  facet normal -0.97169 -0.236259 0
    outer loop
      vertex -3.94025 31.8337 3
      vertex -3.85994 31.5034 2.4
      vertex -3.85994 31.5034 3
    endloop
  endfacet
  facet normal -0.890194 -0.455582 0
    outer loop
      vertex -3.94025 31.8337 2.4
      vertex -4.07408 32.0952 3
      vertex -4.07408 32.0952 2.4
    endloop
  endfacet
  facet normal -0.890194 -0.455582 0
    outer loop
      vertex -4.07408 32.0952 3
      vertex -3.94025 31.8337 2.4
      vertex -3.94025 31.8337 3
    endloop
  endfacet
  facet normal -0.716492 -0.697595 0
    outer loop
      vertex -4.07408 32.0952 2.4
      vertex -4.25829 32.2844 3
      vertex -4.25829 32.2844 2.4
    endloop
  endfacet
  facet normal -0.716492 -0.697595 0
    outer loop
      vertex -4.25829 32.2844 3
      vertex -4.07408 32.0952 2.4
      vertex -4.07408 32.0952 3
    endloop
  endfacet
  facet normal -0.440357 -0.897823 0
    outer loop
      vertex -4.4897 32.3979 2.4
      vertex -4.25829 32.2844 3
      vertex -4.4897 32.3979 3
    endloop
  endfacet
  facet normal -0.440357 -0.897823 -0
    outer loop
      vertex -4.25829 32.2844 3
      vertex -4.4897 32.3979 2.4
      vertex -4.25829 32.2844 2.4
    endloop
  endfacet
  facet normal -0.134791 -0.990874 0
    outer loop
      vertex -4.76831 32.4358 2.4
      vertex -4.4897 32.3979 3
      vertex -4.76831 32.4358 3
    endloop
  endfacet
  facet normal -0.134791 -0.990874 -0
    outer loop
      vertex -4.4897 32.3979 3
      vertex -4.76831 32.4358 2.4
      vertex -4.4897 32.3979 2.4
    endloop
  endfacet
  facet normal 0.045495 -0.998965 0
    outer loop
      vertex -4.88249 32.4306 2.4
      vertex -4.76831 32.4358 3
      vertex -4.88249 32.4306 3
    endloop
  endfacet
  facet normal 0.045495 -0.998965 0
    outer loop
      vertex -4.76831 32.4358 3
      vertex -4.88249 32.4306 2.4
      vertex -4.76831 32.4358 2.4
    endloop
  endfacet
  facet normal 0.144804 -0.98946 0
    outer loop
      vertex -4.98772 32.4152 2.4
      vertex -4.88249 32.4306 3
      vertex -4.98772 32.4152 3
    endloop
  endfacet
  facet normal 0.144804 -0.98946 0
    outer loop
      vertex -4.88249 32.4306 3
      vertex -4.98772 32.4152 2.4
      vertex -4.88249 32.4306 2.4
    endloop
  endfacet
  facet normal 0.257975 -0.966152 0
    outer loop
      vertex -5.08397 32.3895 2.4
      vertex -4.98772 32.4152 3
      vertex -5.08397 32.3895 3
    endloop
  endfacet
  facet normal 0.257975 -0.966152 0
    outer loop
      vertex -4.98772 32.4152 3
      vertex -5.08397 32.3895 2.4
      vertex -4.98772 32.4152 2.4
    endloop
  endfacet
  facet normal 0.369346 -0.929292 0
    outer loop
      vertex -5.17178 32.3546 2.4
      vertex -5.08397 32.3895 3
      vertex -5.17178 32.3546 3
    endloop
  endfacet
  facet normal 0.369346 -0.929292 0
    outer loop
      vertex -5.08397 32.3895 3
      vertex -5.17178 32.3546 2.4
      vertex -5.08397 32.3895 2.4
    endloop
  endfacet
  facet normal 0.474711 -0.880142 0
    outer loop
      vertex -5.25169 32.3115 2.4
      vertex -5.17178 32.3546 3
      vertex -5.25169 32.3115 3
    endloop
  endfacet
  facet normal 0.474711 -0.880142 0
    outer loop
      vertex -5.17178 32.3546 3
      vertex -5.25169 32.3115 2.4
      vertex -5.17178 32.3546 2.4
    endloop
  endfacet
  facet normal 0.580328 -0.814383 0
    outer loop
      vertex -5.32368 32.2602 2.4
      vertex -5.25169 32.3115 3
      vertex -5.32368 32.2602 3
    endloop
  endfacet
  facet normal 0.580328 -0.814383 0
    outer loop
      vertex -5.25169 32.3115 3
      vertex -5.32368 32.2602 2.4
      vertex -5.25169 32.3115 2.4
    endloop
  endfacet
  facet normal 0.675389 -0.737461 0
    outer loop
      vertex -5.38843 32.2009 2.4
      vertex -5.32368 32.2602 3
      vertex -5.38843 32.2009 3
    endloop
  endfacet
  facet normal 0.675389 -0.737461 0
    outer loop
      vertex -5.32368 32.2602 3
      vertex -5.38843 32.2009 2.4
      vertex -5.32368 32.2602 2.4
    endloop
  endfacet
  facet normal 0.756616 -0.65386 0
    outer loop
      vertex -5.44659 32.1336 3
      vertex -5.38843 32.2009 2.4
      vertex -5.38843 32.2009 3
    endloop
  endfacet
  facet normal 0.756616 -0.65386 0
    outer loop
      vertex -5.38843 32.2009 2.4
      vertex -5.44659 32.1336 3
      vertex -5.44659 32.1336 2.4
    endloop
  endfacet
  facet normal 0.824407 -0.565998 0
    outer loop
      vertex -5.49815 32.0585 3
      vertex -5.44659 32.1336 2.4
      vertex -5.44659 32.1336 3
    endloop
  endfacet
  facet normal 0.824407 -0.565998 0
    outer loop
      vertex -5.44659 32.1336 2.4
      vertex -5.49815 32.0585 3
      vertex -5.49815 32.0585 2.4
    endloop
  endfacet
  facet normal 0.872181 -0.489184 0
    outer loop
      vertex -5.54431 31.9762 3
      vertex -5.49815 32.0585 2.4
      vertex -5.49815 32.0585 3
    endloop
  endfacet
  facet normal 0.872181 -0.489184 0
    outer loop
      vertex -5.49815 32.0585 2.4
      vertex -5.54431 31.9762 3
      vertex -5.54431 31.9762 2.4
    endloop
  endfacet
  facet normal 0.903889 -0.427766 0
    outer loop
      vertex -5.58624 31.8876 3
      vertex -5.54431 31.9762 2.4
      vertex -5.54431 31.9762 3
    endloop
  endfacet
  facet normal 0.903889 -0.427766 0
    outer loop
      vertex -5.54431 31.9762 2.4
      vertex -5.58624 31.8876 3
      vertex -5.58624 31.8876 2.4
    endloop
  endfacet
  facet normal 0.929452 -0.368943 0
    outer loop
      vertex -5.62395 31.7926 3
      vertex -5.58624 31.8876 2.4
      vertex -5.58624 31.8876 3
    endloop
  endfacet
  facet normal 0.929452 -0.368943 0
    outer loop
      vertex -5.58624 31.8876 2.4
      vertex -5.62395 31.7926 3
      vertex -5.62395 31.7926 2.4
    endloop
  endfacet
  facet normal 0.952599 -0.304229 0
    outer loop
      vertex -5.66336 31.6692 3
      vertex -5.62395 31.7926 2.4
      vertex -5.62395 31.7926 3
    endloop
  endfacet
  facet normal 0.952599 -0.304229 0
    outer loop
      vertex -5.62395 31.7926 2.4
      vertex -5.66336 31.6692 3
      vertex -5.66336 31.6692 2.4
    endloop
  endfacet
  facet normal 0.965355 -0.26094 0
    outer loop
      vertex -5.71042 31.4951 3
      vertex -5.66336 31.6692 2.4
      vertex -5.66336 31.6692 3
    endloop
  endfacet
  facet normal 0.965355 -0.26094 0
    outer loop
      vertex -5.66336 31.6692 2.4
      vertex -5.71042 31.4951 3
      vertex -5.71042 31.4951 2.4
    endloop
  endfacet
  facet normal 0.971605 -0.23661 0
    outer loop
      vertex -5.76514 31.2704 3
      vertex -5.71042 31.4951 2.4
      vertex -5.71042 31.4951 3
    endloop
  endfacet
  facet normal 0.971605 -0.23661 0
    outer loop
      vertex -5.71042 31.4951 2.4
      vertex -5.76514 31.2704 3
      vertex -5.76514 31.2704 2.4
    endloop
  endfacet
  facet normal 0.977561 -0.210651 0
    outer loop
      vertex -5.8208 31.0121 3
      vertex -5.76514 31.2704 2.4
      vertex -5.76514 31.2704 3
    endloop
  endfacet
  facet normal 0.977561 -0.210651 0
    outer loop
      vertex -5.76514 31.2704 2.4
      vertex -5.8208 31.0121 3
      vertex -5.8208 31.0121 2.4
    endloop
  endfacet
  facet normal 0.969085 -0.246726 0
    outer loop
      vertex -5.87065 30.8163 3
      vertex -5.8208 31.0121 2.4
      vertex -5.8208 31.0121 3
    endloop
  endfacet
  facet normal 0.969085 -0.246726 0
    outer loop
      vertex -5.8208 31.0121 2.4
      vertex -5.87065 30.8163 3
      vertex -5.87065 30.8163 2.4
    endloop
  endfacet
  facet normal 0.94952 -0.313705 0
    outer loop
      vertex -5.91469 30.683 3
      vertex -5.87065 30.8163 2.4
      vertex -5.87065 30.8163 3
    endloop
  endfacet
  facet normal 0.94952 -0.313705 0
    outer loop
      vertex -5.87065 30.8163 2.4
      vertex -5.91469 30.683 3
      vertex -5.91469 30.683 2.4
    endloop
  endfacet
  facet normal 0.904277 -0.426945 0
    outer loop
      vertex -5.95926 30.5886 3
      vertex -5.91469 30.683 2.4
      vertex -5.91469 30.683 3
    endloop
  endfacet
  facet normal 0.904277 -0.426945 0
    outer loop
      vertex -5.91469 30.683 2.4
      vertex -5.95926 30.5886 3
      vertex -5.95926 30.5886 2.4
    endloop
  endfacet
  facet normal 0.838468 -0.544951 0
    outer loop
      vertex -6.01067 30.5095 3
      vertex -5.95926 30.5886 2.4
      vertex -5.95926 30.5886 3
    endloop
  endfacet
  facet normal 0.838468 -0.544951 0
    outer loop
      vertex -5.95926 30.5886 2.4
      vertex -6.01067 30.5095 3
      vertex -6.01067 30.5095 2.4
    endloop
  endfacet
  facet normal 0.738325 -0.674445 0
    outer loop
      vertex -6.06895 30.4457 3
      vertex -6.01067 30.5095 2.4
      vertex -6.01067 30.5095 3
    endloop
  endfacet
  facet normal 0.738325 -0.674445 0
    outer loop
      vertex -6.01067 30.5095 2.4
      vertex -6.06895 30.4457 3
      vertex -6.06895 30.4457 2.4
    endloop
  endfacet
  facet normal 0.571208 -0.820806 0
    outer loop
      vertex -6.1362 30.3989 2.4
      vertex -6.06895 30.4457 3
      vertex -6.1362 30.3989 3
    endloop
  endfacet
  facet normal 0.571208 -0.820806 0
    outer loop
      vertex -6.06895 30.4457 3
      vertex -6.1362 30.3989 2.4
      vertex -6.06895 30.4457 2.4
    endloop
  endfacet
  facet normal 0.337745 -0.941238 0
    outer loop
      vertex -6.21451 30.3708 2.4
      vertex -6.1362 30.3989 3
      vertex -6.21451 30.3708 3
    endloop
  endfacet
  facet normal 0.337745 -0.941238 0
    outer loop
      vertex -6.1362 30.3989 3
      vertex -6.21451 30.3708 2.4
      vertex -6.1362 30.3989 2.4
    endloop
  endfacet
  facet normal 0.104569 -0.994518 0
    outer loop
      vertex -6.30391 30.3614 2.4
      vertex -6.21451 30.3708 3
      vertex -6.30391 30.3614 3
    endloop
  endfacet
  facet normal 0.104569 -0.994518 0
    outer loop
      vertex -6.21451 30.3708 3
      vertex -6.30391 30.3614 2.4
      vertex -6.21451 30.3708 2.4
    endloop
  endfacet
  facet normal -0.312305 -0.949982 0
    outer loop
      vertex -6.55182 30.4429 2.4
      vertex -6.30391 30.3614 3
      vertex -6.55182 30.4429 3
    endloop
  endfacet
  facet normal -0.312305 -0.949982 -0
    outer loop
      vertex -6.30391 30.3614 3
      vertex -6.55182 30.4429 2.4
      vertex -6.30391 30.3614 2.4
    endloop
  endfacet
  facet normal -0.854348 -0.519702 0
    outer loop
      vertex -6.55182 30.4429 2.4
      vertex -6.70055 30.6874 3
      vertex -6.70055 30.6874 2.4
    endloop
  endfacet
  facet normal -0.854348 -0.519702 0
    outer loop
      vertex -6.70055 30.6874 3
      vertex -6.55182 30.4429 2.4
      vertex -6.55182 30.4429 3
    endloop
  endfacet
  facet normal -0.992673 -0.120831 0
    outer loop
      vertex -6.70055 30.6874 2.4
      vertex -6.75014 31.0948 3
      vertex -6.75014 31.0948 2.4
    endloop
  endfacet
  facet normal -0.992673 -0.120831 0
    outer loop
      vertex -6.75014 31.0948 3
      vertex -6.70055 30.6874 2.4
      vertex -6.70055 30.6874 3
    endloop
  endfacet
  facet normal -0.998149 0.0608204 0
    outer loop
      vertex -6.75014 31.0948 2.4
      vertex -6.73682 31.3134 3
      vertex -6.73682 31.3134 2.4
    endloop
  endfacet
  facet normal -0.998149 0.0608204 0
    outer loop
      vertex -6.73682 31.3134 3
      vertex -6.75014 31.0948 2.4
      vertex -6.75014 31.0948 3
    endloop
  endfacet
  facet normal -0.977327 0.211736 0
    outer loop
      vertex -6.73682 31.3134 2.4
      vertex -6.69687 31.4978 3
      vertex -6.69687 31.4978 2.4
    endloop
  endfacet
  facet normal -0.977327 0.211736 0
    outer loop
      vertex -6.69687 31.4978 3
      vertex -6.73682 31.3134 2.4
      vertex -6.73682 31.3134 3
    endloop
  endfacet
  facet normal -0.914007 0.405697 0
    outer loop
      vertex -6.69687 31.4978 2.4
      vertex -6.63029 31.6478 3
      vertex -6.63029 31.6478 2.4
    endloop
  endfacet
  facet normal -0.914007 0.405697 0
    outer loop
      vertex -6.63029 31.6478 3
      vertex -6.69687 31.4978 2.4
      vertex -6.69687 31.4978 3
    endloop
  endfacet
  facet normal -0.776306 0.630356 0
    outer loop
      vertex -6.63029 31.6478 2.4
      vertex -6.53415 31.7662 3
      vertex -6.53415 31.7662 2.4
    endloop
  endfacet
  facet normal -0.776306 0.630356 0
    outer loop
      vertex -6.53415 31.7662 3
      vertex -6.63029 31.6478 2.4
      vertex -6.63029 31.6478 3
    endloop
  endfacet
  facet normal -0.570922 0.821004 0
    outer loop
      vertex -6.40559 31.8556 2.4
      vertex -6.53415 31.7662 3
      vertex -6.40559 31.8556 3
    endloop
  endfacet
  facet normal -0.570922 0.821004 0
    outer loop
      vertex -6.53415 31.7662 3
      vertex -6.40559 31.8556 2.4
      vertex -6.53415 31.7662 2.4
    endloop
  endfacet
  facet normal -0.351232 0.936289 0
    outer loop
      vertex -6.24458 31.916 2.4
      vertex -6.40559 31.8556 3
      vertex -6.24458 31.916 3
    endloop
  endfacet
  facet normal -0.351232 0.936289 0
    outer loop
      vertex -6.40559 31.8556 3
      vertex -6.24458 31.916 2.4
      vertex -6.40559 31.8556 2.4
    endloop
  endfacet
  facet normal -0.986674 -0.16271 0
    outer loop
      vertex -6.24458 31.916 2.4
      vertex -6.35614 32.5925 3
      vertex -6.35614 32.5925 2.4
    endloop
  endfacet
  facet normal -0.986674 -0.16271 0
    outer loop
      vertex -6.35614 32.5925 3
      vertex -6.24458 31.916 2.4
      vertex -6.24458 31.916 3
    endloop
  endfacet
  facet normal 0.329902 -0.944015 0
    outer loop
      vertex -6.63857 32.4938 2.4
      vertex -6.35614 32.5925 3
      vertex -6.63857 32.4938 3
    endloop
  endfacet
  facet normal 0.329902 -0.944015 0
    outer loop
      vertex -6.35614 32.5925 3
      vertex -6.63857 32.4938 2.4
      vertex -6.35614 32.5925 2.4
    endloop
  endfacet
  facet normal 0.562434 -0.826842 0
    outer loop
      vertex -6.86879 32.3372 2.4
      vertex -6.63857 32.4938 3
      vertex -6.86879 32.3372 3
    endloop
  endfacet
  facet normal 0.562434 -0.826842 0
    outer loop
      vertex -6.63857 32.4938 3
      vertex -6.86879 32.3372 2.4
      vertex -6.63857 32.4938 2.4
    endloop
  endfacet
  facet normal 0.769853 -0.638221 0
    outer loop
      vertex -7.04678 32.1225 3
      vertex -6.86879 32.3372 2.4
      vertex -6.86879 32.3372 3
    endloop
  endfacet
  facet normal 0.769853 -0.638221 0
    outer loop
      vertex -6.86879 32.3372 2.4
      vertex -7.04678 32.1225 3
      vertex -7.04678 32.1225 2.4
    endloop
  endfacet
  facet normal 0.908088 -0.418779 0
    outer loop
      vertex -7.17337 31.848 3
      vertex -7.04678 32.1225 2.4
      vertex -7.04678 32.1225 3
    endloop
  endfacet
  facet normal 0.908088 -0.418779 0
    outer loop
      vertex -7.04678 32.1225 2.4
      vertex -7.17337 31.848 3
      vertex -7.17337 31.848 2.4
    endloop
  endfacet
  facet normal 0.975428 -0.22032 0
    outer loop
      vertex -7.24933 31.5117 3
      vertex -7.17337 31.848 2.4
      vertex -7.17337 31.848 3
    endloop
  endfacet
  facet normal 0.975428 -0.22032 0
    outer loop
      vertex -7.17337 31.848 2.4
      vertex -7.24933 31.5117 3
      vertex -7.24933 31.5117 2.4
    endloop
  endfacet
  facet normal 0.997983 -0.0634807 0
    outer loop
      vertex -7.27464 31.1138 3
      vertex -7.24933 31.5117 2.4
      vertex -7.24933 31.5117 3
    endloop
  endfacet
  facet normal 0.997983 -0.0634807 0
    outer loop
      vertex -7.24933 31.5117 2.4
      vertex -7.27464 31.1138 3
      vertex -7.27464 31.1138 2.4
    endloop
  endfacet
  facet normal 0.997774 0.0666876 0
    outer loop
      vertex -7.24576 30.6817 3
      vertex -7.27464 31.1138 2.4
      vertex -7.27464 31.1138 3
    endloop
  endfacet
  facet normal 0.997774 0.0666876 0
    outer loop
      vertex -7.27464 31.1138 2.4
      vertex -7.24576 30.6817 3
      vertex -7.24576 30.6817 2.4
    endloop
  endfacet
  facet normal 0.968118 0.250495 0
    outer loop
      vertex -7.16969 33.632 3
      vertex -7.2484 33.9362 2.4
      vertex -7.2484 33.9362 3
    endloop
  endfacet
  facet normal 0.968118 0.250495 0
    outer loop
      vertex -7.2484 33.9362 2.4
      vertex -7.16969 33.632 3
      vertex -7.16969 33.632 2.4
    endloop
  endfacet
  facet normal 0.89989 0.436116 0
    outer loop
      vertex -7.0385 33.3613 3
      vertex -7.16969 33.632 2.4
      vertex -7.16969 33.632 3
    endloop
  endfacet
  facet normal 0.89989 0.436116 0
    outer loop
      vertex -7.16969 33.632 2.4
      vertex -7.0385 33.3613 3
      vertex -7.0385 33.3613 2.4
    endloop
  endfacet
  facet normal 0.783937 0.62084 0
    outer loop
      vertex -6.8535 33.1277 3
      vertex -7.0385 33.3613 2.4
      vertex -7.0385 33.3613 3
    endloop
  endfacet
  facet normal 0.783937 0.62084 0
    outer loop
      vertex -7.0385 33.3613 2.4
      vertex -6.8535 33.1277 3
      vertex -6.8535 33.1277 2.4
    endloop
  endfacet
  facet normal 0.625709 0.780057 -0
    outer loop
      vertex -6.61339 32.9351 2.4
      vertex -6.8535 33.1277 3
      vertex -6.61339 32.9351 3
    endloop
  endfacet
  facet normal 0.625709 0.780057 0
    outer loop
      vertex -6.8535 33.1277 3
      vertex -6.61339 32.9351 2.4
      vertex -6.8535 33.1277 2.4
    endloop
  endfacet
  facet normal 0.457032 0.88945 -0
    outer loop
      vertex -6.31816 32.7834 2.4
      vertex -6.61339 32.9351 3
      vertex -6.31816 32.7834 3
    endloop
  endfacet
  facet normal 0.457032 0.88945 0
    outer loop
      vertex -6.61339 32.9351 3
      vertex -6.31816 32.7834 2.4
      vertex -6.61339 32.9351 2.4
    endloop
  endfacet
  facet normal -0.935567 0.35315 0
    outer loop
      vertex -6.31816 32.7834 2.4
      vertex -6.08794 33.3933 3
      vertex -6.08794 33.3933 2.4
    endloop
  endfacet
  facet normal -0.935567 0.35315 0
    outer loop
      vertex -6.08794 33.3933 3
      vertex -6.31816 32.7834 2.4
      vertex -6.31816 32.7834 3
    endloop
  endfacet
  facet normal -0.50654 -0.862216 0
    outer loop
      vertex -6.44131 33.6009 2.4
      vertex -6.08794 33.3933 3
      vertex -6.44131 33.6009 3
    endloop
  endfacet
  facet normal -0.50654 -0.862216 -0
    outer loop
      vertex -6.08794 33.3933 3
      vertex -6.44131 33.6009 2.4
      vertex -6.08794 33.3933 2.4
    endloop
  endfacet
  facet normal -0.81059 -0.585614 0
    outer loop
      vertex -6.44131 33.6009 2.4
      vertex -6.65335 33.8944 3
      vertex -6.65335 33.8944 2.4
    endloop
  endfacet
  facet normal -0.81059 -0.585614 0
    outer loop
      vertex -6.65335 33.8944 3
      vertex -6.44131 33.6009 2.4
      vertex -6.44131 33.6009 3
    endloop
  endfacet
  facet normal -0.983104 -0.183047 0
    outer loop
      vertex -6.65335 33.8944 2.4
      vertex -6.72401 34.2739 3
      vertex -6.72401 34.2739 2.4
    endloop
  endfacet
  facet normal -0.983104 -0.183047 0
    outer loop
      vertex -6.72401 34.2739 3
      vertex -6.65335 33.8944 2.4
      vertex -6.65335 33.8944 3
    endloop
  endfacet
  facet normal -0.993436 0.114393 0
    outer loop
      vertex -6.72401 34.2739 2.4
      vertex -6.69026 34.567 3
      vertex -6.69026 34.567 2.4
    endloop
  endfacet
  facet normal -0.993436 0.114393 0
    outer loop
      vertex -6.69026 34.567 3
      vertex -6.72401 34.2739 2.4
      vertex -6.72401 34.2739 3
    endloop
  endfacet
  facet normal -0.923176 0.384378 0
    outer loop
      vertex -6.69026 34.567 2.4
      vertex -6.589 34.8102 3
      vertex -6.589 34.8102 2.4
    endloop
  endfacet
  facet normal -0.923176 0.384378 0
    outer loop
      vertex -6.589 34.8102 3
      vertex -6.69026 34.567 2.4
      vertex -6.69026 34.567 3
    endloop
  endfacet
  facet normal -0.753623 0.657307 0
    outer loop
      vertex -6.589 34.8102 2.4
      vertex -6.42023 35.0037 3
      vertex -6.42023 35.0037 2.4
    endloop
  endfacet
  facet normal -0.753623 0.657307 0
    outer loop
      vertex -6.42023 35.0037 3
      vertex -6.589 34.8102 2.4
      vertex -6.589 34.8102 3
    endloop
  endfacet
  facet normal -0.516328 0.856391 0
    outer loop
      vertex -6.18736 35.1441 2.4
      vertex -6.42023 35.0037 3
      vertex -6.18736 35.1441 3
    endloop
  endfacet
  facet normal -0.516328 0.856391 0
    outer loop
      vertex -6.42023 35.0037 3
      vertex -6.18736 35.1441 2.4
      vertex -6.42023 35.0037 2.4
    endloop
  endfacet
  facet normal -0.276044 0.961145 0
    outer loop
      vertex -5.89384 35.2284 2.4
      vertex -6.18736 35.1441 3
      vertex -5.89384 35.2284 3
    endloop
  endfacet
  facet normal -0.276044 0.961145 0
    outer loop
      vertex -6.18736 35.1441 3
      vertex -5.89384 35.2284 2.4
      vertex -6.18736 35.1441 2.4
    endloop
  endfacet
  facet normal -0.0790919 0.996867 0
    outer loop
      vertex -5.53967 35.2565 2.4
      vertex -5.89384 35.2284 3
      vertex -5.53967 35.2565 3
    endloop
  endfacet
  facet normal -0.0790919 0.996867 0
    outer loop
      vertex -5.89384 35.2284 3
      vertex -5.53967 35.2565 2.4
      vertex -5.89384 35.2284 2.4
    endloop
  endfacet
  facet normal 0.0782437 0.996934 -0
    outer loop
      vertex -5.19183 35.2292 2.4
      vertex -5.53967 35.2565 3
      vertex -5.19183 35.2292 3
    endloop
  endfacet
  facet normal 0.0782437 0.996934 0
    outer loop
      vertex -5.53967 35.2565 3
      vertex -5.19183 35.2292 2.4
      vertex -5.53967 35.2565 2.4
    endloop
  endfacet
  facet normal 0.274261 0.961655 -0
    outer loop
      vertex -4.90466 35.1473 2.4
      vertex -5.19183 35.2292 3
      vertex -4.90466 35.1473 3
    endloop
  endfacet
  facet normal 0.274261 0.961655 0
    outer loop
      vertex -5.19183 35.2292 3
      vertex -4.90466 35.1473 2.4
      vertex -5.19183 35.2292 2.4
    endloop
  endfacet
  facet normal 0.516146 0.8565 -0
    outer loop
      vertex -4.67815 35.0108 2.4
      vertex -4.90466 35.1473 3
      vertex -4.67815 35.0108 3
    endloop
  endfacet
  facet normal 0.516146 0.8565 0
    outer loop
      vertex -4.90466 35.1473 3
      vertex -4.67815 35.0108 2.4
      vertex -4.90466 35.1473 2.4
    endloop
  endfacet
  facet normal 0.756586 0.653895 0
    outer loop
      vertex -4.51463 34.8216 3
      vertex -4.67815 35.0108 2.4
      vertex -4.67815 35.0108 3
    endloop
  endfacet
  facet normal 0.756586 0.653895 0
    outer loop
      vertex -4.67815 35.0108 2.4
      vertex -4.51463 34.8216 3
      vertex -4.51463 34.8216 2.4
    endloop
  endfacet
  facet normal 0.925713 0.378227 0
    outer loop
      vertex -4.41653 34.5815 3
      vertex -4.51463 34.8216 2.4
      vertex -4.51463 34.8216 3
    endloop
  endfacet
  facet normal 0.925713 0.378227 0
    outer loop
      vertex -4.51463 34.8216 2.4
      vertex -4.41653 34.5815 3
      vertex -4.41653 34.5815 2.4
    endloop
  endfacet
  facet normal 0.993746 0.111668 0
    outer loop
      vertex -4.38383 34.2905 3
      vertex -4.41653 34.5815 2.4
      vertex -4.41653 34.5815 3
    endloop
  endfacet
  facet normal 0.993746 0.111668 0
    outer loop
      vertex -4.41653 34.5815 2.4
      vertex -4.38383 34.2905 3
      vertex -4.38383 34.2905 2.4
    endloop
  endfacet
  facet normal 0.996561 -0.0828624 0
    outer loop
      vertex -4.40031 34.0923 3
      vertex -4.38383 34.2905 2.4
      vertex -4.38383 34.2905 3
    endloop
  endfacet
  facet normal 0.996561 -0.0828624 0
    outer loop
      vertex -4.38383 34.2905 2.4
      vertex -4.40031 34.0923 3
      vertex -4.40031 34.0923 2.4
    endloop
  endfacet
  facet normal 0.964288 -0.264858 0
    outer loop
      vertex -4.44975 33.9123 3
      vertex -4.40031 34.0923 2.4
      vertex -4.40031 34.0923 3
    endloop
  endfacet
  facet normal 0.964288 -0.264858 0
    outer loop
      vertex -4.40031 34.0923 2.4
      vertex -4.44975 33.9123 3
      vertex -4.44975 33.9123 2.4
    endloop
  endfacet
  facet normal 0.891054 -0.453898 0
    outer loop
      vertex -4.53217 33.7505 3
      vertex -4.44975 33.9123 2.4
      vertex -4.44975 33.9123 3
    endloop
  endfacet
  facet normal 0.891054 -0.453898 0
    outer loop
      vertex -4.44975 33.9123 2.4
      vertex -4.53217 33.7505 3
      vertex -4.53217 33.7505 2.4
    endloop
  endfacet
  facet normal 0.776306 -0.630356 0
    outer loop
      vertex -4.64252 33.6146 3
      vertex -4.53217 33.7505 2.4
      vertex -4.53217 33.7505 3
    endloop
  endfacet
  facet normal 0.776306 -0.630356 0
    outer loop
      vertex -4.53217 33.7505 2.4
      vertex -4.64252 33.6146 3
      vertex -4.64252 33.6146 2.4
    endloop
  endfacet
  facet normal 0.609567 -0.792735 0
    outer loop
      vertex -4.77582 33.5121 2.4
      vertex -4.64252 33.6146 3
      vertex -4.77582 33.5121 3
    endloop
  endfacet
  facet normal 0.609567 -0.792735 0
    outer loop
      vertex -4.64252 33.6146 3
      vertex -4.77582 33.5121 2.4
      vertex -4.64252 33.6146 2.4
    endloop
  endfacet
  facet normal 0.403474 -0.914991 0
    outer loop
      vertex -4.93207 33.4432 2.4
      vertex -4.77582 33.5121 3
      vertex -4.93207 33.4432 3
    endloop
  endfacet
  facet normal 0.403474 -0.914991 0
    outer loop
      vertex -4.77582 33.5121 3
      vertex -4.93207 33.4432 2.4
      vertex -4.77582 33.5121 2.4
    endloop
  endfacet
  facet normal 0.964699 0.263354 0
    outer loop
      vertex -4.76358 32.826 3
      vertex -4.93207 33.4432 2.4
      vertex -4.93207 33.4432 3
    endloop
  endfacet
  facet normal 0.964699 0.263354 0
    outer loop
      vertex -4.93207 33.4432 2.4
      vertex -4.76358 32.826 3
      vertex -4.76358 32.826 2.4
    endloop
  endfacet
  facet normal -0.404863 0.914377 0
    outer loop
      vertex -4.48285 32.9503 2.4
      vertex -4.76358 32.826 3
      vertex -4.48285 32.9503 3
    endloop
  endfacet
  facet normal -0.404863 0.914377 0
    outer loop
      vertex -4.76358 32.826 3
      vertex -4.48285 32.9503 2.4
      vertex -4.76358 32.826 2.4
    endloop
  endfacet
  facet normal -0.599446 0.800415 0
    outer loop
      vertex -4.25145 33.1236 2.4
      vertex -4.48285 32.9503 3
      vertex -4.25145 33.1236 3
    endloop
  endfacet
  facet normal -0.599446 0.800415 0
    outer loop
      vertex -4.48285 32.9503 3
      vertex -4.25145 33.1236 2.4
      vertex -4.48285 32.9503 2.4
    endloop
  endfacet
  facet normal -0.773585 0.633692 0
    outer loop
      vertex -4.25145 33.1236 2.4
      vertex -4.06935 33.3459 3
      vertex -4.06935 33.3459 2.4
    endloop
  endfacet
  facet normal -0.773585 0.633692 0
    outer loop
      vertex -4.06935 33.3459 3
      vertex -4.25145 33.1236 2.4
      vertex -4.25145 33.1236 3
    endloop
  endfacet
  facet normal -0.900117 0.435649 0
    outer loop
      vertex -4.06935 33.3459 2.4
      vertex -3.93814 33.617 3
      vertex -3.93814 33.617 2.4
    endloop
  endfacet
  facet normal -0.900117 0.435649 0
    outer loop
      vertex -3.93814 33.617 3
      vertex -4.06935 33.3459 2.4
      vertex -4.06935 33.3459 3
    endloop
  endfacet
  facet normal -0.97098 0.23916 0
    outer loop
      vertex -3.93814 33.617 2.4
      vertex -3.85942 33.9366 3
      vertex -3.85942 33.9366 2.4
    endloop
  endfacet
  facet normal -0.97098 0.23916 0
    outer loop
      vertex -3.85942 33.9366 3
      vertex -3.93814 33.617 2.4
      vertex -3.93814 33.617 3
    endloop
  endfacet
  facet normal -0.997469 0.0711045 0
    outer loop
      vertex -3.85942 33.9366 2.4
      vertex -3.83318 34.3047 3
      vertex -3.83318 34.3047 2.4
    endloop
  endfacet
  facet normal -0.997469 0.0711045 0
    outer loop
      vertex -3.83318 34.3047 3
      vertex -3.85942 33.9366 2.4
      vertex -3.85942 33.9366 3
    endloop
  endfacet
  facet normal -0.995136 -0.0985094 0
    outer loop
      vertex -3.83318 34.3047 2.4
      vertex -3.88223 34.8002 3
      vertex -3.88223 34.8002 2.4
    endloop
  endfacet
  facet normal -0.995136 -0.0985094 0
    outer loop
      vertex -3.88223 34.8002 3
      vertex -3.83318 34.3047 2.4
      vertex -3.83318 34.3047 3
    endloop
  endfacet
  facet normal -0.941406 -0.337274 0
    outer loop
      vertex -3.88223 34.8002 2.4
      vertex -4.02937 35.2109 3
      vertex -4.02937 35.2109 2.4
    endloop
  endfacet
  facet normal -0.941406 -0.337274 0
    outer loop
      vertex -4.02937 35.2109 3
      vertex -3.88223 34.8002 2.4
      vertex -3.88223 34.8002 3
    endloop
  endfacet
  facet normal -0.798839 -0.601545 0
    outer loop
      vertex -4.02937 35.2109 2.4
      vertex -4.27463 35.5366 3
      vertex -4.27463 35.5366 2.4
    endloop
  endfacet
  facet normal -0.798839 -0.601545 0
    outer loop
      vertex -4.27463 35.5366 3
      vertex -4.02937 35.2109 2.4
      vertex -4.02937 35.2109 3
    endloop
  endfacet
  facet normal -0.5739 -0.818926 0
    outer loop
      vertex -4.61139 35.7726 2.4
      vertex -4.27463 35.5366 3
      vertex -4.61139 35.7726 3
    endloop
  endfacet
  facet normal -0.5739 -0.818926 -0
    outer loop
      vertex -4.27463 35.5366 3
      vertex -4.61139 35.7726 2.4
      vertex -4.27463 35.5366 2.4
    endloop
  endfacet
  facet normal -0.318331 -0.94798 0
    outer loop
      vertex -5.03307 35.9142 2.4
      vertex -4.61139 35.7726 3
      vertex -5.03307 35.9142 3
    endloop
  endfacet
  facet normal -0.318331 -0.94798 -0
    outer loop
      vertex -4.61139 35.7726 3
      vertex -5.03307 35.9142 2.4
      vertex -4.61139 35.7726 2.4
    endloop
  endfacet
  facet normal -0.0927684 -0.995688 0
    outer loop
      vertex -5.53967 35.9614 2.4
      vertex -5.03307 35.9142 3
      vertex -5.53967 35.9614 3
    endloop
  endfacet
  facet normal -0.0927684 -0.995688 -0
    outer loop
      vertex -5.03307 35.9142 3
      vertex -5.53967 35.9614 2.4
      vertex -5.03307 35.9142 2.4
    endloop
  endfacet
  facet normal 0.0960079 -0.995381 0
    outer loop
      vertex -6.04665 35.9125 2.4
      vertex -5.53967 35.9614 3
      vertex -6.04665 35.9125 3
    endloop
  endfacet
  facet normal 0.0960079 -0.995381 0
    outer loop
      vertex -5.53967 35.9614 3
      vertex -6.04665 35.9125 2.4
      vertex -5.53967 35.9614 2.4
    endloop
  endfacet
  facet normal 0.325785 -0.945444 0
    outer loop
      vertex -6.47267 35.7657 2.4
      vertex -6.04665 35.9125 3
      vertex -6.47267 35.7657 3
    endloop
  endfacet
  facet normal 0.325785 -0.945444 0
    outer loop
      vertex -6.04665 35.9125 3
      vertex -6.47267 35.7657 2.4
      vertex -6.04665 35.9125 2.4
    endloop
  endfacet
  facet normal 0.578282 -0.815837 0
    outer loop
      vertex -6.81775 35.5211 2.4
      vertex -6.47267 35.7657 3
      vertex -6.81775 35.5211 3
    endloop
  endfacet
  facet normal 0.578282 -0.815837 0
    outer loop
      vertex -6.47267 35.7657 3
      vertex -6.81775 35.5211 2.4
      vertex -6.47267 35.7657 2.4
    endloop
  endfacet
  facet normal 0.796435 -0.604724 0
    outer loop
      vertex -7.07158 35.1868 3
      vertex -6.81775 35.5211 2.4
      vertex -6.81775 35.5211 3
    endloop
  endfacet
  facet normal 0.796435 -0.604724 0
    outer loop
      vertex -6.81775 35.5211 2.4
      vertex -7.07158 35.1868 3
      vertex -7.07158 35.1868 2.4
    endloop
  endfacet
  facet normal 0.938966 -0.344009 0
    outer loop
      vertex -7.22388 34.7711 3
      vertex -7.07158 35.1868 2.4
      vertex -7.07158 35.1868 3
    endloop
  endfacet
  facet normal 0.938966 -0.344009 0
    outer loop
      vertex -7.07158 35.1868 2.4
      vertex -7.22388 34.7711 3
      vertex -7.22388 34.7711 2.4
    endloop
  endfacet
  facet normal 0.994829 -0.101564 0
    outer loop
      vertex -7.27464 34.2739 3
      vertex -7.22388 34.7711 2.4
      vertex -7.22388 34.7711 3
    endloop
  endfacet
  facet normal 0.994829 -0.101564 0
    outer loop
      vertex -7.22388 34.7711 2.4
      vertex -7.27464 34.2739 3
      vertex -7.27464 34.2739 2.4
    endloop
  endfacet
  facet normal 0.996995 0.0774686 0
    outer loop
      vertex -7.2484 33.9362 3
      vertex -7.27464 34.2739 2.4
      vertex -7.27464 34.2739 3
    endloop
  endfacet
  facet normal 0.996995 0.0774686 0
    outer loop
      vertex -7.27464 34.2739 2.4
      vertex -7.2484 33.9362 3
      vertex -7.2484 33.9362 2.4
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -3.88301 36.4543 2.4
      vertex -3.88301 37.1545 3
      vertex -3.88301 37.1545 2.4
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -3.88301 37.1545 3
      vertex -3.88301 36.4543 2.4
      vertex -3.88301 36.4543 3
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -7.22717 37.1545 2.4
      vertex -3.88301 37.1545 3
      vertex -7.22717 37.1545 3
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex -3.88301 37.1545 3
      vertex -7.22717 37.1545 2.4
      vertex -3.88301 37.1545 2.4
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex -7.22717 36.4543 3
      vertex -7.22717 37.1545 2.4
      vertex -7.22717 37.1545 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -7.22717 37.1545 2.4
      vertex -7.22717 36.4543 3
      vertex -7.22717 36.4543 2.4
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex -3.88301 36.4543 2.4
      vertex -7.22717 36.4543 3
      vertex -3.88301 36.4543 3
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -7.22717 36.4543 3
      vertex -3.88301 36.4543 2.4
      vertex -7.22717 36.4543 2.4
    endloop
  endfacet
  facet normal 0.948094 0.317991 0
    outer loop
      vertex -8.15149 41.9423 3
      vertex -8.21478 42.131 2.4
      vertex -8.21478 42.131 3
    endloop
  endfacet
  facet normal 0.948094 0.317991 0
    outer loop
      vertex -8.21478 42.131 2.4
      vertex -8.15149 41.9423 3
      vertex -8.15149 41.9423 2.4
    endloop
  endfacet
  facet normal 0.835685 0.549209 0
    outer loop
      vertex -8.04601 41.7818 3
      vertex -8.15149 41.9423 2.4
      vertex -8.15149 41.9423 3
    endloop
  endfacet
  facet normal 0.835685 0.549209 0
    outer loop
      vertex -8.15149 41.9423 2.4
      vertex -8.04601 41.7818 3
      vertex -8.04601 41.7818 2.4
    endloop
  endfacet
  facet normal 0.669717 0.742617 -0
    outer loop
      vertex -7.88567 41.6372 2.4
      vertex -8.04601 41.7818 3
      vertex -7.88567 41.6372 3
    endloop
  endfacet
  facet normal 0.669717 0.742617 0
    outer loop
      vertex -8.04601 41.7818 3
      vertex -7.88567 41.6372 2.4
      vertex -8.04601 41.7818 2.4
    endloop
  endfacet
  facet normal 0.527029 0.849848 -0
    outer loop
      vertex -7.65782 41.4959 2.4
      vertex -7.88567 41.6372 3
      vertex -7.65782 41.4959 3
    endloop
  endfacet
  facet normal 0.527029 0.849848 0
    outer loop
      vertex -7.88567 41.6372 3
      vertex -7.65782 41.4959 2.4
      vertex -7.88567 41.6372 2.4
    endloop
  endfacet
  facet normal 0.422546 0.906341 -0
    outer loop
      vertex -7.36246 41.3582 2.4
      vertex -7.65782 41.4959 3
      vertex -7.36246 41.3582 3
    endloop
  endfacet
  facet normal 0.422546 0.906341 0
    outer loop
      vertex -7.65782 41.4959 3
      vertex -7.36246 41.3582 2.4
      vertex -7.65782 41.4959 2.4
    endloop
  endfacet
  facet normal 0.351776 0.936084 -0
    outer loop
      vertex -4.65913 40.3423 2.4
      vertex -7.36246 41.3582 3
      vertex -4.65913 40.3423 3
    endloop
  endfacet
  facet normal 0.351776 0.936084 0
    outer loop
      vertex -7.36246 41.3582 3
      vertex -4.65913 40.3423 2.4
      vertex -7.36246 41.3582 2.4
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -4.65913 40.3423 2.4
      vertex -4.65913 41.0401 3
      vertex -4.65913 41.0401 2.4
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -4.65913 41.0401 3
      vertex -4.65913 40.3423 2.4
      vertex -4.65913 40.3423 3
    endloop
  endfacet
  facet normal -0.298842 -0.954303 0
    outer loop
      vertex -5.87196 41.4199 2.4
      vertex -4.65913 41.0401 3
      vertex -5.87196 41.4199 3
    endloop
  endfacet
  facet normal -0.298842 -0.954303 -0
    outer loop
      vertex -4.65913 41.0401 3
      vertex -5.87196 41.4199 2.4
      vertex -4.65913 41.0401 2.4
    endloop
  endfacet
  facet normal -0.266476 -0.963842 0
    outer loop
      vertex -6.4297 41.5741 2.4
      vertex -5.87196 41.4199 3
      vertex -6.4297 41.5741 3
    endloop
  endfacet
  facet normal -0.266476 -0.963842 -0
    outer loop
      vertex -5.87196 41.4199 3
      vertex -6.4297 41.5741 2.4
      vertex -5.87196 41.4199 2.4
    endloop
  endfacet
  facet normal -0.254747 -0.967008 0
    outer loop
      vertex -6.65518 41.6335 2.4
      vertex -6.4297 41.5741 3
      vertex -6.65518 41.6335 3
    endloop
  endfacet
  facet normal -0.254747 -0.967008 -0
    outer loop
      vertex -6.4297 41.5741 3
      vertex -6.65518 41.6335 2.4
      vertex -6.4297 41.5741 2.4
    endloop
  endfacet
  facet normal -0.269292 0.963059 0
    outer loop
      vertex -6.32974 41.7245 2.4
      vertex -6.65518 41.6335 3
      vertex -6.32974 41.7245 3
    endloop
  endfacet
  facet normal -0.269292 0.963059 0
    outer loop
      vertex -6.65518 41.6335 3
      vertex -6.32974 41.7245 2.4
      vertex -6.65518 41.6335 2.4
    endloop
  endfacet
  facet normal -0.289444 0.957195 0
    outer loop
      vertex -6.06551 41.8044 2.4
      vertex -6.32974 41.7245 3
      vertex -6.06551 41.8044 3
    endloop
  endfacet
  facet normal -0.289444 0.957195 0
    outer loop
      vertex -6.32974 41.7245 3
      vertex -6.06551 41.8044 2.4
      vertex -6.32974 41.7245 2.4
    endloop
  endfacet
  facet normal -0.320926 0.947104 0
    outer loop
      vertex -5.86247 41.8732 2.4
      vertex -6.06551 41.8044 3
      vertex -5.86247 41.8732 3
    endloop
  endfacet
  facet normal -0.320926 0.947104 0
    outer loop
      vertex -6.06551 41.8044 3
      vertex -5.86247 41.8732 2.4
      vertex -6.06551 41.8044 2.4
    endloop
  endfacet
  facet normal -0.31792 0.948118 0
    outer loop
      vertex -4.65913 42.2767 2.4
      vertex -5.86247 41.8732 3
      vertex -4.65913 42.2767 3
    endloop
  endfacet
  facet normal -0.31792 0.948118 0
    outer loop
      vertex -5.86247 41.8732 3
      vertex -4.65913 42.2767 2.4
      vertex -5.86247 41.8732 2.4
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -4.65913 42.2767 2.4
      vertex -4.65913 42.9816 3
      vertex -4.65913 42.9816 2.4
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex -4.65913 42.9816 3
      vertex -4.65913 42.2767 2.4
      vertex -4.65913 42.2767 3
    endloop
  endfacet
  facet normal 0.371083 -0.9286 0
    outer loop
      vertex -7.20107 41.9658 2.4
      vertex -4.65913 42.9816 3
      vertex -7.20107 41.9658 3
    endloop
  endfacet
  facet normal 0.371083 -0.9286 0
    outer loop
      vertex -4.65913 42.9816 3
      vertex -7.20107 41.9658 2.4
      vertex -4.65913 42.9816 2.4
    endloop
  endfacet
  facet normal -0.369682 -0.929158 0
    outer loop
      vertex -7.35112 42.0255 2.4
      vertex -7.20107 41.9658 3
      vertex -7.35112 42.0255 3
    endloop
  endfacet
  facet normal -0.369682 -0.929158 -0
    outer loop
      vertex -7.20107 41.9658 3
      vertex -7.35112 42.0255 2.4
      vertex -7.20107 41.9658 2.4
    endloop
  endfacet
  facet normal -0.427879 -0.903836 0
    outer loop
      vertex -7.46899 42.0813 2.4
      vertex -7.35112 42.0255 3
      vertex -7.46899 42.0813 3
    endloop
  endfacet
  facet normal -0.427879 -0.903836 -0
    outer loop
      vertex -7.35112 42.0255 3
      vertex -7.46899 42.0813 2.4
      vertex -7.35112 42.0255 2.4
    endloop
  endfacet
  facet normal -0.517239 -0.855841 0
    outer loop
      vertex -7.5547 42.1331 2.4
      vertex -7.46899 42.0813 3
      vertex -7.5547 42.1331 3
    endloop
  endfacet
  facet normal -0.517239 -0.855841 -0
    outer loop
      vertex -7.46899 42.0813 3
      vertex -7.5547 42.1331 2.4
      vertex -7.46899 42.0813 2.4
    endloop
  endfacet
  facet normal -0.635596 -0.772022 0
    outer loop
      vertex -7.61774 42.185 2.4
      vertex -7.5547 42.1331 3
      vertex -7.61774 42.185 3
    endloop
  endfacet
  facet normal -0.635596 -0.772022 -0
    outer loop
      vertex -7.5547 42.1331 3
      vertex -7.61774 42.185 2.4
      vertex -7.5547 42.1331 2.4
    endloop
  endfacet
  facet normal -0.748107 -0.663579 0
    outer loop
      vertex -7.61774 42.185 2.4
      vertex -7.66759 42.2412 3
      vertex -7.66759 42.2412 2.4
    endloop
  endfacet
  facet normal -0.748107 -0.663579 0
    outer loop
      vertex -7.66759 42.2412 3
      vertex -7.61774 42.185 2.4
      vertex -7.61774 42.185 3
    endloop
  endfacet
  facet normal -0.855048 -0.51855 0
    outer loop
      vertex -7.66759 42.2412 2.4
      vertex -7.70422 42.3016 3
      vertex -7.70422 42.3016 2.4
    endloop
  endfacet
  facet normal -0.855048 -0.51855 0
    outer loop
      vertex -7.70422 42.3016 3
      vertex -7.66759 42.2412 2.4
      vertex -7.66759 42.2412 3
    endloop
  endfacet
  facet normal -0.9381 -0.346365 0
    outer loop
      vertex -7.70422 42.3016 2.4
      vertex -7.72929 42.3695 3
      vertex -7.72929 42.3695 2.4
    endloop
  endfacet
  facet normal -0.9381 -0.346365 0
    outer loop
      vertex -7.72929 42.3695 3
      vertex -7.70422 42.3016 2.4
      vertex -7.70422 42.3016 3
    endloop
  endfacet
  facet normal -0.982202 -0.187829 0
    outer loop
      vertex -7.72929 42.3695 2.4
      vertex -7.74434 42.4482 3
      vertex -7.74434 42.4482 2.4
    endloop
  endfacet
  facet normal -0.982202 -0.187829 0
    outer loop
      vertex -7.74434 42.4482 3
      vertex -7.72929 42.3695 2.4
      vertex -7.72929 42.3695 3
    endloop
  endfacet
  facet normal -0.998447 -0.0557169 0
    outer loop
      vertex -7.74434 42.4482 2.4
      vertex -7.74934 42.5378 3
      vertex -7.74934 42.5378 2.4
    endloop
  endfacet
  facet normal -0.998447 -0.0557169 0
    outer loop
      vertex -7.74934 42.5378 3
      vertex -7.74434 42.4482 2.4
      vertex -7.74434 42.4482 3
    endloop
  endfacet
  facet normal -0.999575 0.0291543 0
    outer loop
      vertex -7.74934 42.5378 2.4
      vertex -7.74724 42.6098 3
      vertex -7.74724 42.6098 2.4
    endloop
  endfacet
  facet normal -0.999575 0.0291543 0
    outer loop
      vertex -7.74724 42.6098 3
      vertex -7.74934 42.5378 2.4
      vertex -7.74934 42.5378 3
    endloop
  endfacet
  facet normal -0.996612 0.0822497 0
    outer loop
      vertex -7.74724 42.6098 2.4
      vertex -7.74091 42.6865 3
      vertex -7.74091 42.6865 2.4
    endloop
  endfacet
  facet normal -0.996612 0.0822497 0
    outer loop
      vertex -7.74091 42.6865 3
      vertex -7.74724 42.6098 2.4
      vertex -7.74724 42.6098 3
    endloop
  endfacet
  facet normal -0.99171 0.128496 0
    outer loop
      vertex -7.74091 42.6865 2.4
      vertex -7.73035 42.768 3
      vertex -7.73035 42.768 2.4
    endloop
  endfacet
  facet normal -0.99171 0.128496 0
    outer loop
      vertex -7.73035 42.768 3
      vertex -7.74091 42.6865 2.4
      vertex -7.74091 42.6865 3
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -8.20505 42.768 2.4
      vertex -7.73035 42.768 3
      vertex -8.20505 42.768 3
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex -7.73035 42.768 3
      vertex -8.20505 42.768 2.4
      vertex -7.73035 42.768 2.4
    endloop
  endfacet
  facet normal 0.991022 -0.133698 0
    outer loop
      vertex -8.22217 42.6411 3
      vertex -8.20505 42.768 2.4
      vertex -8.20505 42.768 3
    endloop
  endfacet
  facet normal 0.991022 -0.133698 0
    outer loop
      vertex -8.20505 42.768 2.4
      vertex -8.22217 42.6411 3
      vertex -8.22217 42.6411 2.4
    endloop
  endfacet
  facet normal 0.997315 -0.0732314 0
    outer loop
      vertex -8.23245 42.5011 3
      vertex -8.22217 42.6411 2.4
      vertex -8.22217 42.6411 3
    endloop
  endfacet
  facet normal 0.997315 -0.0732314 0
    outer loop
      vertex -8.22217 42.6411 2.4
      vertex -8.23245 42.5011 3
      vertex -8.23245 42.5011 2.4
    endloop
  endfacet
  facet normal 0.999748 -0.0224486 0
    outer loop
      vertex -8.23589 42.3479 3
      vertex -8.23245 42.5011 2.4
      vertex -8.23245 42.5011 3
    endloop
  endfacet
  facet normal 0.999748 -0.0224486 0
    outer loop
      vertex -8.23245 42.5011 2.4
      vertex -8.23589 42.3479 3
      vertex -8.23589 42.3479 2.4
    endloop
  endfacet
  facet normal 0.995297 0.0968683 0
    outer loop
      vertex -8.21478 42.131 3
      vertex -8.23589 42.3479 2.4
      vertex -8.23589 42.3479 3
    endloop
  endfacet
  facet normal 0.995297 0.0968683 0
    outer loop
      vertex -8.23589 42.3479 2.4
      vertex -8.21478 42.131 3
      vertex -8.21478 42.131 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.27464 37.4194 2.4
      vertex 6.72058 37.4737 2.4
      vertex 6.81894 37.1797 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.42548 37.6501 2.4
      vertex 6.9222 38.1492 2.4
      vertex 6.6557 38.2909 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.9222 38.1492 2.4
      vertex 6.42548 37.6501 2.4
      vertex 6.72058 37.4737 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.32619 38.376 2.4
      vertex 6.42548 37.6501 2.4
      vertex 6.6557 38.2909 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.93367 37.7089 2.4
      vertex 6.32619 38.376 2.4
      vertex 5.93367 38.4043 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.32619 38.376 2.4
      vertex 5.93367 37.7089 2.4
      vertex 6.42548 37.6501 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.93367 38.4043 2.4
      vertex 5.66759 37.6947 2.4
      vertex 5.93367 37.7089 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.54456 38.3773 2.4
      vertex 5.66759 37.6947 2.4
      vertex 5.93367 38.4043 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.54456 38.3773 2.4
      vertex 5.45161 37.652 2.4
      vertex 5.66759 37.6947 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.21901 38.2962 2.4
      vertex 5.45161 37.652 2.4
      vertex 5.54456 38.3773 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.95703 38.161 2.4
      vertex 5.45161 37.652 2.4
      vertex 5.21901 38.2962 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.45161 37.652 2.4
      vertex 4.95703 38.161 2.4
      vertex 5.28575 37.5808 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.76517 37.9753 2.4
      vertex 5.28575 37.5808 2.4
      vertex 4.95703 38.161 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.28575 37.5808 2.4
      vertex 4.76517 37.9753 2.4
      vertex 5.16838 37.4798 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.65005 37.7423 2.4
      vertex 5.16838 37.4798 2.4
      vertex 4.76517 37.9753 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.72058 37.4737 2.4
      vertex 7.27464 37.4194 2.4
      vertex 7.23547 37.7114 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.27464 37.4194 2.4
      vertex 6.81894 37.1797 2.4
      vertex 7.26146 37.2456 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.26146 37.2456 2.4
      vertex 6.81894 37.1797 2.4
      vertex 7.22191 37.0882 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.72058 37.4737 2.4
      vertex 7.23547 37.7114 2.4
      vertex 7.118 37.9547 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22191 37.0882 2.4
      vertex 6.81894 37.1797 2.4
      vertex 7.15599 36.9471 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.79362 37.0139 2.4
      vertex 7.15599 36.9471 2.4
      vertex 6.81894 37.1797 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.72058 37.4737 2.4
      vertex 7.118 37.9547 2.4
      vertex 6.9222 38.1492 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.15599 36.9471 2.4
      vertex 6.79362 37.0139 2.4
      vertex 7.06526 36.8244 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.06526 36.8244 2.4
      vertex 6.79362 37.0139 2.4
      vertex 6.95134 36.7224 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.95134 36.7224 2.4
      vertex 6.71767 36.8774 2.4
      vertex 6.81421 36.6409 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.71767 36.8774 2.4
      vertex 6.95134 36.7224 2.4
      vertex 6.79362 37.0139 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.06393 35.9655 2.4
      vertex 7.22717 36.6029 2.4
      vertex 7.18867 36.6107 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.06393 35.9655 2.4
      vertex 7.18867 36.6107 2.4
      vertex 7.12697 36.6182 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22717 36.6029 2.4
      vertex 7.06393 35.9655 2.4
      vertex 7.22717 35.955 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.04207 36.6255 2.4
      vertex 7.06393 35.9655 2.4
      vertex 7.12697 36.6182 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.95239 36.6314 2.4
      vertex 7.06393 35.9655 2.4
      vertex 7.04207 36.6255 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.86852 35.9718 2.4
      vertex 6.95239 36.6314 2.4
      vertex 6.87645 36.635 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.95239 36.6314 2.4
      vertex 6.86852 35.9718 2.4
      vertex 7.06393 35.9655 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.81421 36.6361 2.4
      vertex 6.86852 35.9718 2.4
      vertex 6.87645 36.635 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.59109 36.7702 2.4
      vertex 6.81421 36.6409 2.4
      vertex 6.71767 36.8774 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.81421 36.6409 2.4
      vertex 6.59109 36.7702 2.4
      vertex 6.81421 36.6361 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.41914 36.6931 2.4
      vertex 6.81421 36.6361 2.4
      vertex 6.59109 36.7702 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.81421 36.6361 2.4
      vertex 6.64093 35.9739 2.4
      vertex 6.86852 35.9718 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.81421 36.6361 2.4
      vertex 6.41914 36.6931 2.4
      vertex 6.64093 35.9739 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.20712 36.6468 2.4
      vertex 6.64093 35.9739 2.4
      vertex 6.41914 36.6931 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.95502 36.6314 2.4
      vertex 6.64093 35.9739 2.4
      vertex 6.20712 36.6468 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.69249 36.6471 2.4
      vertex 6.64093 35.9739 2.4
      vertex 5.95502 36.6314 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.10536 36.6314 2.4
      vertex 5.69249 36.6471 2.4
      vertex 5.47453 36.6942 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.10536 36.6314 2.4
      vertex 5.47453 36.6942 2.4
      vertex 5.30115 36.7726 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.10536 36.6409 2.4
      vertex 5.30115 36.7726 2.4
      vertex 5.17522 36.8811 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.10536 36.6314 2.4
      vertex 5.30115 36.7726 2.4
      vertex 5.10536 36.6409 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.69249 36.6471 2.4
      vertex 5.10536 36.6314 2.4
      vertex 6.64093 35.9739 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.705 35.9739 2.4
      vertex 5.10536 36.6314 2.4
      vertex 4.68764 36.6409 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.705 35.9739 2.4
      vertex 4.68764 36.6409 2.4
      vertex 3.705 36.6409 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.10536 36.6314 2.4
      vertex 3.705 35.9739 2.4
      vertex 6.64093 35.9739 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.83109 36.8324 2.4
      vertex 5.17522 36.8811 2.4
      vertex 5.09967 37.0184 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.66653 37.1061 2.4
      vertex 5.09967 37.0184 2.4
      vertex 5.07448 37.1844 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.61168 37.4621 2.4
      vertex 5.16838 37.4798 2.4
      vertex 4.65005 37.7423 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.09796 37.3476 2.4
      vertex 4.66653 37.1061 2.4
      vertex 5.07448 37.1844 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.16838 37.4798 2.4
      vertex 4.61168 37.4621 2.4
      vertex 5.09796 37.3476 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.09967 37.0184 2.4
      vertex 4.66653 37.1061 2.4
      vertex 4.83109 36.8324 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.66653 37.1061 2.4
      vertex 5.09796 37.3476 2.4
      vertex 4.61168 37.4621 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.17522 36.8811 2.4
      vertex 4.83109 36.8324 2.4
      vertex 5.10536 36.6409 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.48285 32.7766 2.4
      vertex 4.93207 32.2837 2.4
      vertex 4.76358 32.9008 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 32.2837 2.4
      vertex 4.48285 32.7766 2.4
      vertex 4.77582 32.2148 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.25145 32.6033 2.4
      vertex 4.77582 32.2148 2.4
      vertex 4.48285 32.7766 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.77582 32.2148 2.4
      vertex 4.25145 32.6033 2.4
      vertex 4.64252 32.1123 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.06935 32.381 2.4
      vertex 4.64252 32.1123 2.4
      vertex 4.25145 32.6033 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.64252 32.1123 2.4
      vertex 4.06935 32.381 2.4
      vertex 4.53217 31.9764 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 3.93814 32.1099 2.4
      vertex 4.53217 31.9764 2.4
      vertex 4.06935 32.381 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.53217 31.9764 2.4
      vertex 3.93814 32.1099 2.4
      vertex 4.44975 31.8146 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.85942 31.7903 2.4
      vertex 4.44975 31.8146 2.4
      vertex 3.93814 32.1099 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.44975 31.8146 2.4
      vertex 3.85942 31.7903 2.4
      vertex 4.40031 31.6346 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 3.88223 30.9267 2.4
      vertex 4.38383 31.4364 2.4
      vertex 3.83318 31.4222 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.83318 31.4222 2.4
      vertex 4.40031 31.6346 2.4
      vertex 3.85942 31.7903 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.02937 30.516 2.4
      vertex 4.38383 31.4364 2.4
      vertex 3.88223 30.9267 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.40031 31.6346 2.4
      vertex 3.83318 31.4222 2.4
      vertex 4.38383 31.4364 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.38383 31.4364 2.4
      vertex 4.02937 30.516 2.4
      vertex 4.27463 30.1903 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.72401 31.453 2.4
      vertex 7.27464 31.453 2.4
      vertex 7.2484 31.7907 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.65335 31.8325 2.4
      vertex 7.2484 31.7907 2.4
      vertex 7.16969 32.0949 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.69026 31.1599 2.4
      vertex 7.27464 31.453 2.4
      vertex 6.72401 31.453 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.65335 31.8325 2.4
      vertex 7.16969 32.0949 2.4
      vertex 7.0385 32.3656 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.44131 32.126 2.4
      vertex 7.0385 32.3656 2.4
      vertex 6.8535 32.5992 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.27464 31.453 2.4
      vertex 6.69026 31.1599 2.4
      vertex 7.22388 30.9558 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.589 30.9167 2.4
      vertex 7.22388 30.9558 2.4
      vertex 6.69026 31.1599 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.2484 31.7907 2.4
      vertex 6.65335 31.8325 2.4
      vertex 6.72401 31.453 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.44131 32.126 2.4
      vertex 6.8535 32.5992 2.4
      vertex 6.61339 32.7918 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.0385 32.3656 2.4
      vertex 6.44131 32.126 2.4
      vertex 6.65335 31.8325 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 32.3336 2.4
      vertex 6.61339 32.7918 2.4
      vertex 6.31816 32.9435 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.61339 32.7918 2.4
      vertex 6.08794 32.3336 2.4
      vertex 6.44131 32.126 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22388 30.9558 2.4
      vertex 6.589 30.9167 2.4
      vertex 7.07158 30.5401 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.42023 30.7232 2.4
      vertex 7.07158 30.5401 2.4
      vertex 6.589 30.9167 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.07158 30.5401 2.4
      vertex 6.42023 30.7232 2.4
      vertex 6.81775 30.2058 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.18736 30.5828 2.4
      vertex 6.81775 30.2058 2.4
      vertex 6.42023 30.7232 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.81775 30.2058 2.4
      vertex 6.18736 30.5828 2.4
      vertex 6.47267 29.9612 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.18736 30.5828 2.4
      vertex 6.04665 29.8144 2.4
      vertex 6.47267 29.9612 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.89384 30.4985 2.4
      vertex 6.04665 29.8144 2.4
      vertex 6.18736 30.5828 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.53967 29.7655 2.4
      vertex 5.89384 30.4985 2.4
      vertex 5.53967 30.4704 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.89384 30.4985 2.4
      vertex 5.53967 29.7655 2.4
      vertex 6.04665 29.8144 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.19183 30.4977 2.4
      vertex 5.53967 29.7655 2.4
      vertex 5.53967 30.4704 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.19183 30.4977 2.4
      vertex 5.03307 29.8127 2.4
      vertex 5.53967 29.7655 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.90466 30.5796 2.4
      vertex 5.03307 29.8127 2.4
      vertex 5.19183 30.4977 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 30.1903 2.4
      vertex 4.90466 30.5796 2.4
      vertex 4.67815 30.7161 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.90466 30.5796 2.4
      vertex 4.61139 29.9543 2.4
      vertex 5.03307 29.8127 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 30.1903 2.4
      vertex 4.67815 30.7161 2.4
      vertex 4.51463 30.9053 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 30.1903 2.4
      vertex 4.51463 30.9053 2.4
      vertex 4.41653 31.1454 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.90466 30.5796 2.4
      vertex 4.27463 30.1903 2.4
      vertex 4.61139 29.9543 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 30.1903 2.4
      vertex 4.41653 31.1454 2.4
      vertex 4.38383 31.4364 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.40016 46.1611 2.4
      vertex 4.76358 45.5671 2.4
      vertex 4.67101 46.2459 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.76358 45.5671 2.4
      vertex 4.40016 46.1611 2.4
      vertex 4.63145 45.5203 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.18576 46.027 2.4
      vertex 4.63145 45.5203 2.4
      vertex 4.40016 46.1611 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.63145 45.5203 2.4
      vertex 4.18576 46.027 2.4
      vertex 4.52307 45.4495 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.02782 45.8436 2.4
      vertex 4.52307 45.4495 2.4
      vertex 4.18576 46.027 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.52307 45.4495 2.4
      vertex 4.02782 45.8436 2.4
      vertex 4.43843 45.3547 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 3.91968 45.6011 2.4
      vertex 4.43843 45.3547 2.4
      vertex 4.02782 45.8436 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.43843 45.3547 2.4
      vertex 3.91968 45.6011 2.4
      vertex 4.37776 45.2325 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 3.8548 45.2898 2.4
      vertex 4.37776 45.2325 2.4
      vertex 3.91968 45.6011 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 3.85994 44.5105 2.4
      vertex 4.32922 44.8954 2.4
      vertex 3.83318 44.9097 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.37776 45.2325 2.4
      vertex 3.8548 45.2898 2.4
      vertex 4.34137 45.0794 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 3.94025 44.1802 2.4
      vertex 4.32922 44.8954 2.4
      vertex 3.85994 44.5105 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.83318 44.9097 2.4
      vertex 4.34137 45.0794 2.4
      vertex 3.8548 45.2898 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.07408 43.9188 2.4
      vertex 4.32922 44.8954 2.4
      vertex 3.94025 44.1802 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.34137 45.0794 2.4
      vertex 3.83318 44.9097 2.4
      vertex 4.32922 44.8954 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.32922 44.8954 2.4
      vertex 4.07408 43.9188 2.4
      vertex 4.25829 43.7296 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.24576 45.3323 2.4
      vertex 6.70055 45.3266 2.4
      vertex 6.75014 44.9192 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.55182 45.5711 2.4
      vertex 6.81578 46.1718 2.4
      vertex 6.56538 46.2932 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.01477 45.9694 2.4
      vertex 6.55182 45.5711 2.4
      vertex 6.70055 45.3266 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.56538 46.2932 2.4
      vertex 6.30391 45.6526 2.4
      vertex 6.55182 45.5711 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.26357 46.3337 2.4
      vertex 6.30391 45.6526 2.4
      vertex 6.56538 46.2932 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.26357 46.3337 2.4
      vertex 6.21451 45.6432 2.4
      vertex 6.30391 45.6526 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.12973 46.3266 2.4
      vertex 6.21451 45.6432 2.4
      vertex 6.26357 46.3337 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.00673 46.3053 2.4
      vertex 6.21451 45.6432 2.4
      vertex 6.12973 46.3266 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.21451 45.6432 2.4
      vertex 6.00673 46.3053 2.4
      vertex 6.1362 45.6151 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.89453 46.2697 2.4
      vertex 6.1362 45.6151 2.4
      vertex 6.00673 46.3053 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.79272 46.2206 2.4
      vertex 6.1362 45.6151 2.4
      vertex 5.89453 46.2697 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.70094 46.1589 2.4
      vertex 6.1362 45.6151 2.4
      vertex 5.79272 46.2206 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.1362 45.6151 2.4
      vertex 5.70094 46.1589 2.4
      vertex 6.06895 45.5683 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.61919 46.0845 2.4
      vertex 6.06895 45.5683 2.4
      vertex 5.70094 46.1589 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.54561 45.9942 2.4
      vertex 6.06895 45.5683 2.4
      vertex 5.61919 46.0845 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.47836 45.8846 2.4
      vertex 6.06895 45.5683 2.4
      vertex 5.54561 45.9942 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.06895 45.5683 2.4
      vertex 5.47836 45.8846 2.4
      vertex 6.01067 45.5045 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.41745 45.7558 2.4
      vertex 6.01067 45.5045 2.4
      vertex 5.47836 45.8846 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.29509 45.3571 2.4
      vertex 5.91469 45.3309 2.4
      vertex 5.35799 45.5869 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.01067 45.5045 2.4
      vertex 5.41745 45.7558 2.4
      vertex 5.95926 45.4254 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.87065 45.1976 2.4
      vertex 5.29509 45.3571 2.4
      vertex 5.8208 45.0018 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.8208 45.0018 2.4
      vertex 5.22876 45.0663 2.4
      vertex 5.76514 44.7435 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.35799 45.5869 2.4
      vertex 5.95926 45.4254 2.4
      vertex 5.41745 45.7558 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.17352 44.8261 2.4
      vertex 5.76514 44.7435 2.4
      vertex 5.22876 45.0663 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.95926 45.4254 2.4
      vertex 5.35799 45.5869 2.4
      vertex 5.91469 45.3309 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.76514 44.7435 2.4
      vertex 5.17352 44.8261 2.4
      vertex 5.71042 44.5188 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.12486 44.6465 2.4
      vertex 5.71042 44.5188 2.4
      vertex 5.17352 44.8261 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.91469 45.3309 2.4
      vertex 5.29509 45.3571 2.4
      vertex 5.87065 45.1976 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.71042 44.5188 2.4
      vertex 5.12486 44.6465 2.4
      vertex 5.66336 44.3448 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.22876 45.0663 2.4
      vertex 5.8208 45.0018 2.4
      vertex 5.29509 45.3571 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.08281 44.5275 2.4
      vertex 5.66336 44.3448 2.4
      vertex 5.12486 44.6465 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.66336 44.3448 2.4
      vertex 5.08281 44.5275 2.4
      vertex 5.62395 44.2213 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.04128 44.4462 2.4
      vertex 5.62395 44.2213 2.4
      vertex 5.08281 44.5275 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.62395 44.2213 2.4
      vertex 5.04128 44.4462 2.4
      vertex 5.58624 44.1264 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.9942 44.3793 2.4
      vertex 5.58624 44.1264 2.4
      vertex 5.04128 44.4462 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.58624 44.1264 2.4
      vertex 4.9942 44.3793 2.4
      vertex 5.54431 44.0378 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.54431 44.0378 2.4
      vertex 4.9942 44.3793 2.4
      vertex 5.49815 43.9555 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.94159 44.327 2.4
      vertex 5.49815 43.9555 2.4
      vertex 4.9942 44.3793 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.49815 43.9555 2.4
      vertex 4.94159 44.327 2.4
      vertex 5.44659 43.8804 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.44659 43.8804 2.4
      vertex 4.94159 44.327 2.4
      vertex 5.38843 43.8131 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.38843 43.8131 2.4
      vertex 4.94159 44.327 2.4
      vertex 5.32368 43.7538 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.88092 44.2894 2.4
      vertex 5.32368 43.7538 2.4
      vertex 4.94159 44.327 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.32368 43.7538 2.4
      vertex 4.88092 44.2894 2.4
      vertex 5.25169 43.7025 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.25169 43.7025 2.4
      vertex 4.88092 44.2894 2.4
      vertex 5.17178 43.6594 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.17178 43.6594 2.4
      vertex 4.88092 44.2894 2.4
      vertex 5.08397 43.6245 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.80971 44.2669 2.4
      vertex 5.08397 43.6245 2.4
      vertex 4.88092 44.2894 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.08397 43.6245 2.4
      vertex 4.80971 44.2669 2.4
      vertex 4.98772 43.5987 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.98772 43.5987 2.4
      vertex 4.80971 44.2669 2.4
      vertex 4.88249 43.5833 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.80971 44.2669 2.4
      vertex 4.76831 43.5782 2.4
      vertex 4.88249 43.5833 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.72795 44.2594 2.4
      vertex 4.76831 43.5782 2.4
      vertex 4.80971 44.2669 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.25829 43.7296 2.4
      vertex 4.72795 44.2594 2.4
      vertex 4.50644 44.33 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.72795 44.2594 2.4
      vertex 4.4897 43.616 2.4
      vertex 4.76831 43.5782 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.25829 43.7296 2.4
      vertex 4.50644 44.33 2.4
      vertex 4.37354 44.5421 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.72795 44.2594 2.4
      vertex 4.25829 43.7296 2.4
      vertex 4.4897 43.616 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.25829 43.7296 2.4
      vertex 4.37354 44.5421 2.4
      vertex 4.32922 44.8954 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.75014 44.9192 2.4
      vertex 7.27464 44.9002 2.4
      vertex 7.24576 45.3323 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.73682 44.7005 2.4
      vertex 7.27464 44.9002 2.4
      vertex 6.75014 44.9192 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.70055 45.3266 2.4
      vertex 7.24576 45.3323 2.4
      vertex 7.15913 45.6887 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.27464 44.9002 2.4
      vertex 6.73682 44.7005 2.4
      vertex 7.24933 44.5022 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.70055 45.3266 2.4
      vertex 7.15913 45.6887 2.4
      vertex 7.01477 45.9694 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.69687 44.5162 2.4
      vertex 7.24933 44.5022 2.4
      vertex 6.73682 44.7005 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.55182 45.5711 2.4
      vertex 7.01477 45.9694 2.4
      vertex 6.81578 46.1718 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.24933 44.5022 2.4
      vertex 6.69687 44.5162 2.4
      vertex 7.17337 44.166 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.63029 44.3661 2.4
      vertex 7.17337 44.166 2.4
      vertex 6.69687 44.5162 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.17337 44.166 2.4
      vertex 6.63029 44.3661 2.4
      vertex 7.04678 43.8915 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.53415 44.2477 2.4
      vertex 7.04678 43.8915 2.4
      vertex 6.63029 44.3661 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.04678 43.8915 2.4
      vertex 6.53415 44.2477 2.4
      vertex 6.86879 43.6768 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.40559 44.1583 2.4
      vertex 6.86879 43.6768 2.4
      vertex 6.53415 44.2477 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.86879 43.6768 2.4
      vertex 6.40559 44.1583 2.4
      vertex 6.63857 43.5202 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.24458 44.098 2.4
      vertex 6.63857 43.5202 2.4
      vertex 6.40559 44.1583 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.63857 43.5202 2.4
      vertex 6.24458 44.098 2.4
      vertex 6.35614 43.4215 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.48285 43.0637 2.4
      vertex 4.93207 42.5708 2.4
      vertex 4.76358 43.1879 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.93207 42.5708 2.4
      vertex 4.48285 43.0637 2.4
      vertex 4.77582 42.5019 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.25145 42.8904 2.4
      vertex 4.77582 42.5019 2.4
      vertex 4.48285 43.0637 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.77582 42.5019 2.4
      vertex 4.25145 42.8904 2.4
      vertex 4.64252 42.3994 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 4.06935 42.6681 2.4
      vertex 4.64252 42.3994 2.4
      vertex 4.25145 42.8904 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.64252 42.3994 2.4
      vertex 4.06935 42.6681 2.4
      vertex 4.53217 42.2635 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 3.93814 42.397 2.4
      vertex 4.53217 42.2635 2.4
      vertex 4.06935 42.6681 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.53217 42.2635 2.4
      vertex 3.93814 42.397 2.4
      vertex 4.44975 42.1017 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.85942 42.0774 2.4
      vertex 4.44975 42.1017 2.4
      vertex 3.93814 42.397 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.44975 42.1017 2.4
      vertex 3.85942 42.0774 2.4
      vertex 4.40031 41.9217 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 3.88223 41.2137 2.4
      vertex 4.38383 41.7235 2.4
      vertex 3.83318 41.7092 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 3.83318 41.7092 2.4
      vertex 4.40031 41.9217 2.4
      vertex 3.85942 42.0774 2.4
    endloop
  endfacet
  facet normal 0 -0 1
    outer loop
      vertex 4.02937 40.8031 2.4
      vertex 4.38383 41.7235 2.4
      vertex 3.88223 41.2137 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.40031 41.9217 2.4
      vertex 3.83318 41.7092 2.4
      vertex 4.38383 41.7235 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.38383 41.7235 2.4
      vertex 4.02937 40.8031 2.4
      vertex 4.27463 40.4774 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.72401 41.7401 2.4
      vertex 7.27464 41.7401 2.4
      vertex 7.2484 42.0778 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.65335 42.1196 2.4
      vertex 7.2484 42.0778 2.4
      vertex 7.16969 42.382 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.69026 41.447 2.4
      vertex 7.27464 41.7401 2.4
      vertex 6.72401 41.7401 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.65335 42.1196 2.4
      vertex 7.16969 42.382 2.4
      vertex 7.0385 42.6527 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.44131 42.4131 2.4
      vertex 7.0385 42.6527 2.4
      vertex 6.8535 42.8862 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.27464 41.7401 2.4
      vertex 6.69026 41.447 2.4
      vertex 7.22388 41.2429 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.589 41.2037 2.4
      vertex 7.22388 41.2429 2.4
      vertex 6.69026 41.447 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.2484 42.0778 2.4
      vertex 6.65335 42.1196 2.4
      vertex 6.72401 41.7401 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.44131 42.4131 2.4
      vertex 6.8535 42.8862 2.4
      vertex 6.61339 43.0789 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.0385 42.6527 2.4
      vertex 6.44131 42.4131 2.4
      vertex 6.65335 42.1196 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.08794 42.6207 2.4
      vertex 6.61339 43.0789 2.4
      vertex 6.31816 43.2306 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.61339 43.0789 2.4
      vertex 6.08794 42.6207 2.4
      vertex 6.44131 42.4131 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22388 41.2429 2.4
      vertex 6.589 41.2037 2.4
      vertex 7.07158 40.8271 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.42023 41.0103 2.4
      vertex 7.07158 40.8271 2.4
      vertex 6.589 41.2037 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.07158 40.8271 2.4
      vertex 6.42023 41.0103 2.4
      vertex 6.81775 40.4929 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.18736 40.8699 2.4
      vertex 6.81775 40.4929 2.4
      vertex 6.42023 41.0103 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.81775 40.4929 2.4
      vertex 6.18736 40.8699 2.4
      vertex 6.47267 40.2483 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 6.18736 40.8699 2.4
      vertex 6.04665 40.1015 2.4
      vertex 6.47267 40.2483 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.89384 40.7856 2.4
      vertex 6.04665 40.1015 2.4
      vertex 6.18736 40.8699 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.53967 40.0526 2.4
      vertex 5.89384 40.7856 2.4
      vertex 5.53967 40.7575 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.89384 40.7856 2.4
      vertex 5.53967 40.0526 2.4
      vertex 6.04665 40.1015 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.19183 40.7848 2.4
      vertex 5.53967 40.0526 2.4
      vertex 5.53967 40.7575 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.19183 40.7848 2.4
      vertex 5.03307 40.0998 2.4
      vertex 5.53967 40.0526 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.90466 40.8667 2.4
      vertex 5.03307 40.0998 2.4
      vertex 5.19183 40.7848 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 40.4774 2.4
      vertex 4.90466 40.8667 2.4
      vertex 4.67815 41.0032 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.90466 40.8667 2.4
      vertex 4.61139 40.2414 2.4
      vertex 5.03307 40.0998 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 40.4774 2.4
      vertex 4.67815 41.0032 2.4
      vertex 4.51463 41.1924 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 40.4774 2.4
      vertex 4.51463 41.1924 2.4
      vertex 4.41653 41.4325 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.90466 40.8667 2.4
      vertex 4.27463 40.4774 2.4
      vertex 4.61139 40.2414 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.27463 40.4774 2.4
      vertex 4.41653 41.4325 2.4
      vertex 4.38383 41.7235 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 3.88301 39.5596 2.4
      vertex 7.22717 38.8595 2.4
      vertex 7.22717 39.5596 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.22717 38.8595 2.4
      vertex 3.88301 39.5596 2.4
      vertex 3.88301 38.8595 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.23245 33.5129 2.4
      vertex 7.74434 33.5658 2.4
      vertex 7.74934 33.4762 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.04601 34.2321 2.4
      vertex 7.72929 33.6445 2.4
      vertex 7.74434 33.5658 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.04601 34.2321 2.4
      vertex 7.70422 33.7124 2.4
      vertex 7.72929 33.6445 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.04601 34.2321 2.4
      vertex 7.66759 33.7728 2.4
      vertex 7.70422 33.7124 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.46899 33.9327 2.4
      vertex 7.88567 34.3768 2.4
      vertex 7.65782 34.518 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.04601 34.2321 2.4
      vertex 7.61774 33.8289 2.4
      vertex 7.66759 33.7728 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.04601 34.2321 2.4
      vertex 7.5547 33.8809 2.4
      vertex 7.61774 33.8289 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.88567 34.3768 2.4
      vertex 7.46899 33.9327 2.4
      vertex 7.5547 33.8809 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.20107 34.0482 2.4
      vertex 7.65782 34.518 2.4
      vertex 7.36246 34.6558 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.65782 34.518 2.4
      vertex 7.35112 33.9885 2.4
      vertex 7.46899 33.9327 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.65782 34.518 2.4
      vertex 7.20107 34.0482 2.4
      vertex 7.35112 33.9885 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.36246 34.6558 2.4
      vertex 6.65518 34.3805 2.4
      vertex 7.20107 34.0482 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.36246 34.6558 2.4
      vertex 6.4297 34.4398 2.4
      vertex 6.65518 34.3805 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.36246 34.6558 2.4
      vertex 5.87196 34.5941 2.4
      vertex 6.4297 34.4398 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.65913 35.6717 2.4
      vertex 5.87196 34.5941 2.4
      vertex 7.36246 34.6558 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.87196 34.5941 2.4
      vertex 4.65913 35.6717 2.4
      vertex 4.65913 34.9739 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.74434 33.5658 2.4
      vertex 8.23245 33.5129 2.4
      vertex 8.23589 33.6661 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74434 33.5658 2.4
      vertex 8.23589 33.6661 2.4
      vertex 8.21478 33.883 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.23245 33.5129 2.4
      vertex 7.74934 33.4762 2.4
      vertex 8.22217 33.3728 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74434 33.5658 2.4
      vertex 8.21478 33.883 2.4
      vertex 8.15149 34.0717 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74434 33.5658 2.4
      vertex 8.15149 34.0717 2.4
      vertex 8.04601 34.2321 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.5547 33.8809 2.4
      vertex 8.04601 34.2321 2.4
      vertex 7.88567 34.3768 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 7.74724 33.4042 2.4
      vertex 8.22217 33.3728 2.4
      vertex 7.74934 33.4762 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 7.74091 33.3275 2.4
      vertex 8.22217 33.3728 2.4
      vertex 7.74724 33.4042 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.22217 33.3728 2.4
      vertex 7.74091 33.3275 2.4
      vertex 8.20505 33.246 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 8.20505 33.246 2.4
      vertex 7.74091 33.3275 2.4
      vertex 7.73035 33.246 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.32974 34.2895 2.4
      vertex 7.20107 34.0482 2.4
      vertex 6.65518 34.3805 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 6.06551 34.2096 2.4
      vertex 7.20107 34.0482 2.4
      vertex 6.32974 34.2895 2.4
    endloop
  endfacet
  facet normal -0 0 1
    outer loop
      vertex 5.86247 34.1408 2.4
      vertex 7.20107 34.0482 2.4
      vertex 6.06551 34.2096 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 4.65913 33.0324 2.4
      vertex 5.86247 34.1408 2.4
      vertex 4.65913 33.7373 2.4
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 5.86247 34.1408 2.4
      vertex 4.65913 33.0324 2.4
      vertex 7.20107 34.0482 2.4
    endloop
  endfacet
  facet normal -0.90053 -0.434794 0
    outer loop
      vertex 7.23547 37.7114 2.4
      vertex 7.118 37.9547 3
      vertex 7.118 37.9547 2.4
    endloop
  endfacet
  facet normal -0.90053 -0.434794 0
    outer loop
      vertex 7.118 37.9547 3
      vertex 7.23547 37.7114 2.4
      vertex 7.23547 37.7114 3
    endloop
  endfacet
  facet normal -0.704748 -0.709458 0
    outer loop
      vertex 6.9222 38.1492 2.4
      vertex 7.118 37.9547 3
      vertex 6.9222 38.1492 3
    endloop
  endfacet
  facet normal -0.704748 -0.709458 -0
    outer loop
      vertex 7.118 37.9547 3
      vertex 6.9222 38.1492 2.4
      vertex 7.118 37.9547 2.4
    endloop
  endfacet
  facet normal -0.46947 -0.882948 0
    outer loop
      vertex 6.6557 38.2909 2.4
      vertex 6.9222 38.1492 3
      vertex 6.6557 38.2909 3
    endloop
  endfacet
  facet normal -0.46947 -0.882948 -0
    outer loop
      vertex 6.9222 38.1492 3
      vertex 6.6557 38.2909 2.4
      vertex 6.9222 38.1492 2.4
    endloop
  endfacet
  facet normal -0.250058 -0.968231 0
    outer loop
      vertex 6.32619 38.376 2.4
      vertex 6.6557 38.2909 3
      vertex 6.32619 38.376 3
    endloop
  endfacet
  facet normal -0.250058 -0.968231 -0
    outer loop
      vertex 6.6557 38.2909 3
      vertex 6.32619 38.376 2.4
      vertex 6.6557 38.2909 2.4
    endloop
  endfacet
  facet normal -0.0719116 -0.997411 0
    outer loop
      vertex 5.93367 38.4043 2.4
      vertex 6.32619 38.376 3
      vertex 5.93367 38.4043 3
    endloop
  endfacet
  facet normal -0.0719116 -0.997411 -0
    outer loop
      vertex 6.32619 38.376 3
      vertex 5.93367 38.4043 2.4
      vertex 6.32619 38.376 2.4
    endloop
  endfacet
  facet normal 0.0692227 -0.997601 0
    outer loop
      vertex 5.54456 38.3773 2.4
      vertex 5.93367 38.4043 3
      vertex 5.54456 38.3773 3
    endloop
  endfacet
  facet normal 0.0692227 -0.997601 0
    outer loop
      vertex 5.93367 38.4043 3
      vertex 5.54456 38.3773 2.4
      vertex 5.93367 38.4043 2.4
    endloop
  endfacet
  facet normal 0.241729 -0.970344 0
    outer loop
      vertex 5.21901 38.2962 2.4
      vertex 5.54456 38.3773 3
      vertex 5.21901 38.2962 3
    endloop
  endfacet
  facet normal 0.241729 -0.970344 0
    outer loop
      vertex 5.54456 38.3773 3
      vertex 5.21901 38.2962 2.4
      vertex 5.54456 38.3773 2.4
    endloop
  endfacet
  facet normal 0.458601 -0.888642 0
    outer loop
      vertex 4.95703 38.161 2.4
      vertex 5.21901 38.2962 3
      vertex 4.95703 38.161 3
    endloop
  endfacet
  facet normal 0.458601 -0.888642 0
    outer loop
      vertex 5.21901 38.2962 3
      vertex 4.95703 38.161 2.4
      vertex 5.21901 38.2962 2.4
    endloop
  endfacet
  facet normal 0.695478 -0.718548 0
    outer loop
      vertex 4.76517 37.9753 2.4
      vertex 4.95703 38.161 3
      vertex 4.76517 37.9753 3
    endloop
  endfacet
  facet normal 0.695478 -0.718548 0
    outer loop
      vertex 4.95703 38.161 3
      vertex 4.76517 37.9753 2.4
      vertex 4.95703 38.161 2.4
    endloop
  endfacet
  facet normal 0.896541 -0.442961 0
    outer loop
      vertex 4.65005 37.7423 3
      vertex 4.76517 37.9753 2.4
      vertex 4.76517 37.9753 3
    endloop
  endfacet
  facet normal 0.896541 -0.442961 0
    outer loop
      vertex 4.76517 37.9753 2.4
      vertex 4.65005 37.7423 3
      vertex 4.65005 37.7423 2.4
    endloop
  endfacet
  facet normal 0.990754 -0.135672 0
    outer loop
      vertex 4.61168 37.4621 3
      vertex 4.65005 37.7423 2.4
      vertex 4.65005 37.7423 3
    endloop
  endfacet
  facet normal 0.990754 -0.135672 0
    outer loop
      vertex 4.65005 37.7423 2.4
      vertex 4.61168 37.4621 3
      vertex 4.61168 37.4621 2.4
    endloop
  endfacet
  facet normal 0.988338 0.152276 0
    outer loop
      vertex 4.66653 37.1061 3
      vertex 4.61168 37.4621 2.4
      vertex 4.61168 37.4621 3
    endloop
  endfacet
  facet normal 0.988338 0.152276 0
    outer loop
      vertex 4.61168 37.4621 2.4
      vertex 4.66653 37.1061 3
      vertex 4.66653 37.1061 2.4
    endloop
  endfacet
  facet normal 0.857023 0.515278 0
    outer loop
      vertex 4.83109 36.8324 3
      vertex 4.66653 37.1061 2.4
      vertex 4.66653 37.1061 3
    endloop
  endfacet
  facet normal 0.857023 0.515278 0
    outer loop
      vertex 4.66653 37.1061 2.4
      vertex 4.83109 36.8324 3
      vertex 4.83109 36.8324 2.4
    endloop
  endfacet
  facet normal 0.572481 0.819918 -0
    outer loop
      vertex 5.10536 36.6409 2.4
      vertex 4.83109 36.8324 3
      vertex 5.10536 36.6409 3
    endloop
  endfacet
  facet normal 0.572481 0.819918 0
    outer loop
      vertex 4.83109 36.8324 3
      vertex 5.10536 36.6409 2.4
      vertex 4.83109 36.8324 2.4
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 5.10536 36.6314 3
      vertex 5.10536 36.6409 2.4
      vertex 5.10536 36.6409 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 5.10536 36.6409 2.4
      vertex 5.10536 36.6314 3
      vertex 5.10536 36.6314 2.4
    endloop
  endfacet
  facet normal -0.0227366 -0.999741 0
    outer loop
      vertex 4.68764 36.6409 2.4
      vertex 5.10536 36.6314 3
      vertex 4.68764 36.6409 3
    endloop
  endfacet
  facet normal -0.0227366 -0.999741 -0
    outer loop
      vertex 5.10536 36.6314 3
      vertex 4.68764 36.6409 2.4
      vertex 5.10536 36.6314 2.4
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 3.705 36.6409 2.4
      vertex 4.68764 36.6409 3
      vertex 3.705 36.6409 3
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex 4.68764 36.6409 3
      vertex 3.705 36.6409 2.4
      vertex 4.68764 36.6409 2.4
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3.705 35.9739 3
      vertex 3.705 36.6409 2.4
      vertex 3.705 36.6409 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3.705 36.6409 2.4
      vertex 3.705 35.9739 3
      vertex 3.705 35.9739 2.4
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 6.64093 35.9739 2.4
      vertex 3.705 35.9739 3
      vertex 6.64093 35.9739 3
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 3.705 35.9739 3
      vertex 6.64093 35.9739 2.4
      vertex 3.705 35.9739 2.4
    endloop
  endfacet
  facet normal 0.00922673 0.999957 -0
    outer loop
      vertex 6.86852 35.9718 2.4
      vertex 6.64093 35.9739 3
      vertex 6.86852 35.9718 3
    endloop
  endfacet
  facet normal 0.00922673 0.999957 0
    outer loop
      vertex 6.64093 35.9739 3
      vertex 6.86852 35.9718 2.4
      vertex 6.64093 35.9739 2.4
    endloop
  endfacet
  facet normal 0.0322232 0.999481 -0
    outer loop
      vertex 7.06393 35.9655 2.4
      vertex 6.86852 35.9718 3
      vertex 7.06393 35.9655 3
    endloop
  endfacet
  facet normal 0.0322232 0.999481 0
    outer loop
      vertex 6.86852 35.9718 3
      vertex 7.06393 35.9655 2.4
      vertex 6.86852 35.9718 2.4
    endloop
  endfacet
  facet normal 0.0641898 0.997938 -0
    outer loop
      vertex 7.22717 35.955 2.4
      vertex 7.06393 35.9655 3
      vertex 7.22717 35.955 3
    endloop
  endfacet
  facet normal 0.0641898 0.997938 0
    outer loop
      vertex 7.06393 35.9655 3
      vertex 7.22717 35.955 2.4
      vertex 7.06393 35.9655 2.4
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 7.22717 35.955 2.4
      vertex 7.22717 36.6029 3
      vertex 7.22717 36.6029 2.4
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex 7.22717 36.6029 3
      vertex 7.22717 35.955 2.4
      vertex 7.22717 35.955 3
    endloop
  endfacet
  facet normal -0.198563 -0.980088 0
    outer loop
      vertex 7.18867 36.6107 2.4
      vertex 7.22717 36.6029 3
      vertex 7.18867 36.6107 3
    endloop
  endfacet
  facet normal -0.198563 -0.980088 -0
    outer loop
      vertex 7.22717 36.6029 3
      vertex 7.18867 36.6107 2.4
      vertex 7.22717 36.6029 2.4
    endloop
  endfacet
  facet normal -0.120668 -0.992693 0
    outer loop
      vertex 7.12697 36.6182 2.4
      vertex 7.18867 36.6107 3
      vertex 7.12697 36.6182 3
    endloop
  endfacet
  facet normal -0.120668 -0.992693 -0
    outer loop
      vertex 7.18867 36.6107 3
      vertex 7.12697 36.6182 2.4
      vertex 7.18867 36.6107 2.4
    endloop
  endfacet
  facet normal -0.0856674 -0.996324 0
    outer loop
      vertex 7.04207 36.6255 2.4
      vertex 7.12697 36.6182 3
      vertex 7.04207 36.6255 3
    endloop
  endfacet
  facet normal -0.0856674 -0.996324 -0
    outer loop
      vertex 7.12697 36.6182 3
      vertex 7.04207 36.6255 2.4
      vertex 7.12697 36.6182 2.4
    endloop
  endfacet
  facet normal -0.0656476 -0.997843 0
    outer loop
      vertex 6.95239 36.6314 2.4
      vertex 7.04207 36.6255 3
      vertex 6.95239 36.6314 3
    endloop
  endfacet
  facet normal -0.0656476 -0.997843 -0
    outer loop
      vertex 7.04207 36.6255 3
      vertex 6.95239 36.6314 2.4
      vertex 7.04207 36.6255 2.4
    endloop
  endfacet
  facet normal -0.0473527 -0.998878 0
    outer loop
      vertex 6.87645 36.635 2.4
      vertex 6.95239 36.6314 3
      vertex 6.87645 36.635 3
    endloop
  endfacet
  facet normal -0.0473527 -0.998878 -0
    outer loop
      vertex 6.95239 36.6314 3
      vertex 6.87645 36.635 2.4
      vertex 6.95239 36.6314 2.4
    endloop
  endfacet
  facet normal -0.0176708 -0.999844 0
    outer loop
      vertex 6.81421 36.6361 2.4
      vertex 6.87645 36.635 3
      vertex 6.81421 36.6361 3
    endloop
  endfacet
  facet normal -0.0176708 -0.999844 -0
    outer loop
      vertex 6.87645 36.635 3
      vertex 6.81421 36.6361 2.4
      vertex 6.87645 36.635 2.4
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 6.81421 36.6361 2.4
      vertex 6.81421 36.6409 3
      vertex 6.81421 36.6409 2.4
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex 6.81421 36.6409 3
      vertex 6.81421 36.6361 2.4
      vertex 6.81421 36.6361 3
    endloop
  endfacet
  facet normal -0.510905 0.859637 0
    outer loop
      vertex 6.95134 36.7224 2.4
      vertex 6.81421 36.6409 3
      vertex 6.95134 36.7224 3
    endloop
  endfacet
  facet normal -0.510905 0.859637 0
    outer loop
      vertex 6.81421 36.6409 3
      vertex 6.95134 36.7224 2.4
      vertex 6.81421 36.6409 2.4
    endloop
  endfacet
  facet normal -0.667055 0.745009 0
    outer loop
      vertex 7.06526 36.8244 2.4
      vertex 6.95134 36.7224 3
      vertex 7.06526 36.8244 3
    endloop
  endfacet
  facet normal -0.667055 0.745009 0
    outer loop
      vertex 6.95134 36.7224 3
      vertex 7.06526 36.8244 2.4
      vertex 6.95134 36.7224 2.4
    endloop
  endfacet
  facet normal -0.804055 0.594555 0
    outer loop
      vertex 7.06526 36.8244 2.4
      vertex 7.15599 36.9471 3
      vertex 7.15599 36.9471 2.4
    endloop
  endfacet
  facet normal -0.804055 0.594555 0
    outer loop
      vertex 7.15599 36.9471 3
      vertex 7.06526 36.8244 2.4
      vertex 7.06526 36.8244 3
    endloop
  endfacet
  facet normal -0.906003 0.423272 0
    outer loop
      vertex 7.15599 36.9471 2.4
      vertex 7.22191 37.0882 3
      vertex 7.22191 37.0882 2.4
    endloop
  endfacet
  facet normal -0.906003 0.423272 0
    outer loop
      vertex 7.22191 37.0882 3
      vertex 7.15599 36.9471 2.4
      vertex 7.15599 36.9471 3
    endloop
  endfacet
  facet normal -0.969852 0.243695 0
    outer loop
      vertex 7.22191 37.0882 2.4
      vertex 7.26146 37.2456 3
      vertex 7.26146 37.2456 2.4
    endloop
  endfacet
  facet normal -0.969852 0.243695 0
    outer loop
      vertex 7.26146 37.2456 3
      vertex 7.22191 37.0882 2.4
      vertex 7.22191 37.0882 3
    endloop
  endfacet
  facet normal -0.997137 0.0756172 0
    outer loop
      vertex 7.26146 37.2456 2.4
      vertex 7.27464 37.4194 3
      vertex 7.27464 37.4194 2.4
    endloop
  endfacet
  facet normal -0.997137 0.0756172 0
    outer loop
      vertex 7.27464 37.4194 3
      vertex 7.26146 37.2456 2.4
      vertex 7.26146 37.2456 3
    endloop
  endfacet
  facet normal -0.991122 -0.132953 0
    outer loop
      vertex 7.27464 37.4194 2.4
      vertex 7.23547 37.7114 3
      vertex 7.23547 37.7114 2.4
    endloop
  endfacet
  facet normal -0.991122 -0.132953 0
    outer loop
      vertex 7.23547 37.7114 3
      vertex 7.27464 37.4194 2.4
      vertex 7.27464 37.4194 3
    endloop
  endfacet
  facet normal 0.87384 -0.486214 0
    outer loop
      vertex 6.71767 36.8774 3
      vertex 6.79362 37.0139 2.4
      vertex 6.79362 37.0139 3
    endloop
  endfacet
  facet normal 0.87384 -0.486214 0
    outer loop
      vertex 6.79362 37.0139 2.4
      vertex 6.71767 36.8774 3
      vertex 6.71767 36.8774 2.4
    endloop
  endfacet
  facet normal 0.646272 -0.763107 0
    outer loop
      vertex 6.59109 36.7702 2.4
      vertex 6.71767 36.8774 3
      vertex 6.59109 36.7702 3
    endloop
  endfacet
  facet normal 0.646272 -0.763107 0
    outer loop
      vertex 6.71767 36.8774 3
      vertex 6.59109 36.7702 2.4
      vertex 6.71767 36.8774 2.4
    endloop
  endfacet
  facet normal 0.40914 -0.912472 0
    outer loop
      vertex 6.41914 36.6931 2.4
      vertex 6.59109 36.7702 3
      vertex 6.41914 36.6931 3
    endloop
  endfacet
  facet normal 0.40914 -0.912472 0
    outer loop
      vertex 6.59109 36.7702 3
      vertex 6.41914 36.6931 2.4
      vertex 6.59109 36.7702 2.4
    endloop
  endfacet
  facet normal 0.213348 -0.976976 0
    outer loop
      vertex 6.20712 36.6468 2.4
      vertex 6.41914 36.6931 3
      vertex 6.20712 36.6468 3
    endloop
  endfacet
  facet normal 0.213348 -0.976976 0
    outer loop
      vertex 6.41914 36.6931 3
      vertex 6.20712 36.6468 2.4
      vertex 6.41914 36.6931 2.4
    endloop
  endfacet
  facet normal 0.0609732 -0.998139 0
    outer loop
      vertex 5.95502 36.6314 2.4
      vertex 6.20712 36.6468 3
      vertex 5.95502 36.6314 3
    endloop
  endfacet
  facet normal 0.0609732 -0.998139 0
    outer loop
      vertex 6.20712 36.6468 3
      vertex 5.95502 36.6314 2.4
      vertex 6.20712 36.6468 2.4
    endloop
  endfacet
  facet normal -0.059696 -0.998217 0
    outer loop
      vertex 5.69249 36.6471 2.4
      vertex 5.95502 36.6314 3
      vertex 5.69249 36.6471 3
    endloop
  endfacet
  facet normal -0.059696 -0.998217 -0
    outer loop
      vertex 5.95502 36.6314 3
      vertex 5.69249 36.6471 2.4
      vertex 5.95502 36.6314 2.4
    endloop
  endfacet
  facet normal -0.211219 -0.977439 0
    outer loop
      vertex 5.47453 36.6942 2.4
      vertex 5.69249 36.6471 3
      vertex 5.47453 36.6942 3
    endloop
  endfacet
  facet normal -0.211219 -0.977439 -0
    outer loop
      vertex 5.69249 36.6471 3
      vertex 5.47453 36.6942 2.4
      vertex 5.69249 36.6471 2.4
    endloop
  endfacet
  facet normal -0.41202 -0.911175 0
    outer loop
      vertex 5.30115 36.7726 2.4
      vertex 5.47453 36.6942 3
      vertex 5.30115 36.7726 3
    endloop
  endfacet
  facet normal -0.41202 -0.911175 -0
    outer loop
      vertex 5.47453 36.6942 3
      vertex 5.30115 36.7726 2.4
      vertex 5.47453 36.6942 2.4
    endloop
  endfacet
  facet normal -0.652731 -0.757589 0
    outer loop
      vertex 5.17522 36.8811 2.4
      vertex 5.30115 36.7726 3
      vertex 5.17522 36.8811 3
    endloop
  endfacet
  facet normal -0.652731 -0.757589 -0
    outer loop
      vertex 5.30115 36.7726 3
      vertex 5.17522 36.8811 2.4
      vertex 5.30115 36.7726 2.4
    endloop
  endfacet
  facet normal -0.876122 -0.48209 0
    outer loop
      vertex 5.17522 36.8811 2.4
      vertex 5.09967 37.0184 3
      vertex 5.09967 37.0184 2.4
    endloop
  endfacet
  facet normal -0.876122 -0.48209 0
    outer loop
      vertex 5.09967 37.0184 3
      vertex 5.17522 36.8811 2.4
      vertex 5.17522 36.8811 3
    endloop
  endfacet
  facet normal -0.988682 -0.150029 0
    outer loop
      vertex 5.09967 37.0184 2.4
      vertex 5.07448 37.1844 3
      vertex 5.07448 37.1844 2.4
    endloop
  endfacet
  facet normal -0.988682 -0.150029 0
    outer loop
      vertex 5.07448 37.1844 3
      vertex 5.09967 37.0184 2.4
      vertex 5.09967 37.0184 3
    endloop
  endfacet
  facet normal -0.989808 0.142406 0
    outer loop
      vertex 5.07448 37.1844 2.4
      vertex 5.09796 37.3476 3
      vertex 5.09796 37.3476 2.4
    endloop
  endfacet
  facet normal -0.989808 0.142406 0
    outer loop
      vertex 5.09796 37.3476 3
      vertex 5.07448 37.1844 2.4
      vertex 5.07448 37.1844 3
    endloop
  endfacet
  facet normal -0.882593 0.470138 0
    outer loop
      vertex 5.09796 37.3476 2.4
      vertex 5.16838 37.4798 3
      vertex 5.16838 37.4798 2.4
    endloop
  endfacet
  facet normal -0.882593 0.470138 0
    outer loop
      vertex 5.16838 37.4798 3
      vertex 5.09796 37.3476 2.4
      vertex 5.09796 37.3476 3
    endloop
  endfacet
  facet normal -0.652269 0.757988 0
    outer loop
      vertex 5.28575 37.5808 2.4
      vertex 5.16838 37.4798 3
      vertex 5.28575 37.5808 3
    endloop
  endfacet
  facet normal -0.652269 0.757988 0
    outer loop
      vertex 5.16838 37.4798 3
      vertex 5.28575 37.5808 2.4
      vertex 5.16838 37.4798 2.4
    endloop
  endfacet
  facet normal -0.394468 0.91891 0
    outer loop
      vertex 5.45161 37.652 2.4
      vertex 5.28575 37.5808 3
      vertex 5.45161 37.652 3
    endloop
  endfacet
  facet normal -0.394468 0.91891 0
    outer loop
      vertex 5.28575 37.5808 3
      vertex 5.45161 37.652 2.4
      vertex 5.28575 37.5808 2.4
    endloop
  endfacet
  facet normal -0.193949 0.981012 0
    outer loop
      vertex 5.66759 37.6947 2.4
      vertex 5.45161 37.652 3
      vertex 5.66759 37.6947 3
    endloop
  endfacet
  facet normal -0.193949 0.981012 0
    outer loop
      vertex 5.45161 37.652 3
      vertex 5.66759 37.6947 2.4
      vertex 5.45161 37.652 2.4
    endloop
  endfacet
  facet normal -0.0532916 0.998579 0
    outer loop
      vertex 5.93367 37.7089 2.4
      vertex 5.66759 37.6947 3
      vertex 5.93367 37.7089 3
    endloop
  endfacet
  facet normal -0.0532916 0.998579 0
    outer loop
      vertex 5.66759 37.6947 3
      vertex 5.93367 37.7089 2.4
      vertex 5.66759 37.6947 2.4
    endloop
  endfacet
  facet normal 0.118713 0.992929 -0
    outer loop
      vertex 6.42548 37.6501 2.4
      vertex 5.93367 37.7089 3
      vertex 6.42548 37.6501 3
    endloop
  endfacet
  facet normal 0.118713 0.992929 0
    outer loop
      vertex 5.93367 37.7089 3
      vertex 6.42548 37.6501 2.4
      vertex 5.93367 37.7089 2.4
    endloop
  endfacet
  facet normal 0.513084 0.858339 -0
    outer loop
      vertex 6.72058 37.4737 2.4
      vertex 6.42548 37.6501 3
      vertex 6.72058 37.4737 3
    endloop
  endfacet
  facet normal 0.513084 0.858339 0
    outer loop
      vertex 6.42548 37.6501 3
      vertex 6.72058 37.4737 2.4
      vertex 6.42548 37.6501 2.4
    endloop
  endfacet
  facet normal 0.948334 0.317273 0
    outer loop
      vertex 6.81894 37.1797 3
      vertex 6.72058 37.4737 2.4
      vertex 6.72058 37.4737 3
    endloop
  endfacet
  facet normal 0.948334 0.317273 0
    outer loop
      vertex 6.72058 37.4737 2.4
      vertex 6.81894 37.1797 3
      vertex 6.81894 37.1797 2.4
    endloop
  endfacet
  facet normal 0.988539 -0.150964 0
    outer loop
      vertex 6.79362 37.0139 3
      vertex 6.81894 37.1797 2.4
      vertex 6.81894 37.1797 3
    endloop
  endfacet
  facet normal 0.988539 -0.150964 0
    outer loop
      vertex 6.81894 37.1797 2.4
      vertex 6.79362 37.0139 3
      vertex 6.79362 37.0139 2.4
    endloop
  endfacet
  facet normal -0.968118 -0.250495 0
    outer loop
      vertex 7.2484 31.7907 2.4
      vertex 7.16969 32.0949 3
      vertex 7.16969 32.0949 2.4
    endloop
  endfacet
  facet normal -0.968118 -0.250495 0
    outer loop
      vertex 7.16969 32.0949 3
      vertex 7.2484 31.7907 2.4
      vertex 7.2484 31.7907 3
    endloop
  endfacet
  facet normal -0.89989 -0.436116 0
    outer loop
      vertex 7.16969 32.0949 2.4
      vertex 7.0385 32.3656 3
      vertex 7.0385 32.3656 2.4
    endloop
  endfacet
  facet normal -0.89989 -0.436116 0
    outer loop
      vertex 7.0385 32.3656 3
      vertex 7.16969 32.0949 2.4
      vertex 7.16969 32.0949 3
    endloop
  endfacet
  facet normal -0.783937 -0.62084 0
    outer loop
      vertex 7.0385 32.3656 2.4
      vertex 6.8535 32.5992 3
      vertex 6.8535 32.5992 2.4
    endloop
  endfacet
  facet normal -0.783937 -0.62084 0
    outer loop
      vertex 6.8535 32.5992 3
      vertex 7.0385 32.3656 2.4
      vertex 7.0385 32.3656 3
    endloop
  endfacet
  facet normal -0.625709 -0.780057 0
    outer loop
      vertex 6.61339 32.7918 2.4
      vertex 6.8535 32.5992 3
      vertex 6.61339 32.7918 3
    endloop
  endfacet
  facet normal -0.625709 -0.780057 -0
    outer loop
      vertex 6.8535 32.5992 3
      vertex 6.61339 32.7918 2.4
      vertex 6.8535 32.5992 2.4
    endloop
  endfacet
  facet normal -0.457032 -0.88945 0
    outer loop
      vertex 6.31816 32.9435 2.4
      vertex 6.61339 32.7918 3
      vertex 6.31816 32.9435 3
    endloop
  endfacet
  facet normal -0.457032 -0.88945 -0
    outer loop
      vertex 6.61339 32.7918 3
      vertex 6.31816 32.9435 2.4
      vertex 6.61339 32.7918 2.4
    endloop
  endfacet
  facet normal 0.935567 -0.35315 0
    outer loop
      vertex 6.08794 32.3336 3
      vertex 6.31816 32.9435 2.4
      vertex 6.31816 32.9435 3
    endloop
  endfacet
  facet normal 0.935567 -0.35315 0
    outer loop
      vertex 6.31816 32.9435 2.4
      vertex 6.08794 32.3336 3
      vertex 6.08794 32.3336 2.4
    endloop
  endfacet
  facet normal 0.50654 0.862216 -0
    outer loop
      vertex 6.44131 32.126 2.4
      vertex 6.08794 32.3336 3
      vertex 6.44131 32.126 3
    endloop
  endfacet
  facet normal 0.50654 0.862216 0
    outer loop
      vertex 6.08794 32.3336 3
      vertex 6.44131 32.126 2.4
      vertex 6.08794 32.3336 2.4
    endloop
  endfacet
  facet normal 0.81059 0.585614 0
    outer loop
      vertex 6.65335 31.8325 3
      vertex 6.44131 32.126 2.4
      vertex 6.44131 32.126 3
    endloop
  endfacet
  facet normal 0.81059 0.585614 0
    outer loop
      vertex 6.44131 32.126 2.4
      vertex 6.65335 31.8325 3
      vertex 6.65335 31.8325 2.4
    endloop
  endfacet
  facet normal 0.983104 0.183047 0
    outer loop
      vertex 6.72401 31.453 3
      vertex 6.65335 31.8325 2.4
      vertex 6.65335 31.8325 3
    endloop
  endfacet
  facet normal 0.983104 0.183047 0
    outer loop
      vertex 6.65335 31.8325 2.4
      vertex 6.72401 31.453 3
      vertex 6.72401 31.453 2.4
    endloop
  endfacet
  facet normal 0.993436 -0.114393 0
    outer loop
      vertex 6.69026 31.1599 3
      vertex 6.72401 31.453 2.4
      vertex 6.72401 31.453 3
    endloop
  endfacet
  facet normal 0.993436 -0.114393 0
    outer loop
      vertex 6.72401 31.453 2.4
      vertex 6.69026 31.1599 3
      vertex 6.69026 31.1599 2.4
    endloop
  endfacet
  facet normal 0.923176 -0.384378 0
    outer loop
      vertex 6.589 30.9167 3
      vertex 6.69026 31.1599 2.4
      vertex 6.69026 31.1599 3
    endloop
  endfacet
  facet normal 0.923176 -0.384378 0
    outer loop
      vertex 6.69026 31.1599 2.4
      vertex 6.589 30.9167 3
      vertex 6.589 30.9167 2.4
    endloop
  endfacet
  facet normal 0.753623 -0.657307 0
    outer loop
      vertex 6.42023 30.7232 3
      vertex 6.589 30.9167 2.4
      vertex 6.589 30.9167 3
    endloop
  endfacet
  facet normal 0.753623 -0.657307 0
    outer loop
      vertex 6.589 30.9167 2.4
      vertex 6.42023 30.7232 3
      vertex 6.42023 30.7232 2.4
    endloop
  endfacet
  facet normal 0.516328 -0.856391 0
    outer loop
      vertex 6.18736 30.5828 2.4
      vertex 6.42023 30.7232 3
      vertex 6.18736 30.5828 3
    endloop
  endfacet
  facet normal 0.516328 -0.856391 0
    outer loop
      vertex 6.42023 30.7232 3
      vertex 6.18736 30.5828 2.4
      vertex 6.42023 30.7232 2.4
    endloop
  endfacet
  facet normal 0.276044 -0.961145 0
    outer loop
      vertex 5.89384 30.4985 2.4
      vertex 6.18736 30.5828 3
      vertex 5.89384 30.4985 3
    endloop
  endfacet
  facet normal 0.276044 -0.961145 0
    outer loop
      vertex 6.18736 30.5828 3
      vertex 5.89384 30.4985 2.4
      vertex 6.18736 30.5828 2.4
    endloop
  endfacet
  facet normal 0.0790919 -0.996867 0
    outer loop
      vertex 5.53967 30.4704 2.4
      vertex 5.89384 30.4985 3
      vertex 5.53967 30.4704 3
    endloop
  endfacet
  facet normal 0.0790919 -0.996867 0
    outer loop
      vertex 5.89384 30.4985 3
      vertex 5.53967 30.4704 2.4
      vertex 5.89384 30.4985 2.4
    endloop
  endfacet
  facet normal -0.0782437 -0.996934 0
    outer loop
      vertex 5.19183 30.4977 2.4
      vertex 5.53967 30.4704 3
      vertex 5.19183 30.4977 3
    endloop
  endfacet
  facet normal -0.0782437 -0.996934 -0
    outer loop
      vertex 5.53967 30.4704 3
      vertex 5.19183 30.4977 2.4
      vertex 5.53967 30.4704 2.4
    endloop
  endfacet
  facet normal -0.274261 -0.961655 0
    outer loop
      vertex 4.90466 30.5796 2.4
      vertex 5.19183 30.4977 3
      vertex 4.90466 30.5796 3
    endloop
  endfacet
  facet normal -0.274261 -0.961655 -0
    outer loop
      vertex 5.19183 30.4977 3
      vertex 4.90466 30.5796 2.4
      vertex 5.19183 30.4977 2.4
    endloop
  endfacet
  facet normal -0.516146 -0.8565 0
    outer loop
      vertex 4.67815 30.7161 2.4
      vertex 4.90466 30.5796 3
      vertex 4.67815 30.7161 3
    endloop
  endfacet
  facet normal -0.516146 -0.8565 -0
    outer loop
      vertex 4.90466 30.5796 3
      vertex 4.67815 30.7161 2.4
      vertex 4.90466 30.5796 2.4
    endloop
  endfacet
  facet normal -0.756586 -0.653895 0
    outer loop
      vertex 4.67815 30.7161 2.4
      vertex 4.51463 30.9053 3
      vertex 4.51463 30.9053 2.4
    endloop
  endfacet
  facet normal -0.756586 -0.653895 0
    outer loop
      vertex 4.51463 30.9053 3
      vertex 4.67815 30.7161 2.4
      vertex 4.67815 30.7161 3
    endloop
  endfacet
  facet normal -0.925713 -0.378227 0
    outer loop
      vertex 4.51463 30.9053 2.4
      vertex 4.41653 31.1454 3
      vertex 4.41653 31.1454 2.4
    endloop
  endfacet
  facet normal -0.925713 -0.378227 0
    outer loop
      vertex 4.41653 31.1454 3
      vertex 4.51463 30.9053 2.4
      vertex 4.51463 30.9053 3
    endloop
  endfacet
  facet normal -0.993746 -0.111668 0
    outer loop
      vertex 4.41653 31.1454 2.4
      vertex 4.38383 31.4364 3
      vertex 4.38383 31.4364 2.4
    endloop
  endfacet
  facet normal -0.993746 -0.111668 0
    outer loop
      vertex 4.38383 31.4364 3
      vertex 4.41653 31.1454 2.4
      vertex 4.41653 31.1454 3
    endloop
  endfacet
  facet normal -0.996561 0.0828624 0
    outer loop
      vertex 4.38383 31.4364 2.4
      vertex 4.40031 31.6346 3
      vertex 4.40031 31.6346 2.4
    endloop
  endfacet
  facet normal -0.996561 0.0828624 0
    outer loop
      vertex 4.40031 31.6346 3
      vertex 4.38383 31.4364 2.4
      vertex 4.38383 31.4364 3
    endloop
  endfacet
  facet normal -0.964288 0.264858 0
    outer loop
      vertex 4.40031 31.6346 2.4
      vertex 4.44975 31.8146 3
      vertex 4.44975 31.8146 2.4
    endloop
  endfacet
  facet normal -0.964288 0.264858 0
    outer loop
      vertex 4.44975 31.8146 3
      vertex 4.40031 31.6346 2.4
      vertex 4.40031 31.6346 3
    endloop
  endfacet
  facet normal -0.891054 0.453898 0
    outer loop
      vertex 4.44975 31.8146 2.4
      vertex 4.53217 31.9764 3
      vertex 4.53217 31.9764 2.4
    endloop
  endfacet
  facet normal -0.891054 0.453898 0
    outer loop
      vertex 4.53217 31.9764 3
      vertex 4.44975 31.8146 2.4
      vertex 4.44975 31.8146 3
    endloop
  endfacet
  facet normal -0.776306 0.630356 0
    outer loop
      vertex 4.53217 31.9764 2.4
      vertex 4.64252 32.1123 3
      vertex 4.64252 32.1123 2.4
    endloop
  endfacet
  facet normal -0.776306 0.630356 0
    outer loop
      vertex 4.64252 32.1123 3
      vertex 4.53217 31.9764 2.4
      vertex 4.53217 31.9764 3
    endloop
  endfacet
  facet normal -0.609567 0.792735 0
    outer loop
      vertex 4.77582 32.2148 2.4
      vertex 4.64252 32.1123 3
      vertex 4.77582 32.2148 3
    endloop
  endfacet
  facet normal -0.609567 0.792735 0
    outer loop
      vertex 4.64252 32.1123 3
      vertex 4.77582 32.2148 2.4
      vertex 4.64252 32.1123 2.4
    endloop
  endfacet
  facet normal -0.403474 0.914991 0
    outer loop
      vertex 4.93207 32.2837 2.4
      vertex 4.77582 32.2148 3
      vertex 4.93207 32.2837 3
    endloop
  endfacet
  facet normal -0.403474 0.914991 0
    outer loop
      vertex 4.77582 32.2148 3
      vertex 4.93207 32.2837 2.4
      vertex 4.77582 32.2148 2.4
    endloop
  endfacet
  facet normal -0.964688 -0.263394 0
    outer loop
      vertex 4.93207 32.2837 2.4
      vertex 4.76358 32.9008 3
      vertex 4.76358 32.9008 2.4
    endloop
  endfacet
  facet normal -0.964688 -0.263394 0
    outer loop
      vertex 4.76358 32.9008 3
      vertex 4.93207 32.2837 2.4
      vertex 4.93207 32.2837 3
    endloop
  endfacet
  facet normal 0.40459 -0.914498 0
    outer loop
      vertex 4.48285 32.7766 2.4
      vertex 4.76358 32.9008 3
      vertex 4.48285 32.7766 3
    endloop
  endfacet
  facet normal 0.40459 -0.914498 0
    outer loop
      vertex 4.76358 32.9008 3
      vertex 4.48285 32.7766 2.4
      vertex 4.76358 32.9008 2.4
    endloop
  endfacet
  facet normal 0.599446 -0.800415 0
    outer loop
      vertex 4.25145 32.6033 2.4
      vertex 4.48285 32.7766 3
      vertex 4.25145 32.6033 3
    endloop
  endfacet
  facet normal 0.599446 -0.800415 0
    outer loop
      vertex 4.48285 32.7766 3
      vertex 4.25145 32.6033 2.4
      vertex 4.48285 32.7766 2.4
    endloop
  endfacet
  facet normal 0.773585 -0.633692 0
    outer loop
      vertex 4.06935 32.381 3
      vertex 4.25145 32.6033 2.4
      vertex 4.25145 32.6033 3
    endloop
  endfacet
  facet normal 0.773585 -0.633692 0
    outer loop
      vertex 4.25145 32.6033 2.4
      vertex 4.06935 32.381 3
      vertex 4.06935 32.381 2.4
    endloop
  endfacet
  facet normal 0.900117 -0.435649 0
    outer loop
      vertex 3.93814 32.1099 3
      vertex 4.06935 32.381 2.4
      vertex 4.06935 32.381 3
    endloop
  endfacet
  facet normal 0.900117 -0.435649 0
    outer loop
      vertex 4.06935 32.381 2.4
      vertex 3.93814 32.1099 3
      vertex 3.93814 32.1099 2.4
    endloop
  endfacet
  facet normal 0.97098 -0.23916 0
    outer loop
      vertex 3.85942 31.7903 3
      vertex 3.93814 32.1099 2.4
      vertex 3.93814 32.1099 3
    endloop
  endfacet
  facet normal 0.97098 -0.23916 0
    outer loop
      vertex 3.93814 32.1099 2.4
      vertex 3.85942 31.7903 3
      vertex 3.85942 31.7903 2.4
    endloop
  endfacet
  facet normal 0.997469 -0.0711045 0
    outer loop
      vertex 3.83318 31.4222 3
      vertex 3.85942 31.7903 2.4
      vertex 3.85942 31.7903 3
    endloop
  endfacet
  facet normal 0.997469 -0.0711045 0
    outer loop
      vertex 3.85942 31.7903 2.4
      vertex 3.83318 31.4222 3
      vertex 3.83318 31.4222 2.4
    endloop
  endfacet
  facet normal 0.995136 0.0985094 0
    outer loop
      vertex 3.88223 30.9267 3
      vertex 3.83318 31.4222 2.4
      vertex 3.83318 31.4222 3
    endloop
  endfacet
  facet normal 0.995136 0.0985094 0
    outer loop
      vertex 3.83318 31.4222 2.4
      vertex 3.88223 30.9267 3
      vertex 3.88223 30.9267 2.4
    endloop
  endfacet
  facet normal 0.941406 0.337274 0
    outer loop
      vertex 4.02937 30.516 3
      vertex 3.88223 30.9267 2.4
      vertex 3.88223 30.9267 3
    endloop
  endfacet
  facet normal 0.941406 0.337274 0
    outer loop
      vertex 3.88223 30.9267 2.4
      vertex 4.02937 30.516 3
      vertex 4.02937 30.516 2.4
    endloop
  endfacet
  facet normal 0.798839 0.601545 0
    outer loop
      vertex 4.27463 30.1903 3
      vertex 4.02937 30.516 2.4
      vertex 4.02937 30.516 3
    endloop
  endfacet
  facet normal 0.798839 0.601545 0
    outer loop
      vertex 4.02937 30.516 2.4
      vertex 4.27463 30.1903 3
      vertex 4.27463 30.1903 2.4
    endloop
  endfacet
  facet normal 0.5739 0.818926 -0
    outer loop
      vertex 4.61139 29.9543 2.4
      vertex 4.27463 30.1903 3
      vertex 4.61139 29.9543 3
    endloop
  endfacet
  facet normal 0.5739 0.818926 0
    outer loop
      vertex 4.27463 30.1903 3
      vertex 4.61139 29.9543 2.4
      vertex 4.27463 30.1903 2.4
    endloop
  endfacet
  facet normal 0.318331 0.94798 -0
    outer loop
      vertex 5.03307 29.8127 2.4
      vertex 4.61139 29.9543 3
      vertex 5.03307 29.8127 3
    endloop
  endfacet
  facet normal 0.318331 0.94798 0
    outer loop
      vertex 4.61139 29.9543 3
      vertex 5.03307 29.8127 2.4
      vertex 4.61139 29.9543 2.4
    endloop
  endfacet
  facet normal 0.0927684 0.995688 -0
    outer loop
      vertex 5.53967 29.7655 2.4
      vertex 5.03307 29.8127 3
      vertex 5.53967 29.7655 3
    endloop
  endfacet
  facet normal 0.0927684 0.995688 0
    outer loop
      vertex 5.03307 29.8127 3
      vertex 5.53967 29.7655 2.4
      vertex 5.03307 29.8127 2.4
    endloop
  endfacet
  facet normal -0.0960079 0.995381 0
    outer loop
      vertex 6.04665 29.8144 2.4
      vertex 5.53967 29.7655 3
      vertex 6.04665 29.8144 3
    endloop
  endfacet
  facet normal -0.0960079 0.995381 0
    outer loop
      vertex 5.53967 29.7655 3
      vertex 6.04665 29.8144 2.4
      vertex 5.53967 29.7655 2.4
    endloop
  endfacet
  facet normal -0.325785 0.945444 0
    outer loop
      vertex 6.47267 29.9612 2.4
      vertex 6.04665 29.8144 3
      vertex 6.47267 29.9612 3
    endloop
  endfacet
  facet normal -0.325785 0.945444 0
    outer loop
      vertex 6.04665 29.8144 3
      vertex 6.47267 29.9612 2.4
      vertex 6.04665 29.8144 2.4
    endloop
  endfacet
  facet normal -0.578282 0.815837 0
    outer loop
      vertex 6.81775 30.2058 2.4
      vertex 6.47267 29.9612 3
      vertex 6.81775 30.2058 3
    endloop
  endfacet
  facet normal -0.578282 0.815837 0
    outer loop
      vertex 6.47267 29.9612 3
      vertex 6.81775 30.2058 2.4
      vertex 6.47267 29.9612 2.4
    endloop
  endfacet
  facet normal -0.796435 0.604724 0
    outer loop
      vertex 6.81775 30.2058 2.4
      vertex 7.07158 30.5401 3
      vertex 7.07158 30.5401 2.4
    endloop
  endfacet
  facet normal -0.796435 0.604724 0
    outer loop
      vertex 7.07158 30.5401 3
      vertex 6.81775 30.2058 2.4
      vertex 6.81775 30.2058 3
    endloop
  endfacet
  facet normal -0.938966 0.344009 0
    outer loop
      vertex 7.07158 30.5401 2.4
      vertex 7.22388 30.9558 3
      vertex 7.22388 30.9558 2.4
    endloop
  endfacet
  facet normal -0.938966 0.344009 0
    outer loop
      vertex 7.22388 30.9558 3
      vertex 7.07158 30.5401 2.4
      vertex 7.07158 30.5401 3
    endloop
  endfacet
  facet normal -0.994829 0.101564 0
    outer loop
      vertex 7.22388 30.9558 2.4
      vertex 7.27464 31.453 3
      vertex 7.27464 31.453 2.4
    endloop
  endfacet
  facet normal -0.994829 0.101564 0
    outer loop
      vertex 7.27464 31.453 3
      vertex 7.22388 30.9558 2.4
      vertex 7.22388 30.9558 3
    endloop
  endfacet
  facet normal -0.996995 -0.0774686 0
    outer loop
      vertex 7.27464 31.453 2.4
      vertex 7.2484 31.7907 3
      vertex 7.2484 31.7907 2.4
    endloop
  endfacet
  facet normal -0.996995 -0.0774686 0
    outer loop
      vertex 7.2484 31.7907 3
      vertex 7.27464 31.453 2.4
      vertex 7.27464 31.453 3
    endloop
  endfacet
  facet normal -0.971706 -0.236192 0
    outer loop
      vertex 7.24576 45.3323 2.4
      vertex 7.15913 45.6887 3
      vertex 7.15913 45.6887 2.4
    endloop
  endfacet
  facet normal -0.971706 -0.236192 0
    outer loop
      vertex 7.15913 45.6887 3
      vertex 7.24576 45.3323 2.4
      vertex 7.24576 45.3323 3
    endloop
  endfacet
  facet normal -0.889288 -0.457348 0
    outer loop
      vertex 7.15913 45.6887 2.4
      vertex 7.01477 45.9694 3
      vertex 7.01477 45.9694 2.4
    endloop
  endfacet
  facet normal -0.889288 -0.457348 0
    outer loop
      vertex 7.01477 45.9694 3
      vertex 7.15913 45.6887 2.4
      vertex 7.15913 45.6887 3
    endloop
  endfacet
  facet normal -0.713088 -0.701074 0
    outer loop
      vertex 7.01477 45.9694 2.4
      vertex 6.81578 46.1718 3
      vertex 6.81578 46.1718 2.4
    endloop
  endfacet
  facet normal -0.713088 -0.701074 0
    outer loop
      vertex 6.81578 46.1718 3
      vertex 7.01477 45.9694 2.4
      vertex 7.01477 45.9694 3
    endloop
  endfacet
  facet normal -0.436256 -0.899823 0
    outer loop
      vertex 6.56538 46.2932 2.4
      vertex 6.81578 46.1718 3
      vertex 6.56538 46.2932 3
    endloop
  endfacet
  facet normal -0.436256 -0.899823 -0
    outer loop
      vertex 6.81578 46.1718 3
      vertex 6.56538 46.2932 2.4
      vertex 6.81578 46.1718 2.4
    endloop
  endfacet
  facet normal -0.132998 -0.991116 0
    outer loop
      vertex 6.26357 46.3337 2.4
      vertex 6.56538 46.2932 3
      vertex 6.26357 46.3337 3
    endloop
  endfacet
  facet normal -0.132998 -0.991116 -0
    outer loop
      vertex 6.56538 46.2932 3
      vertex 6.26357 46.3337 2.4
      vertex 6.56538 46.2932 2.4
    endloop
  endfacet
  facet normal 0.0529739 -0.998596 0
    outer loop
      vertex 6.12973 46.3266 2.4
      vertex 6.26357 46.3337 3
      vertex 6.12973 46.3266 3
    endloop
  endfacet
  facet normal 0.0529739 -0.998596 0
    outer loop
      vertex 6.26357 46.3337 3
      vertex 6.12973 46.3266 2.4
      vertex 6.26357 46.3337 2.4
    endloop
  endfacet
  facet normal 0.170631 -0.985335 0
    outer loop
      vertex 6.00673 46.3053 2.4
      vertex 6.12973 46.3266 3
      vertex 6.00673 46.3053 3
    endloop
  endfacet
  facet normal 0.170631 -0.985335 0
    outer loop
      vertex 6.12973 46.3266 3
      vertex 6.00673 46.3053 2.4
      vertex 6.12973 46.3266 2.4
    endloop
  endfacet
  facet normal 0.302432 -0.953171 0
    outer loop
      vertex 5.89453 46.2697 2.4
      vertex 6.00673 46.3053 3
      vertex 5.89453 46.2697 3
    endloop
  endfacet
  facet normal 0.302432 -0.953171 0
    outer loop
      vertex 6.00673 46.3053 3
      vertex 5.89453 46.2697 2.4
      vertex 6.00673 46.3053 2.4
    endloop
  endfacet
  facet normal 0.434393 -0.900724 0
    outer loop
      vertex 5.79272 46.2206 2.4
      vertex 5.89453 46.2697 3
      vertex 5.79272 46.2206 3
    endloop
  endfacet
  facet normal 0.434393 -0.900724 0
    outer loop
      vertex 5.89453 46.2697 3
      vertex 5.79272 46.2206 2.4
      vertex 5.89453 46.2697 2.4
    endloop
  endfacet
  facet normal 0.55791 -0.829902 0
    outer loop
      vertex 5.70094 46.1589 2.4
      vertex 5.79272 46.2206 3
      vertex 5.70094 46.1589 3
    endloop
  endfacet
  facet normal 0.55791 -0.829902 0
    outer loop
      vertex 5.79272 46.2206 3
      vertex 5.70094 46.1589 2.4
      vertex 5.79272 46.2206 2.4
    endloop
  endfacet
  facet normal 0.673078 -0.739572 0
    outer loop
      vertex 5.61919 46.0845 2.4
      vertex 5.70094 46.1589 3
      vertex 5.61919 46.0845 3
    endloop
  endfacet
  facet normal 0.673078 -0.739572 0
    outer loop
      vertex 5.70094 46.1589 3
      vertex 5.61919 46.0845 2.4
      vertex 5.70094 46.1589 2.4
    endloop
  endfacet
  facet normal 0.775226 -0.631684 0
    outer loop
      vertex 5.54561 45.9942 3
      vertex 5.61919 46.0845 2.4
      vertex 5.61919 46.0845 3
    endloop
  endfacet
  facet normal 0.775226 -0.631684 0
    outer loop
      vertex 5.61919 46.0845 2.4
      vertex 5.54561 45.9942 3
      vertex 5.54561 45.9942 2.4
    endloop
  endfacet
  facet normal 0.852338 -0.522991 0
    outer loop
      vertex 5.47836 45.8846 3
      vertex 5.54561 45.9942 2.4
      vertex 5.54561 45.9942 3
    endloop
  endfacet
  facet normal 0.852338 -0.522991 0
    outer loop
      vertex 5.54561 45.9942 2.4
      vertex 5.47836 45.8846 3
      vertex 5.47836 45.8846 2.4
    endloop
  endfacet
  facet normal 0.904011 -0.42751 0
    outer loop
      vertex 5.41745 45.7558 3
      vertex 5.47836 45.8846 2.4
      vertex 5.47836 45.8846 3
    endloop
  endfacet
  facet normal 0.904011 -0.42751 0
    outer loop
      vertex 5.47836 45.8846 2.4
      vertex 5.41745 45.7558 3
      vertex 5.41745 45.7558 2.4
    endloop
  endfacet
  facet normal 0.943256 -0.332066 0
    outer loop
      vertex 5.35799 45.5869 3
      vertex 5.41745 45.7558 2.4
      vertex 5.41745 45.7558 3
    endloop
  endfacet
  facet normal 0.943256 -0.332066 0
    outer loop
      vertex 5.41745 45.7558 2.4
      vertex 5.35799 45.5869 3
      vertex 5.35799 45.5869 2.4
    endloop
  endfacet
  facet normal 0.964521 -0.264005 0
    outer loop
      vertex 5.29509 45.3571 3
      vertex 5.35799 45.5869 2.4
      vertex 5.35799 45.5869 3
    endloop
  endfacet
  facet normal 0.964521 -0.264005 0
    outer loop
      vertex 5.35799 45.5869 2.4
      vertex 5.29509 45.3571 3
      vertex 5.29509 45.3571 2.4
    endloop
  endfacet
  facet normal 0.974959 -0.222383 0
    outer loop
      vertex 5.22876 45.0663 3
      vertex 5.29509 45.3571 2.4
      vertex 5.29509 45.3571 3
    endloop
  endfacet
  facet normal 0.974959 -0.222383 0
    outer loop
      vertex 5.29509 45.3571 2.4
      vertex 5.22876 45.0663 3
      vertex 5.22876 45.0663 2.4
    endloop
  endfacet
  facet normal 0.974561 -0.224125 0
    outer loop
      vertex 5.17352 44.8261 3
      vertex 5.22876 45.0663 2.4
      vertex 5.22876 45.0663 3
    endloop
  endfacet
  facet normal 0.974561 -0.224125 0
    outer loop
      vertex 5.22876 45.0663 2.4
      vertex 5.17352 44.8261 3
      vertex 5.17352 44.8261 2.4
    endloop
  endfacet
  facet normal 0.965202 -0.261507 0
    outer loop
      vertex 5.12486 44.6465 3
      vertex 5.17352 44.8261 2.4
      vertex 5.17352 44.8261 3
    endloop
  endfacet
  facet normal 0.965202 -0.261507 0
    outer loop
      vertex 5.17352 44.8261 2.4
      vertex 5.12486 44.6465 3
      vertex 5.12486 44.6465 2.4
    endloop
  endfacet
  facet normal 0.942866 -0.333172 0
    outer loop
      vertex 5.08281 44.5275 3
      vertex 5.12486 44.6465 2.4
      vertex 5.12486 44.6465 3
    endloop
  endfacet
  facet normal 0.942866 -0.333172 0
    outer loop
      vertex 5.12486 44.6465 2.4
      vertex 5.08281 44.5275 3
      vertex 5.08281 44.5275 2.4
    endloop
  endfacet
  facet normal 0.890538 -0.454908 0
    outer loop
      vertex 5.04128 44.4462 3
      vertex 5.08281 44.5275 2.4
      vertex 5.08281 44.5275 3
    endloop
  endfacet
  facet normal 0.890538 -0.454908 0
    outer loop
      vertex 5.08281 44.5275 2.4
      vertex 5.04128 44.4462 3
      vertex 5.04128 44.4462 2.4
    endloop
  endfacet
  facet normal 0.817794 -0.575512 0
    outer loop
      vertex 4.9942 44.3793 3
      vertex 5.04128 44.4462 2.4
      vertex 5.04128 44.4462 3
    endloop
  endfacet
  facet normal 0.817794 -0.575512 0
    outer loop
      vertex 5.04128 44.4462 2.4
      vertex 4.9942 44.3793 3
      vertex 4.9942 44.3793 2.4
    endloop
  endfacet
  facet normal 0.705014 -0.709193 0
    outer loop
      vertex 4.94159 44.327 2.4
      vertex 4.9942 44.3793 3
      vertex 4.94159 44.327 3
    endloop
  endfacet
  facet normal 0.705014 -0.709193 0
    outer loop
      vertex 4.9942 44.3793 3
      vertex 4.94159 44.327 2.4
      vertex 4.9942 44.3793 2.4
    endloop
  endfacet
  facet normal 0.526784 -0.849999 0
    outer loop
      vertex 4.88092 44.2894 2.4
      vertex 4.94159 44.327 3
      vertex 4.88092 44.2894 3
    endloop
  endfacet
  facet normal 0.526784 -0.849999 0
    outer loop
      vertex 4.94159 44.327 3
      vertex 4.88092 44.2894 2.4
      vertex 4.94159 44.327 2.4
    endloop
  endfacet
  facet normal 0.301285 -0.953534 0
    outer loop
      vertex 4.80971 44.2669 2.4
      vertex 4.88092 44.2894 3
      vertex 4.80971 44.2669 3
    endloop
  endfacet
  facet normal 0.301285 -0.953534 0
    outer loop
      vertex 4.88092 44.2894 3
      vertex 4.80971 44.2669 2.4
      vertex 4.88092 44.2894 2.4
    endloop
  endfacet
  facet normal 0.0913484 -0.995819 0
    outer loop
      vertex 4.72795 44.2594 2.4
      vertex 4.80971 44.2669 3
      vertex 4.72795 44.2594 3
    endloop
  endfacet
  facet normal 0.0913484 -0.995819 0
    outer loop
      vertex 4.80971 44.2669 3
      vertex 4.72795 44.2594 2.4
      vertex 4.80971 44.2669 2.4
    endloop
  endfacet
  facet normal -0.303671 -0.952777 0
    outer loop
      vertex 4.50644 44.33 2.4
      vertex 4.72795 44.2594 3
      vertex 4.50644 44.33 3
    endloop
  endfacet
  facet normal -0.303671 -0.952777 -0
    outer loop
      vertex 4.72795 44.2594 3
      vertex 4.50644 44.33 2.4
      vertex 4.72795 44.2594 2.4
    endloop
  endfacet
  facet normal -0.847392 -0.530968 0
    outer loop
      vertex 4.50644 44.33 2.4
      vertex 4.37354 44.5421 3
      vertex 4.37354 44.5421 2.4
    endloop
  endfacet
  facet normal -0.847392 -0.530968 0
    outer loop
      vertex 4.37354 44.5421 3
      vertex 4.50644 44.33 2.4
      vertex 4.50644 44.33 3
    endloop
  endfacet
  facet normal -0.992223 -0.12447 0
    outer loop
      vertex 4.37354 44.5421 2.4
      vertex 4.32922 44.8954 3
      vertex 4.32922 44.8954 2.4
    endloop
  endfacet
  facet normal -0.992223 -0.12447 0
    outer loop
      vertex 4.32922 44.8954 3
      vertex 4.37354 44.5421 2.4
      vertex 4.37354 44.5421 3
    endloop
  endfacet
  facet normal -0.997827 0.0658891 0
    outer loop
      vertex 4.32922 44.8954 2.4
      vertex 4.34137 45.0794 3
      vertex 4.34137 45.0794 2.4
    endloop
  endfacet
  facet normal -0.997827 0.0658891 0
    outer loop
      vertex 4.34137 45.0794 3
      vertex 4.32922 44.8954 2.4
      vertex 4.32922 44.8954 3
    endloop
  endfacet
  facet normal -0.972895 0.231245 0
    outer loop
      vertex 4.34137 45.0794 2.4
      vertex 4.37776 45.2325 3
      vertex 4.37776 45.2325 2.4
    endloop
  endfacet
  facet normal -0.972895 0.231245 0
    outer loop
      vertex 4.37776 45.2325 3
      vertex 4.34137 45.0794 2.4
      vertex 4.34137 45.0794 3
    endloop
  endfacet
  facet normal -0.895684 0.44469 0
    outer loop
      vertex 4.37776 45.2325 2.4
      vertex 4.43843 45.3547 3
      vertex 4.43843 45.3547 2.4
    endloop
  endfacet
  facet normal -0.895684 0.44469 0
    outer loop
      vertex 4.43843 45.3547 3
      vertex 4.37776 45.2325 2.4
      vertex 4.37776 45.2325 3
    endloop
  endfacet
  facet normal -0.745949 0.666003 0
    outer loop
      vertex 4.43843 45.3547 2.4
      vertex 4.52307 45.4495 3
      vertex 4.52307 45.4495 2.4
    endloop
  endfacet
  facet normal -0.745949 0.666003 0
    outer loop
      vertex 4.52307 45.4495 3
      vertex 4.43843 45.3547 2.4
      vertex 4.43843 45.3547 3
    endloop
  endfacet
  facet normal -0.546904 0.837195 0
    outer loop
      vertex 4.63145 45.5203 2.4
      vertex 4.52307 45.4495 3
      vertex 4.63145 45.5203 3
    endloop
  endfacet
  facet normal -0.546904 0.837195 0
    outer loop
      vertex 4.52307 45.4495 3
      vertex 4.63145 45.5203 2.4
      vertex 4.52307 45.4495 2.4
    endloop
  endfacet
  facet normal -0.333872 0.942618 0
    outer loop
      vertex 4.76358 45.5671 2.4
      vertex 4.63145 45.5203 3
      vertex 4.76358 45.5671 3
    endloop
  endfacet
  facet normal -0.333872 0.942618 0
    outer loop
      vertex 4.63145 45.5203 3
      vertex 4.76358 45.5671 2.4
      vertex 4.63145 45.5203 2.4
    endloop
  endfacet
  facet normal -0.990829 -0.135122 0
    outer loop
      vertex 4.76358 45.5671 2.4
      vertex 4.67101 46.2459 3
      vertex 4.67101 46.2459 2.4
    endloop
  endfacet
  facet normal -0.990829 -0.135122 0
    outer loop
      vertex 4.67101 46.2459 3
      vertex 4.76358 45.5671 2.4
      vertex 4.76358 45.5671 3
    endloop
  endfacet
  facet normal 0.298787 -0.95432 0
    outer loop
      vertex 4.40016 46.1611 2.4
      vertex 4.67101 46.2459 3
      vertex 4.40016 46.1611 3
    endloop
  endfacet
  facet normal 0.298787 -0.95432 0
    outer loop
      vertex 4.67101 46.2459 3
      vertex 4.40016 46.1611 2.4
      vertex 4.67101 46.2459 2.4
    endloop
  endfacet
  facet normal 0.530283 -0.847821 0
    outer loop
      vertex 4.18576 46.027 2.4
      vertex 4.40016 46.1611 3
      vertex 4.18576 46.027 3
    endloop
  endfacet
  facet normal 0.530283 -0.847821 0
    outer loop
      vertex 4.40016 46.1611 3
      vertex 4.18576 46.027 2.4
      vertex 4.40016 46.1611 2.4
    endloop
  endfacet
  facet normal 0.757744 -0.652552 0
    outer loop
      vertex 4.02782 45.8436 3
      vertex 4.18576 46.027 2.4
      vertex 4.18576 46.027 3
    endloop
  endfacet
  facet normal 0.757744 -0.652552 0
    outer loop
      vertex 4.18576 46.027 2.4
      vertex 4.02782 45.8436 3
      vertex 4.02782 45.8436 2.4
    endloop
  endfacet
  facet normal 0.913305 -0.407277 0
    outer loop
      vertex 3.91968 45.6011 3
      vertex 4.02782 45.8436 2.4
      vertex 4.02782 45.8436 3
    endloop
  endfacet
  facet normal 0.913305 -0.407277 0
    outer loop
      vertex 4.02782 45.8436 2.4
      vertex 3.91968 45.6011 3
      vertex 3.91968 45.6011 2.4
    endloop
  endfacet
  facet normal 0.978964 -0.204032 0
    outer loop
      vertex 3.8548 45.2898 3
      vertex 3.91968 45.6011 2.4
      vertex 3.91968 45.6011 3
    endloop
  endfacet
  facet normal 0.978964 -0.204032 0
    outer loop
      vertex 3.91968 45.6011 2.4
      vertex 3.8548 45.2898 3
      vertex 3.8548 45.2898 2.4
    endloop
  endfacet
  facet normal 0.998386 -0.056788 0
    outer loop
      vertex 3.83318 44.9097 3
      vertex 3.8548 45.2898 2.4
      vertex 3.8548 45.2898 3
    endloop
  endfacet
  facet normal 0.998386 -0.056788 0
    outer loop
      vertex 3.8548 45.2898 2.4
      vertex 3.83318 44.9097 3
      vertex 3.83318 44.9097 2.4
    endloop
  endfacet
  facet normal 0.997761 0.066884 0
    outer loop
      vertex 3.85994 44.5105 3
      vertex 3.83318 44.9097 2.4
      vertex 3.83318 44.9097 3
    endloop
  endfacet
  facet normal 0.997761 0.066884 0
    outer loop
      vertex 3.83318 44.9097 2.4
      vertex 3.85994 44.5105 3
      vertex 3.85994 44.5105 2.4
    endloop
  endfacet
  facet normal 0.97169 0.236259 0
    outer loop
      vertex 3.94025 44.1802 3
      vertex 3.85994 44.5105 2.4
      vertex 3.85994 44.5105 3
    endloop
  endfacet
  facet normal 0.97169 0.236259 0
    outer loop
      vertex 3.85994 44.5105 2.4
      vertex 3.94025 44.1802 3
      vertex 3.94025 44.1802 2.4
    endloop
  endfacet
  facet normal 0.890123 0.45572 0
    outer loop
      vertex 4.07408 43.9188 3
      vertex 3.94025 44.1802 2.4
      vertex 3.94025 44.1802 3
    endloop
  endfacet
  facet normal 0.890123 0.45572 0
    outer loop
      vertex 3.94025 44.1802 2.4
      vertex 4.07408 43.9188 3
      vertex 4.07408 43.9188 2.4
    endloop
  endfacet
  facet normal 0.716492 0.697595 0
    outer loop
      vertex 4.25829 43.7296 3
      vertex 4.07408 43.9188 2.4
      vertex 4.07408 43.9188 3
    endloop
  endfacet
  facet normal 0.716492 0.697595 0
    outer loop
      vertex 4.07408 43.9188 2.4
      vertex 4.25829 43.7296 3
      vertex 4.25829 43.7296 2.4
    endloop
  endfacet
  facet normal 0.440669 0.89767 -0
    outer loop
      vertex 4.4897 43.616 2.4
      vertex 4.25829 43.7296 3
      vertex 4.4897 43.616 3
    endloop
  endfacet
  facet normal 0.440669 0.89767 0
    outer loop
      vertex 4.25829 43.7296 3
      vertex 4.4897 43.616 2.4
      vertex 4.25829 43.7296 2.4
    endloop
  endfacet
  facet normal 0.134442 0.990921 -0
    outer loop
      vertex 4.76831 43.5782 2.4
      vertex 4.4897 43.616 3
      vertex 4.76831 43.5782 3
    endloop
  endfacet
  facet normal 0.134442 0.990921 0
    outer loop
      vertex 4.4897 43.616 3
      vertex 4.76831 43.5782 2.4
      vertex 4.4897 43.616 2.4
    endloop
  endfacet
  facet normal -0.0446218 0.999004 0
    outer loop
      vertex 4.88249 43.5833 2.4
      vertex 4.76831 43.5782 3
      vertex 4.88249 43.5833 3
    endloop
  endfacet
  facet normal -0.0446218 0.999004 0
    outer loop
      vertex 4.76831 43.5782 3
      vertex 4.88249 43.5833 2.4
      vertex 4.76831 43.5782 2.4
    endloop
  endfacet
  facet normal -0.144804 0.98946 0
    outer loop
      vertex 4.98772 43.5987 2.4
      vertex 4.88249 43.5833 3
      vertex 4.98772 43.5987 3
    endloop
  endfacet
  facet normal -0.144804 0.98946 0
    outer loop
      vertex 4.88249 43.5833 3
      vertex 4.98772 43.5987 2.4
      vertex 4.88249 43.5833 2.4
    endloop
  endfacet
  facet normal -0.258912 0.965901 0
    outer loop
      vertex 5.08397 43.6245 2.4
      vertex 4.98772 43.5987 3
      vertex 5.08397 43.6245 3
    endloop
  endfacet
  facet normal -0.258912 0.965901 0
    outer loop
      vertex 4.98772 43.5987 3
      vertex 5.08397 43.6245 2.4
      vertex 4.98772 43.5987 2.4
    endloop
  endfacet
  facet normal -0.369346 0.929292 0
    outer loop
      vertex 5.17178 43.6594 2.4
      vertex 5.08397 43.6245 3
      vertex 5.17178 43.6594 3
    endloop
  endfacet
  facet normal -0.369346 0.929292 0
    outer loop
      vertex 5.08397 43.6245 3
      vertex 5.17178 43.6594 2.4
      vertex 5.08397 43.6245 2.4
    endloop
  endfacet
  facet normal -0.474711 0.880142 0
    outer loop
      vertex 5.25169 43.7025 2.4
      vertex 5.17178 43.6594 3
      vertex 5.25169 43.7025 3
    endloop
  endfacet
  facet normal -0.474711 0.880142 0
    outer loop
      vertex 5.17178 43.6594 3
      vertex 5.25169 43.7025 2.4
      vertex 5.17178 43.6594 2.4
    endloop
  endfacet
  facet normal -0.580328 0.814383 0
    outer loop
      vertex 5.32368 43.7538 2.4
      vertex 5.25169 43.7025 3
      vertex 5.32368 43.7538 3
    endloop
  endfacet
  facet normal -0.580328 0.814383 0
    outer loop
      vertex 5.25169 43.7025 3
      vertex 5.32368 43.7538 2.4
      vertex 5.25169 43.7025 2.4
    endloop
  endfacet
  facet normal -0.675389 0.737461 0
    outer loop
      vertex 5.38843 43.8131 2.4
      vertex 5.32368 43.7538 3
      vertex 5.38843 43.8131 3
    endloop
  endfacet
  facet normal -0.675389 0.737461 0
    outer loop
      vertex 5.32368 43.7538 3
      vertex 5.38843 43.8131 2.4
      vertex 5.32368 43.7538 2.4
    endloop
  endfacet
  facet normal -0.756616 0.65386 0
    outer loop
      vertex 5.38843 43.8131 2.4
      vertex 5.44659 43.8804 3
      vertex 5.44659 43.8804 2.4
    endloop
  endfacet
  facet normal -0.756616 0.65386 0
    outer loop
      vertex 5.44659 43.8804 3
      vertex 5.38843 43.8131 2.4
      vertex 5.38843 43.8131 3
    endloop
  endfacet
  facet normal -0.824407 0.565998 0
    outer loop
      vertex 5.44659 43.8804 2.4
      vertex 5.49815 43.9555 3
      vertex 5.49815 43.9555 2.4
    endloop
  endfacet
  facet normal -0.824407 0.565998 0
    outer loop
      vertex 5.49815 43.9555 3
      vertex 5.44659 43.8804 2.4
      vertex 5.44659 43.8804 3
    endloop
  endfacet
  facet normal -0.872181 0.489184 0
    outer loop
      vertex 5.49815 43.9555 2.4
      vertex 5.54431 44.0378 3
      vertex 5.54431 44.0378 2.4
    endloop
  endfacet
  facet normal -0.872181 0.489184 0
    outer loop
      vertex 5.54431 44.0378 3
      vertex 5.49815 43.9555 2.4
      vertex 5.49815 43.9555 3
    endloop
  endfacet
  facet normal -0.903889 0.427766 0
    outer loop
      vertex 5.54431 44.0378 2.4
      vertex 5.58624 44.1264 3
      vertex 5.58624 44.1264 2.4
    endloop
  endfacet
  facet normal -0.903889 0.427766 0
    outer loop
      vertex 5.58624 44.1264 3
      vertex 5.54431 44.0378 2.4
      vertex 5.54431 44.0378 3
    endloop
  endfacet
  facet normal -0.929318 0.369279 0
    outer loop
      vertex 5.58624 44.1264 2.4
      vertex 5.62395 44.2213 3
      vertex 5.62395 44.2213 2.4
    endloop
  endfacet
  facet normal -0.929318 0.369279 0
    outer loop
      vertex 5.62395 44.2213 3
      vertex 5.58624 44.1264 2.4
      vertex 5.58624 44.1264 3
    endloop
  endfacet
  facet normal -0.95267 0.304006 0
    outer loop
      vertex 5.62395 44.2213 2.4
      vertex 5.66336 44.3448 3
      vertex 5.66336 44.3448 2.4
    endloop
  endfacet
  facet normal -0.95267 0.304006 0
    outer loop
      vertex 5.66336 44.3448 3
      vertex 5.62395 44.2213 2.4
      vertex 5.62395 44.2213 3
    endloop
  endfacet
  facet normal -0.965317 0.261079 0
    outer loop
      vertex 5.66336 44.3448 2.4
      vertex 5.71042 44.5188 3
      vertex 5.71042 44.5188 2.4
    endloop
  endfacet
  facet normal -0.965317 0.261079 0
    outer loop
      vertex 5.71042 44.5188 3
      vertex 5.66336 44.3448 2.4
      vertex 5.66336 44.3448 3
    endloop
  endfacet
  facet normal -0.971605 0.23661 0
    outer loop
      vertex 5.71042 44.5188 2.4
      vertex 5.76514 44.7435 3
      vertex 5.76514 44.7435 2.4
    endloop
  endfacet
  facet normal -0.971605 0.23661 0
    outer loop
      vertex 5.76514 44.7435 3
      vertex 5.71042 44.5188 2.4
      vertex 5.71042 44.5188 3
    endloop
  endfacet
  facet normal -0.977561 0.210651 0
    outer loop
      vertex 5.76514 44.7435 2.4
      vertex 5.8208 45.0018 3
      vertex 5.8208 45.0018 2.4
    endloop
  endfacet
  facet normal -0.977561 0.210651 0
    outer loop
      vertex 5.8208 45.0018 3
      vertex 5.76514 44.7435 2.4
      vertex 5.76514 44.7435 3
    endloop
  endfacet
  facet normal -0.969085 0.246726 0
    outer loop
      vertex 5.8208 45.0018 2.4
      vertex 5.87065 45.1976 3
      vertex 5.87065 45.1976 2.4
    endloop
  endfacet
  facet normal -0.969085 0.246726 0
    outer loop
      vertex 5.87065 45.1976 3
      vertex 5.8208 45.0018 2.4
      vertex 5.8208 45.0018 3
    endloop
  endfacet
  facet normal -0.94952 0.313705 0
    outer loop
      vertex 5.87065 45.1976 2.4
      vertex 5.91469 45.3309 3
      vertex 5.91469 45.3309 2.4
    endloop
  endfacet
  facet normal -0.94952 0.313705 0
    outer loop
      vertex 5.91469 45.3309 3
      vertex 5.87065 45.1976 2.4
      vertex 5.87065 45.1976 3
    endloop
  endfacet
  facet normal -0.904452 0.426576 0
    outer loop
      vertex 5.91469 45.3309 2.4
      vertex 5.95926 45.4254 3
      vertex 5.95926 45.4254 2.4
    endloop
  endfacet
  facet normal -0.904452 0.426576 0
    outer loop
      vertex 5.95926 45.4254 3
      vertex 5.91469 45.3309 2.4
      vertex 5.91469 45.3309 3
    endloop
  endfacet
  facet normal -0.838468 0.544951 0
    outer loop
      vertex 5.95926 45.4254 2.4
      vertex 6.01067 45.5045 3
      vertex 6.01067 45.5045 2.4
    endloop
  endfacet
  facet normal -0.838468 0.544951 0
    outer loop
      vertex 6.01067 45.5045 3
      vertex 5.95926 45.4254 2.4
      vertex 5.95926 45.4254 3
    endloop
  endfacet
  facet normal -0.738325 0.674445 0
    outer loop
      vertex 6.01067 45.5045 2.4
      vertex 6.06895 45.5683 3
      vertex 6.06895 45.5683 2.4
    endloop
  endfacet
  facet normal -0.738325 0.674445 0
    outer loop
      vertex 6.06895 45.5683 3
      vertex 6.01067 45.5045 2.4
      vertex 6.01067 45.5045 3
    endloop
  endfacet
  facet normal -0.571208 0.820806 0
    outer loop
      vertex 6.1362 45.6151 2.4
      vertex 6.06895 45.5683 3
      vertex 6.1362 45.6151 3
    endloop
  endfacet
  facet normal -0.571208 0.820806 0
    outer loop
      vertex 6.06895 45.5683 3
      vertex 6.1362 45.6151 2.4
      vertex 6.06895 45.5683 2.4
    endloop
  endfacet
  facet normal -0.337745 0.941238 0
    outer loop
      vertex 6.21451 45.6432 2.4
      vertex 6.1362 45.6151 3
      vertex 6.21451 45.6432 3
    endloop
  endfacet
  facet normal -0.337745 0.941238 0
    outer loop
      vertex 6.1362 45.6151 3
      vertex 6.21451 45.6432 2.4
      vertex 6.1362 45.6151 2.4
    endloop
  endfacet
  facet normal -0.104569 0.994518 0
    outer loop
      vertex 6.30391 45.6526 2.4
      vertex 6.21451 45.6432 3
      vertex 6.30391 45.6526 3
    endloop
  endfacet
  facet normal -0.104569 0.994518 0
    outer loop
      vertex 6.21451 45.6432 3
      vertex 6.30391 45.6526 2.4
      vertex 6.21451 45.6432 2.4
    endloop
  endfacet
  facet normal 0.312305 0.949982 -0
    outer loop
      vertex 6.55182 45.5711 2.4
      vertex 6.30391 45.6526 3
      vertex 6.55182 45.5711 3
    endloop
  endfacet
  facet normal 0.312305 0.949982 0
    outer loop
      vertex 6.30391 45.6526 3
      vertex 6.55182 45.5711 2.4
      vertex 6.30391 45.6526 2.4
    endloop
  endfacet
  facet normal 0.854348 0.519702 0
    outer loop
      vertex 6.70055 45.3266 3
      vertex 6.55182 45.5711 2.4
      vertex 6.55182 45.5711 3
    endloop
  endfacet
  facet normal 0.854348 0.519702 0
    outer loop
      vertex 6.55182 45.5711 2.4
      vertex 6.70055 45.3266 3
      vertex 6.70055 45.3266 2.4
    endloop
  endfacet
  facet normal 0.992673 0.120831 0
    outer loop
      vertex 6.75014 44.9192 3
      vertex 6.70055 45.3266 2.4
      vertex 6.70055 45.3266 3
    endloop
  endfacet
  facet normal 0.992673 0.120831 0
    outer loop
      vertex 6.70055 45.3266 2.4
      vertex 6.75014 44.9192 3
      vertex 6.75014 44.9192 2.4
    endloop
  endfacet
  facet normal 0.99815 -0.0607927 0
    outer loop
      vertex 6.73682 44.7005 3
      vertex 6.75014 44.9192 2.4
      vertex 6.75014 44.9192 3
    endloop
  endfacet
  facet normal 0.99815 -0.0607927 0
    outer loop
      vertex 6.75014 44.9192 2.4
      vertex 6.73682 44.7005 3
      vertex 6.73682 44.7005 2.4
    endloop
  endfacet
  facet normal 0.977303 -0.211846 0
    outer loop
      vertex 6.69687 44.5162 3
      vertex 6.73682 44.7005 2.4
      vertex 6.73682 44.7005 3
    endloop
  endfacet
  facet normal 0.977303 -0.211846 0
    outer loop
      vertex 6.73682 44.7005 2.4
      vertex 6.69687 44.5162 3
      vertex 6.69687 44.5162 2.4
    endloop
  endfacet
  facet normal 0.914108 -0.405472 0
    outer loop
      vertex 6.63029 44.3661 3
      vertex 6.69687 44.5162 2.4
      vertex 6.69687 44.5162 3
    endloop
  endfacet
  facet normal 0.914108 -0.405472 0
    outer loop
      vertex 6.69687 44.5162 2.4
      vertex 6.63029 44.3661 3
      vertex 6.63029 44.3661 2.4
    endloop
  endfacet
  facet normal 0.776306 -0.630356 0
    outer loop
      vertex 6.53415 44.2477 3
      vertex 6.63029 44.3661 2.4
      vertex 6.63029 44.3661 3
    endloop
  endfacet
  facet normal 0.776306 -0.630356 0
    outer loop
      vertex 6.63029 44.3661 2.4
      vertex 6.53415 44.2477 3
      vertex 6.53415 44.2477 2.4
    endloop
  endfacet
  facet normal 0.570922 -0.821004 0
    outer loop
      vertex 6.40559 44.1583 2.4
      vertex 6.53415 44.2477 3
      vertex 6.40559 44.1583 3
    endloop
  endfacet
  facet normal 0.570922 -0.821004 0
    outer loop
      vertex 6.53415 44.2477 3
      vertex 6.40559 44.1583 2.4
      vertex 6.53415 44.2477 2.4
    endloop
  endfacet
  facet normal 0.350722 -0.93648 0
    outer loop
      vertex 6.24458 44.098 2.4
      vertex 6.40559 44.1583 3
      vertex 6.24458 44.098 3
    endloop
  endfacet
  facet normal 0.350722 -0.93648 0
    outer loop
      vertex 6.40559 44.1583 3
      vertex 6.24458 44.098 2.4
      vertex 6.40559 44.1583 2.4
    endloop
  endfacet
  facet normal 0.986674 0.16271 0
    outer loop
      vertex 6.35614 43.4215 3
      vertex 6.24458 44.098 2.4
      vertex 6.24458 44.098 3
    endloop
  endfacet
  facet normal 0.986674 0.16271 0
    outer loop
      vertex 6.24458 44.098 2.4
      vertex 6.35614 43.4215 3
      vertex 6.35614 43.4215 2.4
    endloop
  endfacet
  facet normal -0.329902 0.944015 0
    outer loop
      vertex 6.63857 43.5202 2.4
      vertex 6.35614 43.4215 3
      vertex 6.63857 43.5202 3
    endloop
  endfacet
  facet normal -0.329902 0.944015 0
    outer loop
      vertex 6.35614 43.4215 3
      vertex 6.63857 43.5202 2.4
      vertex 6.35614 43.4215 2.4
    endloop
  endfacet
  facet normal -0.562434 0.826842 0
    outer loop
      vertex 6.86879 43.6768 2.4
      vertex 6.63857 43.5202 3
      vertex 6.86879 43.6768 3
    endloop
  endfacet
  facet normal -0.562434 0.826842 0
    outer loop
      vertex 6.63857 43.5202 3
      vertex 6.86879 43.6768 2.4
      vertex 6.63857 43.5202 2.4
    endloop
  endfacet
  facet normal -0.769853 0.638221 0
    outer loop
      vertex 6.86879 43.6768 2.4
      vertex 7.04678 43.8915 3
      vertex 7.04678 43.8915 2.4
    endloop
  endfacet
  facet normal -0.769853 0.638221 0
    outer loop
      vertex 7.04678 43.8915 3
      vertex 6.86879 43.6768 2.4
      vertex 6.86879 43.6768 3
    endloop
  endfacet
  facet normal -0.908088 0.418779 0
    outer loop
      vertex 7.04678 43.8915 2.4
      vertex 7.17337 44.166 3
      vertex 7.17337 44.166 2.4
    endloop
  endfacet
  facet normal -0.908088 0.418779 0
    outer loop
      vertex 7.17337 44.166 3
      vertex 7.04678 43.8915 2.4
      vertex 7.04678 43.8915 3
    endloop
  endfacet
  facet normal -0.975414 0.220382 0
    outer loop
      vertex 7.17337 44.166 2.4
      vertex 7.24933 44.5022 3
      vertex 7.24933 44.5022 2.4
    endloop
  endfacet
  facet normal -0.975414 0.220382 0
    outer loop
      vertex 7.24933 44.5022 3
      vertex 7.17337 44.166 2.4
      vertex 7.17337 44.166 3
    endloop
  endfacet
  facet normal -0.997984 0.0634648 0
    outer loop
      vertex 7.24933 44.5022 2.4
      vertex 7.27464 44.9002 3
      vertex 7.27464 44.9002 2.4
    endloop
  endfacet
  facet normal -0.997984 0.0634648 0
    outer loop
      vertex 7.27464 44.9002 3
      vertex 7.24933 44.5022 2.4
      vertex 7.24933 44.5022 3
    endloop
  endfacet
  facet normal -0.997774 -0.0666876 0
    outer loop
      vertex 7.27464 44.9002 2.4
      vertex 7.24576 45.3323 3
      vertex 7.24576 45.3323 2.4
    endloop
  endfacet
  facet normal -0.997774 -0.0666876 0
    outer loop
      vertex 7.24576 45.3323 3
      vertex 7.27464 44.9002 2.4
      vertex 7.27464 44.9002 3
    endloop
  endfacet
  facet normal -0.968118 -0.250495 0
    outer loop
      vertex 7.2484 42.0778 2.4
      vertex 7.16969 42.382 3
      vertex 7.16969 42.382 2.4
    endloop
  endfacet
  facet normal -0.968118 -0.250495 0
    outer loop
      vertex 7.16969 42.382 3
      vertex 7.2484 42.0778 2.4
      vertex 7.2484 42.0778 3
    endloop
  endfacet
  facet normal -0.89989 -0.436116 0
    outer loop
      vertex 7.16969 42.382 2.4
      vertex 7.0385 42.6527 3
      vertex 7.0385 42.6527 2.4
    endloop
  endfacet
  facet normal -0.89989 -0.436116 0
    outer loop
      vertex 7.0385 42.6527 3
      vertex 7.16969 42.382 2.4
      vertex 7.16969 42.382 3
    endloop
  endfacet
  facet normal -0.783808 -0.621004 0
    outer loop
      vertex 7.0385 42.6527 2.4
      vertex 6.8535 42.8862 3
      vertex 6.8535 42.8862 2.4
    endloop
  endfacet
  facet normal -0.783808 -0.621004 0
    outer loop
      vertex 6.8535 42.8862 3
      vertex 7.0385 42.6527 2.4
      vertex 7.0385 42.6527 3
    endloop
  endfacet
  facet normal -0.625906 -0.779898 0
    outer loop
      vertex 6.61339 43.0789 2.4
      vertex 6.8535 42.8862 3
      vertex 6.61339 43.0789 3
    endloop
  endfacet
  facet normal -0.625906 -0.779898 -0
    outer loop
      vertex 6.8535 42.8862 3
      vertex 6.61339 43.0789 2.4
      vertex 6.8535 42.8862 2.4
    endloop
  endfacet
  facet normal -0.457032 -0.88945 0
    outer loop
      vertex 6.31816 43.2306 2.4
      vertex 6.61339 43.0789 3
      vertex 6.31816 43.2306 3
    endloop
  endfacet
  facet normal -0.457032 -0.88945 -0
    outer loop
      vertex 6.61339 43.0789 3
      vertex 6.31816 43.2306 2.4
      vertex 6.61339 43.0789 2.4
    endloop
  endfacet
  facet normal 0.935567 -0.35315 0
    outer loop
      vertex 6.08794 42.6207 3
      vertex 6.31816 43.2306 2.4
      vertex 6.31816 43.2306 3
    endloop
  endfacet
  facet normal 0.935567 -0.35315 0
    outer loop
      vertex 6.31816 43.2306 2.4
      vertex 6.08794 42.6207 3
      vertex 6.08794 42.6207 2.4
    endloop
  endfacet
  facet normal 0.50654 0.862216 -0
    outer loop
      vertex 6.44131 42.4131 2.4
      vertex 6.08794 42.6207 3
      vertex 6.44131 42.4131 3
    endloop
  endfacet
  facet normal 0.50654 0.862216 0
    outer loop
      vertex 6.08794 42.6207 3
      vertex 6.44131 42.4131 2.4
      vertex 6.08794 42.6207 2.4
    endloop
  endfacet
  facet normal 0.81059 0.585614 0
    outer loop
      vertex 6.65335 42.1196 3
      vertex 6.44131 42.4131 2.4
      vertex 6.44131 42.4131 3
    endloop
  endfacet
  facet normal 0.81059 0.585614 0
    outer loop
      vertex 6.44131 42.4131 2.4
      vertex 6.65335 42.1196 3
      vertex 6.65335 42.1196 2.4
    endloop
  endfacet
  facet normal 0.983104 0.183047 0
    outer loop
      vertex 6.72401 41.7401 3
      vertex 6.65335 42.1196 2.4
      vertex 6.65335 42.1196 3
    endloop
  endfacet
  facet normal 0.983104 0.183047 0
    outer loop
      vertex 6.65335 42.1196 2.4
      vertex 6.72401 41.7401 3
      vertex 6.72401 41.7401 2.4
    endloop
  endfacet
  facet normal 0.993436 -0.114393 0
    outer loop
      vertex 6.69026 41.447 3
      vertex 6.72401 41.7401 2.4
      vertex 6.72401 41.7401 3
    endloop
  endfacet
  facet normal 0.993436 -0.114393 0
    outer loop
      vertex 6.72401 41.7401 2.4
      vertex 6.69026 41.447 3
      vertex 6.69026 41.447 2.4
    endloop
  endfacet
  facet normal 0.923232 -0.384244 0
    outer loop
      vertex 6.589 41.2037 3
      vertex 6.69026 41.447 2.4
      vertex 6.69026 41.447 3
    endloop
  endfacet
  facet normal 0.923232 -0.384244 0
    outer loop
      vertex 6.69026 41.447 2.4
      vertex 6.589 41.2037 3
      vertex 6.589 41.2037 2.4
    endloop
  endfacet
  facet normal 0.753454 -0.6575 0
    outer loop
      vertex 6.42023 41.0103 3
      vertex 6.589 41.2037 2.4
      vertex 6.589 41.2037 3
    endloop
  endfacet
  facet normal 0.753454 -0.6575 0
    outer loop
      vertex 6.589 41.2037 2.4
      vertex 6.42023 41.0103 3
      vertex 6.42023 41.0103 2.4
    endloop
  endfacet
  facet normal 0.516328 -0.856391 0
    outer loop
      vertex 6.18736 40.8699 2.4
      vertex 6.42023 41.0103 3
      vertex 6.18736 40.8699 3
    endloop
  endfacet
  facet normal 0.516328 -0.856391 0
    outer loop
      vertex 6.42023 41.0103 3
      vertex 6.18736 40.8699 2.4
      vertex 6.42023 41.0103 2.4
    endloop
  endfacet
  facet normal 0.276044 -0.961145 0
    outer loop
      vertex 5.89384 40.7856 2.4
      vertex 6.18736 40.8699 3
      vertex 5.89384 40.7856 3
    endloop
  endfacet
  facet normal 0.276044 -0.961145 0
    outer loop
      vertex 6.18736 40.8699 3
      vertex 5.89384 40.7856 2.4
      vertex 6.18736 40.8699 2.4
    endloop
  endfacet
  facet normal 0.0790919 -0.996867 0
    outer loop
      vertex 5.53967 40.7575 2.4
      vertex 5.89384 40.7856 3
      vertex 5.53967 40.7575 3
    endloop
  endfacet
  facet normal 0.0790919 -0.996867 0
    outer loop
      vertex 5.89384 40.7856 3
      vertex 5.53967 40.7575 2.4
      vertex 5.89384 40.7856 2.4
    endloop
  endfacet
  facet normal -0.0782437 -0.996934 0
    outer loop
      vertex 5.19183 40.7848 2.4
      vertex 5.53967 40.7575 3
      vertex 5.19183 40.7848 3
    endloop
  endfacet
  facet normal -0.0782437 -0.996934 -0
    outer loop
      vertex 5.53967 40.7575 3
      vertex 5.19183 40.7848 2.4
      vertex 5.53967 40.7575 2.4
    endloop
  endfacet
  facet normal -0.274261 -0.961655 0
    outer loop
      vertex 4.90466 40.8667 2.4
      vertex 5.19183 40.7848 3
      vertex 4.90466 40.8667 3
    endloop
  endfacet
  facet normal -0.274261 -0.961655 -0
    outer loop
      vertex 5.19183 40.7848 3
      vertex 4.90466 40.8667 2.4
      vertex 5.19183 40.7848 2.4
    endloop
  endfacet
  facet normal -0.516146 -0.8565 0
    outer loop
      vertex 4.67815 41.0032 2.4
      vertex 4.90466 40.8667 3
      vertex 4.67815 41.0032 3
    endloop
  endfacet
  facet normal -0.516146 -0.8565 -0
    outer loop
      vertex 4.90466 40.8667 3
      vertex 4.67815 41.0032 2.4
      vertex 4.90466 40.8667 2.4
    endloop
  endfacet
  facet normal -0.756586 -0.653895 0
    outer loop
      vertex 4.67815 41.0032 2.4
      vertex 4.51463 41.1924 3
      vertex 4.51463 41.1924 2.4
    endloop
  endfacet
  facet normal -0.756586 -0.653895 0
    outer loop
      vertex 4.51463 41.1924 3
      vertex 4.67815 41.0032 2.4
      vertex 4.67815 41.0032 3
    endloop
  endfacet
  facet normal -0.925713 -0.378227 0
    outer loop
      vertex 4.51463 41.1924 2.4
      vertex 4.41653 41.4325 3
      vertex 4.41653 41.4325 2.4
    endloop
  endfacet
  facet normal -0.925713 -0.378227 0
    outer loop
      vertex 4.41653 41.4325 3
      vertex 4.51463 41.1924 2.4
      vertex 4.51463 41.1924 3
    endloop
  endfacet
  facet normal -0.993746 -0.111668 0
    outer loop
      vertex 4.41653 41.4325 2.4
      vertex 4.38383 41.7235 3
      vertex 4.38383 41.7235 2.4
    endloop
  endfacet
  facet normal -0.993746 -0.111668 0
    outer loop
      vertex 4.38383 41.7235 3
      vertex 4.41653 41.4325 2.4
      vertex 4.41653 41.4325 3
    endloop
  endfacet
  facet normal -0.996561 0.0828624 0
    outer loop
      vertex 4.38383 41.7235 2.4
      vertex 4.40031 41.9217 3
      vertex 4.40031 41.9217 2.4
    endloop
  endfacet
  facet normal -0.996561 0.0828624 0
    outer loop
      vertex 4.40031 41.9217 3
      vertex 4.38383 41.7235 2.4
      vertex 4.38383 41.7235 3
    endloop
  endfacet
  facet normal -0.964288 0.264858 0
    outer loop
      vertex 4.40031 41.9217 2.4
      vertex 4.44975 42.1017 3
      vertex 4.44975 42.1017 2.4
    endloop
  endfacet
  facet normal -0.964288 0.264858 0
    outer loop
      vertex 4.44975 42.1017 3
      vertex 4.40031 41.9217 2.4
      vertex 4.40031 41.9217 3
    endloop
  endfacet
  facet normal -0.891054 0.453898 0
    outer loop
      vertex 4.44975 42.1017 2.4
      vertex 4.53217 42.2635 3
      vertex 4.53217 42.2635 2.4
    endloop
  endfacet
  facet normal -0.891054 0.453898 0
    outer loop
      vertex 4.53217 42.2635 3
      vertex 4.44975 42.1017 2.4
      vertex 4.44975 42.1017 3
    endloop
  endfacet
  facet normal -0.776306 0.630356 0
    outer loop
      vertex 4.53217 42.2635 2.4
      vertex 4.64252 42.3994 3
      vertex 4.64252 42.3994 2.4
    endloop
  endfacet
  facet normal -0.776306 0.630356 0
    outer loop
      vertex 4.64252 42.3994 3
      vertex 4.53217 42.2635 2.4
      vertex 4.53217 42.2635 3
    endloop
  endfacet
  facet normal -0.609567 0.792735 0
    outer loop
      vertex 4.77582 42.5019 2.4
      vertex 4.64252 42.3994 3
      vertex 4.77582 42.5019 3
    endloop
  endfacet
  facet normal -0.609567 0.792735 0
    outer loop
      vertex 4.64252 42.3994 3
      vertex 4.77582 42.5019 2.4
      vertex 4.64252 42.3994 2.4
    endloop
  endfacet
  facet normal -0.403474 0.914991 0
    outer loop
      vertex 4.93207 42.5708 2.4
      vertex 4.77582 42.5019 3
      vertex 4.93207 42.5708 3
    endloop
  endfacet
  facet normal -0.403474 0.914991 0
    outer loop
      vertex 4.77582 42.5019 3
      vertex 4.93207 42.5708 2.4
      vertex 4.77582 42.5019 2.4
    endloop
  endfacet
  facet normal -0.964688 -0.263394 0
    outer loop
      vertex 4.93207 42.5708 2.4
      vertex 4.76358 43.1879 3
      vertex 4.76358 43.1879 2.4
    endloop
  endfacet
  facet normal -0.964688 -0.263394 0
    outer loop
      vertex 4.76358 43.1879 3
      vertex 4.93207 42.5708 2.4
      vertex 4.93207 42.5708 3
    endloop
  endfacet
  facet normal 0.40459 -0.914498 0
    outer loop
      vertex 4.48285 43.0637 2.4
      vertex 4.76358 43.1879 3
      vertex 4.48285 43.0637 3
    endloop
  endfacet
  facet normal 0.40459 -0.914498 0
    outer loop
      vertex 4.76358 43.1879 3
      vertex 4.48285 43.0637 2.4
      vertex 4.76358 43.1879 2.4
    endloop
  endfacet
  facet normal 0.599446 -0.800415 0
    outer loop
      vertex 4.25145 42.8904 2.4
      vertex 4.48285 43.0637 3
      vertex 4.25145 42.8904 3
    endloop
  endfacet
  facet normal 0.599446 -0.800415 0
    outer loop
      vertex 4.48285 43.0637 3
      vertex 4.25145 42.8904 2.4
      vertex 4.48285 43.0637 2.4
    endloop
  endfacet
  facet normal 0.773585 -0.633692 0
    outer loop
      vertex 4.06935 42.6681 3
      vertex 4.25145 42.8904 2.4
      vertex 4.25145 42.8904 3
    endloop
  endfacet
  facet normal 0.773585 -0.633692 0
    outer loop
      vertex 4.25145 42.8904 2.4
      vertex 4.06935 42.6681 3
      vertex 4.06935 42.6681 2.4
    endloop
  endfacet
  facet normal 0.900117 -0.435649 0
    outer loop
      vertex 3.93814 42.397 3
      vertex 4.06935 42.6681 2.4
      vertex 4.06935 42.6681 3
    endloop
  endfacet
  facet normal 0.900117 -0.435649 0
    outer loop
      vertex 4.06935 42.6681 2.4
      vertex 3.93814 42.397 3
      vertex 3.93814 42.397 2.4
    endloop
  endfacet
  facet normal 0.97098 -0.23916 0
    outer loop
      vertex 3.85942 42.0774 3
      vertex 3.93814 42.397 2.4
      vertex 3.93814 42.397 3
    endloop
  endfacet
  facet normal 0.97098 -0.23916 0
    outer loop
      vertex 3.93814 42.397 2.4
      vertex 3.85942 42.0774 3
      vertex 3.85942 42.0774 2.4
    endloop
  endfacet
  facet normal 0.99747 -0.0710853 0
    outer loop
      vertex 3.83318 41.7092 3
      vertex 3.85942 42.0774 2.4
      vertex 3.85942 42.0774 3
    endloop
  endfacet
  facet normal 0.99747 -0.0710853 0
    outer loop
      vertex 3.85942 42.0774 2.4
      vertex 3.83318 41.7092 3
      vertex 3.83318 41.7092 2.4
    endloop
  endfacet
  facet normal 0.995136 0.0985094 0
    outer loop
      vertex 3.88223 41.2137 3
      vertex 3.83318 41.7092 2.4
      vertex 3.83318 41.7092 3
    endloop
  endfacet
  facet normal 0.995136 0.0985094 0
    outer loop
      vertex 3.83318 41.7092 2.4
      vertex 3.88223 41.2137 3
      vertex 3.88223 41.2137 2.4
    endloop
  endfacet
  facet normal 0.94138 0.337347 0
    outer loop
      vertex 4.02937 40.8031 3
      vertex 3.88223 41.2137 2.4
      vertex 3.88223 41.2137 3
    endloop
  endfacet
  facet normal 0.94138 0.337347 0
    outer loop
      vertex 3.88223 41.2137 2.4
      vertex 4.02937 40.8031 3
      vertex 4.02937 40.8031 2.4
    endloop
  endfacet
  facet normal 0.798839 0.601545 0
    outer loop
      vertex 4.27463 40.4774 3
      vertex 4.02937 40.8031 2.4
      vertex 4.02937 40.8031 3
    endloop
  endfacet
  facet normal 0.798839 0.601545 0
    outer loop
      vertex 4.02937 40.8031 2.4
      vertex 4.27463 40.4774 3
      vertex 4.27463 40.4774 2.4
    endloop
  endfacet
  facet normal 0.5739 0.818926 -0
    outer loop
      vertex 4.61139 40.2414 2.4
      vertex 4.27463 40.4774 3
      vertex 4.61139 40.2414 3
    endloop
  endfacet
  facet normal 0.5739 0.818926 0
    outer loop
      vertex 4.27463 40.4774 3
      vertex 4.61139 40.2414 2.4
      vertex 4.27463 40.4774 2.4
    endloop
  endfacet
  facet normal 0.318331 0.94798 -0
    outer loop
      vertex 5.03307 40.0998 2.4
      vertex 4.61139 40.2414 3
      vertex 5.03307 40.0998 3
    endloop
  endfacet
  facet normal 0.318331 0.94798 0
    outer loop
      vertex 4.61139 40.2414 3
      vertex 5.03307 40.0998 2.4
      vertex 4.61139 40.2414 2.4
    endloop
  endfacet
  facet normal 0.0927684 0.995688 -0
    outer loop
      vertex 5.53967 40.0526 2.4
      vertex 5.03307 40.0998 3
      vertex 5.53967 40.0526 3
    endloop
  endfacet
  facet normal 0.0927684 0.995688 0
    outer loop
      vertex 5.03307 40.0998 3
      vertex 5.53967 40.0526 2.4
      vertex 5.03307 40.0998 2.4
    endloop
  endfacet
  facet normal -0.0960079 0.995381 0
    outer loop
      vertex 6.04665 40.1015 2.4
      vertex 5.53967 40.0526 3
      vertex 6.04665 40.1015 3
    endloop
  endfacet
  facet normal -0.0960079 0.995381 0
    outer loop
      vertex 5.53967 40.0526 3
      vertex 6.04665 40.1015 2.4
      vertex 5.53967 40.0526 2.4
    endloop
  endfacet
  facet normal -0.325785 0.945444 0
    outer loop
      vertex 6.47267 40.2483 2.4
      vertex 6.04665 40.1015 3
      vertex 6.47267 40.2483 3
    endloop
  endfacet
  facet normal -0.325785 0.945444 0
    outer loop
      vertex 6.04665 40.1015 3
      vertex 6.47267 40.2483 2.4
      vertex 6.04665 40.1015 2.4
    endloop
  endfacet
  facet normal -0.578282 0.815837 0
    outer loop
      vertex 6.81775 40.4929 2.4
      vertex 6.47267 40.2483 3
      vertex 6.81775 40.4929 3
    endloop
  endfacet
  facet normal -0.578282 0.815837 0
    outer loop
      vertex 6.47267 40.2483 3
      vertex 6.81775 40.4929 2.4
      vertex 6.47267 40.2483 2.4
    endloop
  endfacet
  facet normal -0.796348 0.604839 0
    outer loop
      vertex 6.81775 40.4929 2.4
      vertex 7.07158 40.8271 3
      vertex 7.07158 40.8271 2.4
    endloop
  endfacet
  facet normal -0.796348 0.604839 0
    outer loop
      vertex 7.07158 40.8271 3
      vertex 6.81775 40.4929 2.4
      vertex 6.81775 40.4929 3
    endloop
  endfacet
  facet normal -0.938993 0.343936 0
    outer loop
      vertex 7.07158 40.8271 2.4
      vertex 7.22388 41.2429 3
      vertex 7.22388 41.2429 2.4
    endloop
  endfacet
  facet normal -0.938993 0.343936 0
    outer loop
      vertex 7.22388 41.2429 3
      vertex 7.07158 40.8271 2.4
      vertex 7.07158 40.8271 3
    endloop
  endfacet
  facet normal -0.994829 0.101564 0
    outer loop
      vertex 7.22388 41.2429 2.4
      vertex 7.27464 41.7401 3
      vertex 7.27464 41.7401 2.4
    endloop
  endfacet
  facet normal -0.994829 0.101564 0
    outer loop
      vertex 7.27464 41.7401 3
      vertex 7.22388 41.2429 2.4
      vertex 7.22388 41.2429 3
    endloop
  endfacet
  facet normal -0.996995 -0.0774686 0
    outer loop
      vertex 7.27464 41.7401 2.4
      vertex 7.2484 42.0778 3
      vertex 7.2484 42.0778 2.4
    endloop
  endfacet
  facet normal -0.996995 -0.0774686 0
    outer loop
      vertex 7.2484 42.0778 3
      vertex 7.27464 41.7401 2.4
      vertex 7.27464 41.7401 3
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 3.88301 38.8595 3
      vertex 3.88301 39.5596 2.4
      vertex 3.88301 39.5596 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 3.88301 39.5596 2.4
      vertex 3.88301 38.8595 3
      vertex 3.88301 38.8595 2.4
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 7.22717 38.8595 2.4
      vertex 3.88301 38.8595 3
      vertex 7.22717 38.8595 3
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 3.88301 38.8595 3
      vertex 7.22717 38.8595 2.4
      vertex 3.88301 38.8595 2.4
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 7.22717 38.8595 2.4
      vertex 7.22717 39.5596 3
      vertex 7.22717 39.5596 2.4
    endloop
  endfacet
  facet normal -1 -0 0
    outer loop
      vertex 7.22717 39.5596 3
      vertex 7.22717 38.8595 2.4
      vertex 7.22717 38.8595 3
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 3.88301 39.5596 2.4
      vertex 7.22717 39.5596 3
      vertex 3.88301 39.5596 3
    endloop
  endfacet
  facet normal 0 -1 -0
    outer loop
      vertex 7.22717 39.5596 3
      vertex 3.88301 39.5596 2.4
      vertex 7.22717 39.5596 2.4
    endloop
  endfacet
  facet normal -0.948094 -0.317991 0
    outer loop
      vertex 8.21478 33.883 2.4
      vertex 8.15149 34.0717 3
      vertex 8.15149 34.0717 2.4
    endloop
  endfacet
  facet normal -0.948094 -0.317991 0
    outer loop
      vertex 8.15149 34.0717 3
      vertex 8.21478 33.883 2.4
      vertex 8.21478 33.883 3
    endloop
  endfacet
  facet normal -0.835528 -0.549448 0
    outer loop
      vertex 8.15149 34.0717 2.4
      vertex 8.04601 34.2321 3
      vertex 8.04601 34.2321 2.4
    endloop
  endfacet
  facet normal -0.835528 -0.549448 0
    outer loop
      vertex 8.04601 34.2321 3
      vertex 8.15149 34.0717 2.4
      vertex 8.15149 34.0717 3
    endloop
  endfacet
  facet normal -0.669972 -0.742386 0
    outer loop
      vertex 7.88567 34.3768 2.4
      vertex 8.04601 34.2321 3
      vertex 7.88567 34.3768 3
    endloop
  endfacet
  facet normal -0.669972 -0.742386 -0
    outer loop
      vertex 8.04601 34.2321 3
      vertex 7.88567 34.3768 2.4
      vertex 8.04601 34.2321 2.4
    endloop
  endfacet
  facet normal -0.526759 -0.850015 0
    outer loop
      vertex 7.65782 34.518 2.4
      vertex 7.88567 34.3768 3
      vertex 7.65782 34.518 3
    endloop
  endfacet
  facet normal -0.526759 -0.850015 -0
    outer loop
      vertex 7.88567 34.3768 3
      vertex 7.65782 34.518 2.4
      vertex 7.88567 34.3768 2.4
    endloop
  endfacet
  facet normal -0.422798 -0.906224 0
    outer loop
      vertex 7.36246 34.6558 2.4
      vertex 7.65782 34.518 3
      vertex 7.36246 34.6558 3
    endloop
  endfacet
  facet normal -0.422798 -0.906224 -0
    outer loop
      vertex 7.65782 34.518 3
      vertex 7.36246 34.6558 2.4
      vertex 7.65782 34.518 2.4
    endloop
  endfacet
  facet normal -0.351776 -0.936084 0
    outer loop
      vertex 4.65913 35.6717 2.4
      vertex 7.36246 34.6558 3
      vertex 4.65913 35.6717 3
    endloop
  endfacet
  facet normal -0.351776 -0.936084 -0
    outer loop
      vertex 7.36246 34.6558 3
      vertex 4.65913 35.6717 2.4
      vertex 7.36246 34.6558 2.4
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 4.65913 34.9739 3
      vertex 4.65913 35.6717 2.4
      vertex 4.65913 35.6717 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 4.65913 35.6717 2.4
      vertex 4.65913 34.9739 3
      vertex 4.65913 34.9739 2.4
    endloop
  endfacet
  facet normal 0.298842 0.954303 -0
    outer loop
      vertex 5.87196 34.5941 2.4
      vertex 4.65913 34.9739 3
      vertex 5.87196 34.5941 3
    endloop
  endfacet
  facet normal 0.298842 0.954303 0
    outer loop
      vertex 4.65913 34.9739 3
      vertex 5.87196 34.5941 2.4
      vertex 4.65913 34.9739 2.4
    endloop
  endfacet
  facet normal 0.266637 0.963797 -0
    outer loop
      vertex 6.4297 34.4398 2.4
      vertex 5.87196 34.5941 3
      vertex 6.4297 34.4398 3
    endloop
  endfacet
  facet normal 0.266637 0.963797 0
    outer loop
      vertex 5.87196 34.5941 3
      vertex 6.4297 34.4398 2.4
      vertex 5.87196 34.5941 2.4
    endloop
  endfacet
  facet normal 0.254346 0.967113 -0
    outer loop
      vertex 6.65518 34.3805 2.4
      vertex 6.4297 34.4398 3
      vertex 6.65518 34.3805 3
    endloop
  endfacet
  facet normal 0.254346 0.967113 0
    outer loop
      vertex 6.4297 34.4398 3
      vertex 6.65518 34.3805 2.4
      vertex 6.4297 34.4398 2.4
    endloop
  endfacet
  facet normal 0.269292 -0.963059 0
    outer loop
      vertex 6.32974 34.2895 2.4
      vertex 6.65518 34.3805 3
      vertex 6.32974 34.2895 3
    endloop
  endfacet
  facet normal 0.269292 -0.963059 0
    outer loop
      vertex 6.65518 34.3805 3
      vertex 6.32974 34.2895 2.4
      vertex 6.65518 34.3805 2.4
    endloop
  endfacet
  facet normal 0.289444 -0.957195 0
    outer loop
      vertex 6.06551 34.2096 2.4
      vertex 6.32974 34.2895 3
      vertex 6.06551 34.2096 3
    endloop
  endfacet
  facet normal 0.289444 -0.957195 0
    outer loop
      vertex 6.32974 34.2895 3
      vertex 6.06551 34.2096 2.4
      vertex 6.32974 34.2895 2.4
    endloop
  endfacet
  facet normal 0.320926 -0.947104 0
    outer loop
      vertex 5.86247 34.1408 2.4
      vertex 6.06551 34.2096 3
      vertex 5.86247 34.1408 3
    endloop
  endfacet
  facet normal 0.320926 -0.947104 0
    outer loop
      vertex 6.06551 34.2096 3
      vertex 5.86247 34.1408 2.4
      vertex 6.06551 34.2096 2.4
    endloop
  endfacet
  facet normal 0.31792 -0.948118 0
    outer loop
      vertex 4.65913 33.7373 2.4
      vertex 5.86247 34.1408 3
      vertex 4.65913 33.7373 3
    endloop
  endfacet
  facet normal 0.31792 -0.948118 0
    outer loop
      vertex 5.86247 34.1408 3
      vertex 4.65913 33.7373 2.4
      vertex 5.86247 34.1408 2.4
    endloop
  endfacet
  facet normal 1 -0 0
    outer loop
      vertex 4.65913 33.0324 3
      vertex 4.65913 33.7373 2.4
      vertex 4.65913 33.7373 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 4.65913 33.7373 2.4
      vertex 4.65913 33.0324 3
      vertex 4.65913 33.0324 2.4
    endloop
  endfacet
  facet normal -0.371083 0.9286 0
    outer loop
      vertex 7.20107 34.0482 2.4
      vertex 4.65913 33.0324 3
      vertex 7.20107 34.0482 3
    endloop
  endfacet
  facet normal -0.371083 0.9286 0
    outer loop
      vertex 4.65913 33.0324 3
      vertex 7.20107 34.0482 2.4
      vertex 4.65913 33.0324 2.4
    endloop
  endfacet
  facet normal 0.369682 0.929158 -0
    outer loop
      vertex 7.35112 33.9885 2.4
      vertex 7.20107 34.0482 3
      vertex 7.35112 33.9885 3
    endloop
  endfacet
  facet normal 0.369682 0.929158 0
    outer loop
      vertex 7.20107 34.0482 3
      vertex 7.35112 33.9885 2.4
      vertex 7.20107 34.0482 2.4
    endloop
  endfacet
  facet normal 0.427879 0.903836 -0
    outer loop
      vertex 7.46899 33.9327 2.4
      vertex 7.35112 33.9885 3
      vertex 7.46899 33.9327 3
    endloop
  endfacet
  facet normal 0.427879 0.903836 0
    outer loop
      vertex 7.35112 33.9885 3
      vertex 7.46899 33.9327 2.4
      vertex 7.35112 33.9885 2.4
    endloop
  endfacet
  facet normal 0.517239 0.855841 -0
    outer loop
      vertex 7.5547 33.8809 2.4
      vertex 7.46899 33.9327 3
      vertex 7.5547 33.8809 3
    endloop
  endfacet
  facet normal 0.517239 0.855841 0
    outer loop
      vertex 7.46899 33.9327 3
      vertex 7.5547 33.8809 2.4
      vertex 7.46899 33.9327 2.4
    endloop
  endfacet
  facet normal 0.636325 0.771421 -0
    outer loop
      vertex 7.61774 33.8289 2.4
      vertex 7.5547 33.8809 3
      vertex 7.61774 33.8289 3
    endloop
  endfacet
  facet normal 0.636325 0.771421 0
    outer loop
      vertex 7.5547 33.8809 3
      vertex 7.61774 33.8289 2.4
      vertex 7.5547 33.8809 2.4
    endloop
  endfacet
  facet normal 0.74752 0.66424 0
    outer loop
      vertex 7.66759 33.7728 3
      vertex 7.61774 33.8289 2.4
      vertex 7.61774 33.8289 3
    endloop
  endfacet
  facet normal 0.74752 0.66424 0
    outer loop
      vertex 7.61774 33.8289 2.4
      vertex 7.66759 33.7728 3
      vertex 7.66759 33.7728 2.4
    endloop
  endfacet
  facet normal 0.855048 0.51855 0
    outer loop
      vertex 7.70422 33.7124 3
      vertex 7.66759 33.7728 2.4
      vertex 7.66759 33.7728 3
    endloop
  endfacet
  facet normal 0.855048 0.51855 0
    outer loop
      vertex 7.66759 33.7728 2.4
      vertex 7.70422 33.7124 3
      vertex 7.70422 33.7124 2.4
    endloop
  endfacet
  facet normal 0.9381 0.346365 0
    outer loop
      vertex 7.72929 33.6445 3
      vertex 7.70422 33.7124 2.4
      vertex 7.70422 33.7124 3
    endloop
  endfacet
  facet normal 0.9381 0.346365 0
    outer loop
      vertex 7.70422 33.7124 2.4
      vertex 7.72929 33.6445 3
      vertex 7.72929 33.6445 2.4
    endloop
  endfacet
  facet normal 0.982202 0.187829 0
    outer loop
      vertex 7.74434 33.5658 3
      vertex 7.72929 33.6445 2.4
      vertex 7.72929 33.6445 3
    endloop
  endfacet
  facet normal 0.982202 0.187829 0
    outer loop
      vertex 7.72929 33.6445 2.4
      vertex 7.74434 33.5658 3
      vertex 7.74434 33.5658 2.4
    endloop
  endfacet
  facet normal 0.998447 0.0557169 0
    outer loop
      vertex 7.74934 33.4762 3
      vertex 7.74434 33.5658 2.4
      vertex 7.74434 33.5658 3
    endloop
  endfacet
  facet normal 0.998447 0.0557169 0
    outer loop
      vertex 7.74434 33.5658 2.4
      vertex 7.74934 33.4762 3
      vertex 7.74934 33.4762 2.4
    endloop
  endfacet
  facet normal 0.999575 -0.0291543 0
    outer loop
      vertex 7.74724 33.4042 3
      vertex 7.74934 33.4762 2.4
      vertex 7.74934 33.4762 3
    endloop
  endfacet
  facet normal 0.999575 -0.0291543 0
    outer loop
      vertex 7.74934 33.4762 2.4
      vertex 7.74724 33.4042 3
      vertex 7.74724 33.4042 2.4
    endloop
  endfacet
  facet normal 0.996612 -0.0822497 0
    outer loop
      vertex 7.74091 33.3275 3
      vertex 7.74724 33.4042 2.4
      vertex 7.74724 33.4042 3
    endloop
  endfacet
  facet normal 0.996612 -0.0822497 0
    outer loop
      vertex 7.74724 33.4042 2.4
      vertex 7.74091 33.3275 3
      vertex 7.74091 33.3275 2.4
    endloop
  endfacet
  facet normal 0.99171 -0.128496 0
    outer loop
      vertex 7.73035 33.246 3
      vertex 7.74091 33.3275 2.4
      vertex 7.74091 33.3275 3
    endloop
  endfacet
  facet normal 0.99171 -0.128496 0
    outer loop
      vertex 7.74091 33.3275 2.4
      vertex 7.73035 33.246 3
      vertex 7.73035 33.246 2.4
    endloop
  endfacet
  facet normal 0 1 -0
    outer loop
      vertex 8.20505 33.246 2.4
      vertex 7.73035 33.246 3
      vertex 8.20505 33.246 3
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 7.73035 33.246 3
      vertex 8.20505 33.246 2.4
      vertex 7.73035 33.246 2.4
    endloop
  endfacet
  facet normal -0.991008 0.133802 0
    outer loop
      vertex 8.20505 33.246 2.4
      vertex 8.22217 33.3728 3
      vertex 8.22217 33.3728 2.4
    endloop
  endfacet
  facet normal -0.991008 0.133802 0
    outer loop
      vertex 8.22217 33.3728 3
      vertex 8.20505 33.246 2.4
      vertex 8.20505 33.246 3
    endloop
  endfacet
  facet normal -0.997319 0.0731794 0
    outer loop
      vertex 8.22217 33.3728 2.4
      vertex 8.23245 33.5129 3
      vertex 8.23245 33.5129 2.4
    endloop
  endfacet
  facet normal -0.997319 0.0731794 0
    outer loop
      vertex 8.23245 33.5129 3
      vertex 8.22217 33.3728 2.4
      vertex 8.22217 33.3728 3
    endloop
  endfacet
  facet normal -0.999748 0.0224486 0
    outer loop
      vertex 8.23245 33.5129 2.4
      vertex 8.23589 33.6661 3
      vertex 8.23589 33.6661 2.4
    endloop
  endfacet
  facet normal -0.999748 0.0224486 0
    outer loop
      vertex 8.23589 33.6661 3
      vertex 8.23245 33.5129 2.4
      vertex 8.23245 33.5129 3
    endloop
  endfacet
  facet normal -0.995297 -0.0968683 0
    outer loop
      vertex 8.23589 33.6661 2.4
      vertex 8.21478 33.883 3
      vertex 8.21478 33.883 2.4
    endloop
  endfacet
  facet normal -0.995297 -0.0968683 0
    outer loop
      vertex 8.21478 33.883 3
      vertex 8.23589 33.6661 2.4
      vertex 8.23589 33.6661 3
    endloop
  endfacet
endsolid OpenSCAD_Model
```
