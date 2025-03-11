import argparse, os, sys, re, warnings, io, collections, collections.abc, contextlib, shutil, logging, time
from datetime import datetime, timedelta
from itertools import zip_longest
# import datetime #from datetime import datetime
import math
import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree import ElementPath
from jinja2 import FileSystemLoader,Environment
from io import StringIO
from enum import Enum


def header_conversion(df_sensor_header):
  result_sensor_header = [value.replace('#', 'nb.') for value in df_sensor_header]
  result_sensor_header = [value.replace('%', 'pc.') for value in result_sensor_header]
  result_sensor_header = [value.replace('^', '_') for value in result_sensor_header]
  result_sensor_header = [value.replace('/', '_') for value in result_sensor_header]
  result_sensor_header = [value.replace('@', 'at.') for value in result_sensor_header]
  result_sensor_header = [value.replace(' ', '_') for value in result_sensor_header]
  return result_sensor_header


def add_df_sensor_timestamp(df_sensor,header_date):
    list_timestamp = []
    list_elasped_time = df_sensor['Elasped_Time'].astype(float).tolist()
    
    for ela_time in list_elasped_time:
        el_datetime = header_date + timedelta(milliseconds=int(ela_time*1000))
        list_timestamp.append(el_datetime.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3])
    
    return list_timestamp


def is_number_or_float(sample_str):
    ''' Returns True if the string contains only
        number or float '''
    result = True
    if re.search("[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$", sample_str) is None:
        result = False
    return result


######################
#    Del Lock func   #
######################
# def is_lock_file_expired(lock_file_path):
#     if not os.path.exists(lock_file_path):
#         return False

#     file_stats = os.stat(lock_file_path)
#     file_modified_time = file_stats.st_mtime

#     current_time = time.time()
#     time_diff = current_time - file_modified_time
#     time_diff_minutes = time_diff / 15
#     return time_diff_minutes >= 15


