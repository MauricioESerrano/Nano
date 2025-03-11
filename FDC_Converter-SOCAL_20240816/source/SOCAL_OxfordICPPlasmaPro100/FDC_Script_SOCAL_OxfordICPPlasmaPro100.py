import argparse, os, sys, re, warnings, io, collections, collections.abc, contextlib, shutil, logging, time, csv
from datetime import datetime, timedelta
# import datetime #from datetime import datetime
import math
import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree import ElementPath
from jinja2 import FileSystemLoader,Environment
from io import StringIO
from enum import Enum



def datetime_conversion(datetime_str, mode):
    formatted_datetime = datetime_str
    # Convert string to datetime object
    dt_object = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
    # dt_object = datetime.strptime(datetime_str[:-9], "%Y-%m-%dT%H:%M:%S.%f")
    if mode == 1:
        # Format the datetime object as "YYYYMMDDhhmmss"
        formatted_datetime = dt_object.strftime("%Y%m%d%H%M%S")
    elif mode == 2:
        # Format the datetime object as "YYYY/MM/DD hh:mm:ss.SSS"
        formatted_datetime = dt_object.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]
    elif mode == 3:
        # Format the datetime object as "YYYYMMDD_hhmmss"
        formatted_datetime = dt_object.strftime("%Y%m%d_%H%M%S")

    return formatted_datetime

def extract_milliseconds(offset):
    # Transfer the Offset to Milliseconds
    offset_str = str(offset)
    
    # Find the index of the '.'
    decimal_index = offset_str.find('.')
    
    # If the number after '.' is less than 3, fill 0 in.
    if decimal_index != -1:
        milliseconds = offset_str[decimal_index + 1:]
        if len(milliseconds) < 3:
            milliseconds += '0' * (3 - len(milliseconds))
    else:
        # If no '.', fill 000
        milliseconds = '000'
    
    return milliseconds

