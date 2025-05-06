import arcpy
import pandas as pd
import os

from pathlib import Path


def set_temporary_fgdb_workspace(gdb_name: str, is_scratch_workspace: bool=True):
    """
    Note! It is up to the caller to set the scratch workspace back to the original
    and handle deletion of temporary scratch dir and its contents.
    """
    if not gdb_name.endswith(".gdb"):
        gdb_name = f"{gdb_name}.gdb"

    if is_scratch_workspace:
        original_workspace_path = arcpy.env.scratchWorkspace
    else:
        original_workspace_path = arcpy.env.workspace

    project = arcpy.mp.ArcGISProject('CURRENT')
    project_toolbox_path = Path(project.filePath)
    # It's necessary to have path string in posix format for CreateFileGDB to work
    project_dir = str(project_toolbox_path.parent.as_posix())

    temp_fgdb_result = arcpy.management.CreateFileGDB(project_dir, gdb_name)
    temp_workspace_path = temp_fgdb_result[0]

    if is_scratch_workspace:
        arcpy.env.scratchWorkspace = temp_workspace_path
    else:
        arcpy.env.workspace = temp_workspace_path

    return temp_workspace_path, original_workspace_path


def reset_workspace(temp_workspace_path: str, original_workspace_path: str, is_scratch_workspace: bool=True):
    """
    Reset the workspace environment setting back to its original value. Delete the temporary workspace and its contents.

    Args:
        temp_workspace_path: <str>
            Path to the temporary workspace that will be unset and deleted.
        original_workspace_path: <str>
            Path that will be reset as the workspace.
        is_scratch_workspace: <bool>
            If True, resets arcpy.env.scratchWorkspace (default).
            If False, resets arcpy.env.workspace.
    """
    if is_scratch_workspace:
        arcpy.env.scratchWorkspace = original_workspace_path
    else:
        arcpy.env.workspace = original_workspace_path
    
    for file in inventory_data(temp_workspace_path, None):
        arcpy.management.Delete(file)
    
    arcpy.management.Delete(temp_workspace_path)


def inventory_data(workspace, datatypes):
    """
    Generates full path names under a catalog tree for all requested
    datatype(s).

    Source: https://arcpy.wordpress.com/2012/12/10/inventorying-data-a-new-approach/
 
    Parameters:
    workspace: string
        The top-level workspace that will be used.
    datatypes: string | list | tuple
        Keyword(s) representing the desired datatypes. A single
        datatype can be expressed as a string, otherwise use
        a list or tuple. See arcpy.da.Walk documentation 
        for a full list.
    """
    for path, _, data_names in arcpy.da.Walk(
            workspace, datatype=datatypes):
        for data_name in data_names:
            yield os.path.join(path, data_name)


# Modified from this: https://community.esri.com/t5/python-questions/stand-alone-table-to-pandas-data-frame/td-p/1349915
def feature_class_to_dataframe(input_fc: str, input_fields: list = None, index_field = "id", query: str = ""):
    """Converts a feature class to a pandas dataframe. If 
    no input fields are specified, all fields
    will be included. If a query is specified, only those
    features will be included in the dataframe.

    This is an excellent function to use when exploring data
    without having to queue up ArcGIS Pro. Particularly good
    for using pandas to generate unique field values.

    Args:
        input_fc (string): path to the input feature class
        input_fields (list, optional): List of fields for dataframe. 
            Defaults to None.
        query (str, optional): Pandas query. Defaults to "".

    Returns:
        Pandas Dataframe: Dataframe of feature class
    """

    # get list of fields if desired fields specified
    if input_fields:
        final_fields = [index_field] + input_fields

    # use all fields if no fields specified
    else:
        final_fields = [field.name for field in arcpy.ListFields(input_fc)]

    # build dataframe row by row using search cursor
    data = [row for row in arcpy.da.SearchCursor(
        input_fc, final_fields, where_clause=query)]
    fc_dataframe = pd.DataFrame(data, columns=final_fields)

    # set index to object id
    fc_dataframe = fc_dataframe.set_index(index_field, drop=True)
    
    return fc_dataframe
