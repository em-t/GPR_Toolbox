import arcpy
import os
import pandas as pd
import sys
import traceback

from arcgis.features import GeoAccessor, GeoSeriesAccessor

from utils import (
    feature_class_to_dataframe,
    reset_workspace,
    set_temporary_fgdb_workspace
)


SEPARATOR = "\t"
COLNAMES = ["ID", "DATE", "LOCAL_TIME", "LATITUDE", "N_S", "LONGITUDE", "E_W", "GPS_ELEVATION", "ELEVATION_UNIT", "UNKNOWN"]

def process_cor(cor_files, lidar_dem_raster, output_dir):
    if (len(cor_files)) == 0:
        arcpy.AddWarning("No .cor files provided.")
        return None
    
    temp_scratch_gdb_path, original_scratch_workspace = set_temporary_fgdb_workspace("cor_temp.gdb")

    original_output_crs = arcpy.env.outputCoordinateSystem
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3067)

    desc = arcpy.Describe(lidar_dem_raster)
    
    try:
        for i in range(len(cor_files)):
            f = cor_files[i]
            df = pd.read_csv(f, sep=SEPARATOR, names=COLNAMES)
            dfc = df.set_index(keys="ID", drop=False)

            temp_fc = arcpy.CreateScratchName("Extr", f"{i}", "FeatureClass", arcpy.env.scratchWorkspace)

            sdf = pd.DataFrame.spatial.from_xy(
                df=dfc,
                x_column="LONGITUDE",
                y_column="LATITUDE",
                sr=104129
            )
            
            sdf.spatial.to_featureclass(location=temp_fc, overwrite=True)

            temp_elev_points = get_elevation_at_points(temp_fc, desc.catalogPath)

            arcpy.management.CalculateGeometryAttributes(
                in_features=temp_elev_points,
                geometry_property=[["N", "POINT_Y"], ["E", "POINT_X"]],
                length_unit="METERS"
            )

            # "RASTERVALU" contains the extracted elevation
            new_df = feature_class_to_dataframe(input_fc=temp_elev_points, input_fields=["N", "E", "RASTERVALU"], index_field="ID")

            dfc["GPS_ELEVATION"] = new_df["RASTERVALU"].values
            dfc["LONGITUDE"] = new_df["E"]
            dfc["LATITUDE"] = new_df["N"]
            
            if not os.path.exists(output_dir):
                raise ValueError(f"Output directory does not exist. Check path: {output_dir}")

            filename = os.path.join(output_dir, os.path.basename(f))
            log_message = f"Created modified .cor file: {filename}"
            if os.path.exists(filename):
                log_message = f"A file with path {filename} already existed. File was replaced with the new output."
            
            dfc.to_csv(filename, sep=SEPARATOR, header=False, index=False)

            arcpy.AddMessage(log_message)

    except arcpy.ExecuteError:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        arcpy.AddError(f"ExecuteError when trying to process .cor file: {tbinfo}\n{sys.exc_info()[1]}")
    except Exception:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        arcpy.AddError(f"Unable to process .cor file. Exception: {tbinfo}\n{sys.exc_info()[1]}")
    
    reset_workspace(temp_scratch_gdb_path, original_scratch_workspace)
    arcpy.env.outputCoordinateSystem = original_output_crs

    return None


def get_elevation_at_points(gpr_points, dem_raster):
    output_tmp_feature = arcpy.CreateScratchName("Values", "", "FeatureClass", arcpy.env.scratchWorkspace)
    arcpy.sa.ExtractValuesToPoints(in_point_features=gpr_points, in_raster=dem_raster, out_point_features=output_tmp_feature)

    return output_tmp_feature