def find_the_4th_columns_name(csv_filename):
    with open(csv_filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Read header line only

        # Find the index of "Offset"
        offset_index = header.index("Offset")

        # Find the next one
        next_column_name = header[offset_index + 1]

        return next_column_name

def naming_normalization(input_string):
    # Define the special characters to be replaced
    special_characters = r'[|*/\\^!%@&^#~:;?"]'

    # Use regular expressions to replace special characters with underscores
    result = re.sub(special_characters, '_', input_string)

    return result

def load_map_skip_step(map_skip_step):
    tool_id = "Tool_ID"
    step_name = "STEP_NAME"
    # Load the file first
    with open('source/SOCAL_OxfordICPPlasmaPro100/stepname_filter.cfg', newline='') as csvfile:
        rows = csv.DictReader(csvfile)
        for row in rows:
            key = str(row[tool_id]).lower()
            value = str(row[step_name]).lower()
            if key not in map_skip_step:
                map_skip_step[key] = [value]
            else:
                map_skip_step[key].append(value)
        
    print(map_skip_step)
    
    return
            


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
    parser.add_argument("pos3", help="positional argument 3")
    parser.add_argument("-outdir",help="output folder",dest="outdir",default="outdir/")
    parser.add_argument("-logdir",help="log folder",dest="logdir",default="logdir/")
    parser.add_argument("-refdir",help="reference folder",dest="refdir")
    parser.add_argument("-lockdir",help="lock folder",dest="lockdir")
    parser.add_argument("-ext","--extension",help="file extension",dest="fileext",default="csv")
    args = parser.parse_args()
    print("Executing FDC Script SOCAL Oxford ICP Plasma Pro 100 ... •ᴗ• ")
    print(args)
    input_filepath = args.pos1
    tool_id = args.pos2
    chamber_id = args.pos3
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
    
    # Load map_skip_step
    map_skip_step = {}
    load_map_skip_step(map_skip_step)


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
                
                # Data Structure for different Data Type
                arr_step_name = []
                df_sensor = []
                step_id = 0
                step_name = 'NA'
                # Initialize
                arr_step_name.append(step_name)

                # Find the 4th column name. The "Offset" is the 3rd column
                next_column_name = find_the_4th_columns_name(input_filepath + Cache_Filename)
                # Parse CSV file
                csv_contents = pd.read_csv(input_filepath + Cache_Filename, dtype={'Offset': str, next_column_name: str})

                # Find the sensor columns in the list
                df_sensor_column = ['New_Timestamp', 'StepID', "StepName"] + csv_contents.columns.tolist()
                # Acquire the column next to "Offset"
                index_offset = df_sensor_column.index('Offset')
                step_name_columns_name = df_sensor_column[(index_offset + 1) % len(df_sensor_column)]

                # Acquire basic information
                str_time_created = str(csv_contents.iloc[1]['Timestamp']).strip()+"."+str(extract_milliseconds(csv_contents.iloc[1]['Offset'])).strip()
                str_job_id = str(csv_contents.iloc[1]['jobID']).strip().replace(' ', '_')
                str_recipe_name = str(csv_contents.iloc[1]['recipe']).strip().replace(' ', '_')
                str_current_user = str(csv_contents.iloc[1]['user']).strip().replace(' ', '_')
                str_batch_id = str(csv_contents.iloc[1]['batchID']).strip().replace(' ', '_')
                # Workaround if lotID is empty
                if pd.isnull(csv_contents.iloc[1]['lotID']):
                    str_lot_id = str_batch_id
                else:
                    str_lot_id = str(csv_contents.iloc[1]['lotID']).strip().replace(' ', '_')


                # Start to Process
                continuous_event = -1 # For skipping continuous Event Data
                for index, row in csv_contents.iterrows():
                    # Event parts
                    if row['Type'] == 'Event':
                        if row['Offset'] == 'RecipeMarker':
                            # Do thing
                            pass
                        else:
                            # Find the Step Name value in the column next to "Offset"
                            step_name = str(row[step_name_columns_name]).strip()
                            # Whether need to skip
                            if tool_id.lower() in map_skip_step and step_name.lower() in map_skip_step[tool_id.lower()]:
                                    step_id = 0
                                    step_name = "NA"
                            else:
                                if continuous_event >= 0:
                                    # If happen continuous Events, remove the previous one, and insert the following one instead.
                                    del arr_step_name[continuous_event]
                                    
                                # Find Step Id or Create one if not exists.
                                try:
                                    step_id = arr_step_name.index(step_name)
                                except ValueError:
                                    arr_step_name.append(step_name)
                                    step_id = arr_step_name.index(step_name)
                                    # Keep the step id to mark continuous part
                                    continuous_event = step_id
                    # Data parts
                    elif row['Type'] == 'Data':
                        # Calculated Sensor Values
                        row_timestamp = str(row['Timestamp']) + "." + str(extract_milliseconds(row['Offset']))
                        df_sensor_row = [datetime_conversion(row_timestamp,2), step_id, step_name]
                        # Add it to the rows
                        df_sensor_row.extend(row)
                        df_sensor.append(df_sensor_row)
                        # Confirm it is not continuous events
                        continuous_event = -1

                # Add df sensor columns to the list
                df_sensor = pd.DataFrame(df_sensor, columns=df_sensor_column)
                # Drop the columns after column "id"
                df_sensor=df_sensor.loc[:, :'id']
                # Drop the columns named "Type" & "Timestamp"
                df_sensor.drop(columns=['Type', 'Timestamp'], inplace=True)
                # Rename the New Timestamp to Timestamp
                df_sensor.rename(columns={"New_Timestamp": "Timestamp"}, inplace=True)
                
                

                #########################
                #    New Output XML     #
                #########################
                Output_FileName = datetime_conversion(str_time_created,3).replace(' ', '_') + "_" + tool_id.replace('/', '_') + "_" + chamber_id.replace('/', '_') + "_" + str_batch_id.replace('/', '_') + ".exntrace"
                Output_FileName = naming_normalization(Output_FileName)

                env = Environment(loader=FileSystemLoader("source/SOCAL_OxfordICPPlasmaPro100/templates/"))
                template = env.get_template('process_context_oxfordicpplasmapro100.xml')
                content = template.render(
                    tool_id=tool_id,
                    module=chamber_id,
                    recipe_name=str_recipe_name,
                    material_id=str_lot_id,
                    lot_id=str_lot_id,
                    current_user=str_current_user,
                    wafer_id=str_lot_id+"_"+datetime_conversion(str_time_created,1)
                )
                with open(outdir + Output_FileName, mode="w", encoding="utf-8") as message:
                    message.write(content)
                    message.write("\n\n")

                print(f"... wrote template for {Output_FileName}")
                with open(outdir + Output_FileName, mode="a") as f:
                    f.write(df_sensor.to_csv(index=False, sep='\t'))

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
            # sys.exit()
        
            

    

main()
