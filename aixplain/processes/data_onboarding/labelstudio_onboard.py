import json
import requests
import pandas as pd
import os
from typing import List, Optional, Dict
from aixplain.enums import DataType, Language, License, StorageType
from aixplain.factories import CorpusFactory
from aixplain.modules import MetaData

def getTaskData(url, header, task_id):
    """
    Retrieves data for a specific task from Label Studio.

    Args:
        url (str): The base URL of Label Studio.
        header (dict): The request headers containing authentication details.
        task_id (int): The ID of the task for which data is to be retrieved.

    Returns:
        bytes: The raw response content containing the task data.
    """
    fullUrl = url +'/api/tasks/' + str(task_id)
    response = requests.get(fullUrl, headers=header)
    output = response.content
    return output

def getAllTasksPerProject(url, header, project_id):
    """
    Retrieves a list of task IDs for all tasks associated with a specific project within Label Studio.

    Args:
        url (str): The base URL of Label Studio.
        header (dict): The request headers containing authentication details.
        project_id (int): The ID of the project for which tasks are to be retrieved.

    Returns:
        list: A list containing task IDs of all tasks in the specified project.
    """
    output = list()
    response = '[200]'
    i = 1
    while '[200]' in response:
        fullUrl = url +'/api/projects/' + str(project_id) + '/tasks/?page=' + str(i)
        response = requests.get(fullUrl, headers=header)
        if response.status_code == 200:
            for taskInfo in json.loads(response.content):
                output.append(taskInfo['id'])
    return output

def extractData(dict):
    """
    Extracts and transforms data and annotations from a dictionary representing a task in Label Studio.

    Args:
        data_dict (dict): A dictionary representing a task data in Label Studio.
    Returns:
        tuple: A tuple containing two dictionaries. The first dictionary contains extracted data and annotations,
               while the second dictionary maps annotation names to their corresponding data types.
    """
    output = {}
    if 'data' in dict:
        if 'text' in dict['data']:
            output['data'] = dict['data']['text']
            output['id'] = dict['id']
            dtypes = {}
            if 'annotations' in dict and 'result' in dict['annotations'][0]:
                for annotation in dict['annotations'][0]['result']:
                    name = annotation['from_name']
                    annotation_type = annotation['type']
                    if annotation['type'] == 'textarea':
                        annotation_type = 'text'
                    dtypes[name] = annotation['type']
                    tags = annotation['value'][annotation_type][0]
                    output[name] = tags    
                return output, dtypes
            else:
                return {'Error': 'No annotations'}
        elif 'url' in dict['data']:
            output['data'] = dict['data']['url']
            output['id'] = dict['id']
            output['annotation'] = []
            prev_start = -1
            prev_end = -1
            dtypes = {}
            try:
                if 'annotations' in dict and 'result' in dict['annotations'][0]:
                    item = {}
                    for annotation in dict['annotations'][0]['result']:
                        name = annotation['from_name']
                        annotation_type = annotation['type']
                        if annotation['type'] == 'textarea':
                            annotation_type = 'text'
                        tags = annotation['value'][annotation_type][0]
                        dtypes[name] = annotation['type']
                        if 'start' in annotation['value']:
                            start = annotation['value']['start']
                        if 'end' in annotation['value']:
                            end = annotation['value']['end']
                        if prev_start != start and len(item) > 0:
                            item['start'] = prev_start
                            item['end'] = prev_end
                            output['annotation'].append(item)
                            item = {}
                        if 'start' in annotation['value']:
                            item[name] = tags
                            prev_start = start
                            prev_end = end
                    if len(item) > 0:
                        item['start'] = prev_start
                        item['end'] = prev_end
                        output['annotation'].append(item)
            except:
                print('Error: No annotations found!')
            return output, dtypes
    else:
        return {'Error': 'No data'}

def getAllDataForAProject(url, header, project_id):
    """
    Retrieves and extracts data for all tasks associated with a specific project in a Label Studio instance.

    Args:
        url (str): The base URL of Label Studio.
        header (dict): The request headers containing authentication details.
        project_id (int): The ID of the project for which tasks' data are to be retrieved.

    Returns:
        tuple: A tuple containing two dictionaries. The first dictionary contains extracted data and annotations,
               while the second dictionary maps annotation names to their corresponding data types.
    """
    output = []
    tasks = getAllTasksPerProject(url, header, project_id)
    dtypes = extractData(json.loads(getTaskData(url, header, tasks[0])))[1]
    for task in tasks:
        output.append(extractData(json.loads(getTaskData(url, header, task)))[0])
    return output, dtypes

