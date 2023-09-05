import os
import requests
import json
from typing import List, Optional, Dict


labelstudio_key = os.environ.get('LABELSTUDIO_KEY')
if labelstudio_key is None:
    raise ValueError("Please specify a valid Label Studio API Key.")

header =  {'Content-Type': 'application/json', 'Authorization': f'Token {labelstudio_key}'} 
url = 'https://label.aixplain.com'

def get_task_data(task_id: int):
    """
    Retrieves data for a specific task from Label Studio.

    Args:
        task_id (int): The ID of the task for which data is to be retrieved.

    Returns:
        bytes: The raw response content containing the task data.
    """
    full_url = url +'/api/tasks/' + str(task_id)
    response = requests.get(full_url, headers=header)
    output = response.content
    return output

def get_all_tasks_per_project(project_id: int):
    """
    Retrieves a list of task IDs for all tasks associated with a specific project within Label Studio.

    Args:
        project_id (int): The ID of the project for which tasks are to be retrieved.

    Returns:
        list: A list containing task IDs of all tasks in the specified project.
    """
    output = []
    response = '[200]'
    i = 1
    while '[200]' in response:
        full_url = url +'/api/projects/' + str(project_id) + '/tasks/?page=' + str(i)
        response = requests.get(full_url, headers=header)
        if response.status_code == 200:
            for taskInfo in json.loads(response.content):
                output.append(taskInfo['id'])
    return output

def extract_data(dict: Dict):
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
    
def extract_project_data(project_id: int):
    """
    Retrieves and extracts data for all tasks associated with a specific project in a Label Studio instance.

    Args:
        project_id (int): The ID of the project for which tasks' data are to be retrieved.

    Returns:
        tuple: A tuple containing two dictionaries. The first dictionary contains extracted data and annotations,
            while the second dictionary maps annotation names to their corresponding data types.
    """
    output = []
    tasks = get_all_tasks_per_project(project_id)
    dtypes = extract_data(json.loads(get_task_data(tasks[0])))[1]
    for task in tasks:
        output.append(extract_data(json.loads(get_task_data(task)))[0])
    return output, dtypes