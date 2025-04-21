You can install the components referred in the requirements.txt using pip install -r <"pathTo">/requirements.txt

If your python environment is newer than 3.10, it might be possible that you may encounter errors when attempting to install the chromadb package. This will require installing the Visual C++ build tool at: https://visualstudio.microsoft.com/visual-cpp-build-tools/ 

1. In the application navigate to "Individual Components" and find enable the two components for install:
   - MSVC v143 - VS 2022 C++ x64/x86 build tools (Latest)
   - Windows 11 SDK (Latest version)

Note that some models will automatically be downloaded onto your machine when running the Main.py file with the integrated memory component. 