def auto_onboard(
    labelstudio_key: str,
    data_name: str,
    task_id: Optional[int] = None,
    project_id: Optional[int] = None,
    columns_to_drop: Optional[List[str]] = None,
    onboard: Optional[bool] = False,
    data_description: Optional[str] = None
) -> Dict:
    """
    Automatically onboard a corpus onto the aiXplain platform using LabelStudio and aiXplain APIs.

    Args:
        labelstudio_key (str): The authentication API key from LabelStudio.
        data_name (str): The data name of the corpus to be onboarded on the platform.
        task_id (Optional[int]): LabelStudio task ID to be retrieved. Default is None.
        project_id (Optional[int]): LabelStudio project ID to be retrieved. User must specify
                                  either task_id or project_id, not both, nor None. Default is None.
        columns_to_drop (Optional[List[str]]): List of column names to drop from the dataset
                                               before onboarding. Default is None.
        onboard (Optional[bool]): Whether user wants to perform the onboarding process.
                                  Default is False.
        data_description (Optional[str]): Data description of the corpus to be onboarded.
                                         Default is None.

    Returns:
        None

    Note:
        This function automates the process of onboarding a corpus onto aiXplain platform.
        It requires authentication keys for both LabelStudio and aiXplain, as well as information
        about the dataset and the desired onboarding process. The function should handle all text and audio datasets.

    Example:
        auto_onboard(labelstudio_key="labelstudio-api-key",
                     aixplain_key="aixplain-team-api-key",
                     data_name="sample_corpus",
                     task_id=12345,
                     columns_to_drop=["unwanted_col1", "unwanted_col2"],
                     onboard=True,
                     data_description="This is a sample dataset for testing.")
    """

    header =  {'Content-Type': 'application/json', 'Authorization': f'Token {labelstudio_key}'} 
    url = 'https://label.aixplain.com'
    
    task_filename1 = 'task_audio_{}.csv'.format(task_id)
    task_filename2 = 'task_text_{}.csv'.format(task_id)

    project_filename1 = 'project_audio_{}.csv'.format(project_id)
    project_filename2 = 'project_text_{}.csv'.format(project_id)
    
    
    # Code to handle task_id or project_id accordingly

    if (project_id is None and task_id is None) or (project_id is not None and task_id is not None):
        raise ValueError("One and only one of project_id or task_id must be specified.")
    elif task_id:
        print('Extracting data...')
        # Extracting data using Task ID
        data, dtypes = extractData(json.loads(getTaskData(url, header, task_id)))
        # Processing audio data into a pandas dataframe
        if data['data'][:5] == 'https':
            df = pd.DataFrame(data['annotation'])
            df['audio'] = [data['data']] * len(data['annotation'])
            filename = task_filename1
        else: # Processing text data into a pandas dataframe
            df = pd.DataFrame([d])
            filename = task_filename2
    elif project_id:
        print('Extracting data...')
        # Extracting data using Project ID
        data, dtypes = getAllDataForAProject(url, header, project_id)
        # Processing audio data into a pandas dataframe
        if data[0]['data'][:5] == 'https':
            df = pd.DataFrame()
            for item in data:
                temp = pd.DataFrame(item['annotation'])
                temp['audio'] = [item['data']] * len(item['annotation'])
                df = pd.concat([df, temp], ignore_index=True, sort=False)
            filename = project_filename1
        else: # Processing text data into a pandas dataframe
            df = pd.DataFrame(data)
            filename = project_filename2

    for col in df.columns:
        if (col not in dtypes.keys()) and (col not in ['start', 'end']) and (df[col].dtype != object):
            df.drop(columns = [col], inplace = True)


    # Use `columns_to_drop` to process the columns as needed.
    if columns_to_drop is None:
        print("Continuing without dropping any columns.")
    else:
        try:
            print(f"Dropping columns: {', '.join(columns_to_drop)}")
            df.drop(columns = columns_to_drop, inplace = True)
        except:
            print("No columns found that match the given names. Continuing without dropping any columns.")


    df.to_csv(filename, index = False)
    print('Data extracted successfully, and saved to a CSV file with the name: {}.'.format(filename))

    # Use onboard to determine the user's choice.
    if onboard is False:
        print('Terminating the operation.')
        return None
    else:
        print("Proceeding to onboard the corpus to aiXplain platform...")
        schema = []
        if 'text' in filename:
            for col in df.columns:
                print('Creating MetaData for column: {}.'.format(col))
                if col not in dtypes.keys():
                    schema.append(MetaData(
                        name = col, 
                        dtype = DataType.TEXT, 
                        data_column = col,
                        storage_type = StorageType.TEXT
                    ))
                elif dtypes[col].lower() in ['choices', 'labels']:
                    schema.append(MetaData(
                        name = col,
                        dtype = DataType.LABEL, 
                        data_column = col,
                        storage_type = StorageType.TEXT, 
                    ))
                elif dtypes[col].lower() in ['text', 'textarea']:
                    print('Creating MetaData for column: {}.'.format(col))
                    schema.append(MetaData(
                        name=col, 
                        dtype=DataType.TEXT, 
                        data_column=col,
                        storage_type=StorageType.TEXT
                    ))
        else:
            for col in df.columns:
                if col in ['start', 'end']:
                    continue
                elif col == 'audio':
                    print('Creating MetaData for column: {}.'.format(col))
                    if ('start' in df.columns) and ('end' in df.columns):
                        schema.append(MetaData(
                            name=col, 
                            dtype=DataType.AUDIO,
                            start_column='start',
                            end_column='end',
                            data_column=col,
                            storage_type=StorageType.URL
                        ))
                    else:
                        schema.append(MetaData(
                            name=col, 
                            dtype=DataType.AUDIO,
                            data_column=col,
                            storage_type=StorageType.URL
                        ))

                elif dtypes[col].lower() in ['choices', 'labels']:
                    print('Creating MetaData for column: {}.'.format(col))
                    schema.append(MetaData(
                        name=col, 
                        dtype=DataType.LABEL, 
                        data_column=col,
                        storage_type=StorageType.TEXT, 
                    ))

                elif dtypes[col].lower() in ['text', 'textarea']:
                    print('Creating MetaData for column: {}.'.format(col))
                    schema.append(MetaData(
                        name=col, 
                        dtype=DataType.TEXT, 
                        data_column=col,
                        storage_type=StorageType.TEXT
                    ))
                        
        if data_description:
            payload = CorpusFactory.create(
                name=data_name,
                description=data_description,
                license=License.MIT,
                content_path=filename,
                schema=schema
            )
        else:
            payload = CorpusFactory.create(
                name=data_name,
                license=License.MIT,
                content_path=filename,
                schema=schema
            )
            
        return payload