def main():
    ########################
    #    Setup Arguments   #
    ########################
    parser = argparse.ArgumentParser()
    parser.add_argument("pos1", help="positional argument 1")
    parser.add_argument("pos2", help="positional argument 2")
    parser.add_argument("-outdir",help="output folder",dest="outdir",default="outdir/")
    parser.add_argument("-logdir",help="log folder",dest="logdir",default="logdir/")
    parser.add_argument("-refdir",help="reference folder",dest="refdir")
    parser.add_argument("-lockdir",help="lock folder",dest="lockdir")
    parser.add_argument("-ext","--extension",help="file extension",dest="fileext",default="log")
    args = parser.parse_args()
    print("Executing FDC Script SOCAL Trion RIE ICP ... •ᴗ• ")
    print(args)
    input_filepath = args.pos1
    tool_id = args.pos2
    outdir = args.outdir
    logdir = args.logdir
    refdir = args.refdir
    lockdir = args.lockdir
    fileext = args.fileext
    if lockdir is None: lockdir = r'/'
    print(f"... output files in context split mode")
    processed_path = os.path.join(input_filepath, "Processed/")
    notprocessed_path = os.path.join(input_filepath, "NotProcessed/")
    if not os.path.exists(processed_path): os.makedirs(processed_path)
    if not os.path.exists(notprocessed_path): os.makedirs(notprocessed_path)
    

    


    ########################
    #    Run By Filename   #
    ########################
    Cache_Folder_File = os.listdir(input_filepath)
    for Cache_Filename in Cache_Folder_File:
        try:
            if Cache_Filename[-3:] == fileext and not os.path.exists(lockdir + Cache_Filename[:-3] + "lock"):
                if not len(lockdir) == 1:
                    with open(lockdir + Cache_Filename[:-3] + "lock", 'w') as f:
                        f.write('Lock File Content and File Path:' + lockdir + Cache_Filename[:-3] + "lock")
                # Put Filename in Logging

                #######################
                #    Setup Log File   #
                #######################
                current_dateTime = datetime.today()
                by_filename_logger: logging.Logger = logging.getLogger(name=Cache_Filename)
                FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
                logging.basicConfig(filename=logdir + str(current_dateTime.strftime('%Y%m%d')) + 'example.log', level=logging.DEBUG, format=FORMAT)

                #####################
                #  Load Input File  #
                #####################

                # Extract waferID
                waferID = pd.read_csv(input_filepath + Cache_Filename, header=None, nrows=1).iloc[0].str.strip()
                waferID = waferID.iloc[0].replace("C:\\Process Data\\", "")
                print(f">>> Wafer: {waferID}")

                # Extract Username
                username = pd.read_csv(input_filepath + Cache_Filename, header=None, skiprows=2, nrows=1).iloc[0].str.strip()
                username = username.iloc[0].replace("Username: ", "")
                print(f">>> Username: {username}")

                # Extract RecipeID
                recipeID = pd.read_csv(input_filepath + Cache_Filename, header=None, skiprows=4, nrows=1).iloc[0].str.strip()
                recipeID = recipeID.iloc[0].replace("Recipe: ", "")
                print(f">>> Recipe: {recipeID}")

                # Extract Time Related
                header_date_time = pd.read_csv(input_filepath + Cache_Filename, skiprows=5, nrows=2, header=None)
                str_header_date = header_date_time.iloc[0].str.strip().iloc[0].replace("Date: ", "")
                str_header_time = header_date_time.iloc[1].str.strip().iloc[0].replace("Start Time: ", "")
                header_date = pd.to_datetime(str_header_date + " " + str_header_time, format='%m/%d/%Y %I:%M:%S %p')
                print(f">>> Header Date: {header_date}")

                # Calculate Lot ID & Wafer ID
                lot_id = '_'.join(Cache_Filename.split('_')[2:]).split('.')[0]
                wafer_id = lot_id + "_" + header_date.strftime("%Y%m%d%H%M%S")
                material_id = lot_id

                # Get operation status
                operation_value = "NA"
                with open(input_filepath + Cache_Filename, 'r') as file:
                    # Read all line
                    lines = file.readlines()
                    # Start from the last line
                    for line in reversed(lines):
                        first_tab_string = line.strip().split("\t")[0]
                        is_summary_string = any(char.isalpha() for char in first_tab_string)
                        
                        if is_summary_string:
                            if "COMPLETED" in first_tab_string:
                                operation_value = "completed"
                                print(first_tab_string)
                                break
                            if "ABORTED" in first_tab_string:
                                operation_value = "aborted"
                                print(first_tab_string)
                                break
                        else:
                            print("Summary keyword not found")
                            break

                #########################
                #    New Output XML     #
                #########################

                Output_FileName = header_date.strftime("%Y%m%d%H%M%S") + "_" + tool_id.replace('/', '_') + "_" + lot_id.replace('/', '_') + ".exntrace"

                env = Environment(loader=FileSystemLoader("../SOCAL_TrionRIEICP/templates/"))
                template = env.get_template('process_context_trionrieicp.xml')
                content = template.render(
                    tool_id=tool_id,
                    module="Module",
                    recipe_name=recipeID,
                    material_id=material_id,
                    lot_id=lot_id,
                    wafer_id=wafer_id,
                    current_user=username,
                    operation=operation_value
                )
                with open(outdir + Output_FileName, mode="w", encoding="utf-8") as message:
                    message.write(content)
                    message.write("\n\n")

                # Extract header by line 9,10,11
                selected_row_9 = pd.read_csv(input_filepath + Cache_Filename, sep='\t', skiprows=8, nrows=1, header=None, na_filter=False).iloc[0].str.strip()
                selected_row_10 = pd.read_csv(input_filepath + Cache_Filename, sep='\t', skiprows=9, nrows=1, header=None, na_filter=False).iloc[0].str.strip()
                selected_row_11 = pd.read_csv(input_filepath + Cache_Filename, sep='\t', skiprows=10, nrows=1, header=None, na_filter=False).iloc[0].str.strip()
                # Convert the row to a list
                df_sensor_header = []
                df_sensor_header_length = max(selected_row_9.size, selected_row_10.size, selected_row_11.size)
                for i in range(df_sensor_header_length):  # iterates from {{ 0 }} to {{ df_sensor_header_length }}
                    header_column_i = str(selected_row_10.iloc[i])
                    if selected_row_9.size > i and str(selected_row_9.iloc[i]) != "" :
                        header_column_i = str(selected_row_9.iloc[i])+"_"+header_column_i
                    if selected_row_11.size > i and str(selected_row_11.iloc[i]) != "" :
                        header_column_i = header_column_i+"_"+str(selected_row_11.iloc[i])
                    df_sensor_header.append(header_column_i)
                df_sensor_header = header_conversion(df_sensor_header)
                df_sensor_header_ordered = df_sensor_header.copy()
                df_sensor_header_ordered.insert(0,'TimeStamp')
                df_sensor_header_ordered.insert(1,'StepID')
                header_row = "\t".join(str(item) for item in df_sensor_header_ordered)
                with open(outdir + Output_FileName, mode="a") as f:
                    f.write(header_row)
                    f.write("\n")


                # Read the rest of the file skipping the first 12 rows (8 + 4)
                chunksize = 10 ** 4

                for chunk in pd.read_csv(input_filepath + Cache_Filename, sep='\t', skiprows=12, header=None, chunksize=chunksize):
                    merged_df = pd.DataFrame()
                    # chunk is a DataFrame. To "process" the rows in the chunk:
                    for index, df_sensor in chunk.iterrows():
                        # Skip 0 column
                        if float(df_sensor.iloc[1]) == 0 :
                            continue
                        
                        df_sensor = pd.DataFrame(df_sensor).transpose().reset_index(drop=True)
                        df_sensor.columns = df_sensor_header

                        isData = is_number_or_float(str(df_sensor['Sample'].values[0]))
                        
                        if isData:
                            el_datetime = header_date + timedelta(milliseconds=int(float(df_sensor['Elasped_Time'].values[0])*1000))
                            df_sensor['TimeStamp']=el_datetime.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]
                            df_sensor['StepID'] = int(df_sensor['Step_nb.'].values[0])
                            df_sensor = df_sensor[df_sensor_header_ordered]
                            
                            merged_df = pd.concat([merged_df, df_sensor], axis=0)
                        else:
                            df_sensor_summary = str(df_sensor['Sample'].values[0])
                            break

                    with open(outdir + Output_FileName, mode="a") as f:
                        f.write(merged_df.to_csv(path_or_buf=None, index=False, sep='\t', header=False))

                ###########################
                #    Move to Processed    #
                ###########################
                shutil.move(input_filepath + Cache_Filename[:-4] + "." + fileext, processed_path + Cache_Filename[:-4] + "." + fileext)
                if os.path.exists(lockdir + Cache_Filename[:-3] + "lock") and not len(lockdir) == 1: os.remove(lockdir + Cache_Filename[:-3] + "lock")
        except Exception as ex:
            print('Exception Messages: ' + str(ex))
            if lockdir is not None:
                if os.path.exists(lockdir + Cache_Filename[:-3] + "lock") and not len(lockdir) == 1: os.remove(lockdir + Cache_Filename[:-3] + "lock")
            if not os.path.exists(input_filepath + Cache_Filename[:-4] + "." + fileext):
                print('Input File Doesn\'t Exist: ' + refdir + Cache_Filename[:-4] + "." + fileext)
                by_filename_logger.error('Input File Doesn\'t Exist: ' + refdir + Cache_Filename[:-4] + "." + fileext)
            else:
                shutil.move(input_filepath + Cache_Filename[:-4] + "." + fileext, notprocessed_path + Cache_Filename[:-4] + "." + fileext)
            print('Exception Messages: ' + str(ex))
            by_filename_logger.error('Exception Messages: ' + str(ex))
            import traceback
            traceback.print_exc()
            print("Debug Mode exception:")
            ## sys.exit()
        
            

    

main()
