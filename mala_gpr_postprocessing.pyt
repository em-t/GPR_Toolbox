import arcpy

import gpr_postprocessing


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [ProcessCorFile]


class ProcessCorFile:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Process .cor file"
        self.description = ""

    def getParameterInfo(self):
        param_input_cor_file = arcpy.Parameter(
            displayName="Input .cor file",
            name="input_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
            multiValue=True
        )
        param_input_cor_file.filter.list = ["cor"]

        param_lidar_DEM = arcpy.Parameter(
            displayName="Lidar DEM raster",
            name="dem_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )

        param_output_cor_file = arcpy.Parameter(
            displayName="Output directory",
            name="output_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )

        params = [param_input_cor_file, param_lidar_DEM, param_output_cor_file]
        return params

    def isLicensed(self):
        try:
            if arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception:
            return False

        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.CheckOutExtension("Spatial")

        input_files = parameters[0].valueAsText.split(";")
        input_files = [f.replace("\\", "/") for f in input_files]

        lidar_dem = parameters[1]

        output_dir = parameters[2].valueAsText.replace("\\", "/")

        gpr_postprocessing.process_cor(input_files, lidar_dem, output_dir)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
