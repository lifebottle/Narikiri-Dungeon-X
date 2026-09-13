::GimConv.exe font1-1.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-1.gim
::GimConv.exe font1-2.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-2.gim
::GimConv.exe font1-3.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-3.gim
::GimConv.exe font1-4.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-4.gim
::GimConv.exe font1-5.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-5.gim

::the command used for the font need the script to strip the palette size
::gimconv.exe -ndxfont font1-1.png -N -o font1-1.gim --filter_script2 ReducePalette
::gimconv.exe -ndxfont font1-2.png -N -o font1-2.gim --filter_script2 ReducePalette
::gimconv.exe -ndxfont font1-3.png -N -o font1-3.gim --filter_script2 ReducePalette
::gimconv.exe -ndxfont font1-4.png -N -o font1-4.gim --filter_script2 ReducePalette
::gimconv.exe -ndxfont font1-5.png -N -o font1-5.gim --filter_script2 ReducePalette

:: the command for the battlegui if the script is used no update info will be present
::need to reduce the palette to the size of the palette in the file in optpix
::gimconv.exe -ndxbattlegui B_STATE03_test_optix.png -o B_STATE03_test_optix.gim 
::gimconv.exe -ndxbattlegui B_STATE03_test_optix.png -o B_STATE03_test_optix.gim --filter_script2 ReducePalette

::the menutex seems to have the optix setting to have the palette be alpha ordered
::gimconv.exe -ndxmenutex 0296.png -o 0296.gim

::the town name need to have their palette be alpha ordered and reduce to 16 colors
gimconv.exe -ndxtownname TOWNNAME00.png -o TOWNNAME00.gim

pause