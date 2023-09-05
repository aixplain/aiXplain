import json
import pandas as pd
from typing import List, Optional
from aixplain.factories.asset_factory import AssetFactory
import aixplain.processes.labelstudio_data.labelstudio_functions as labelstudio_functions
from aixplain.modules.labelstudio_data import LabelStudioData

class LabelStudioFactory(AssetFactory):
    @classmethod
    def create(
        cls,
        task_id: Optional[int] = None,
        project_id: Optional[int] = None,
        columns_to_drop: Optional[List[str]] = None
    ) -> LabelStudioData:
        """
        Extracts data for audio and text dtpyes of either a project or a task in Label Studio, stores the data in a pandas.DataFrame and saves it to a CSV file.

        Args:
            task_id (Optional[int]): LabelStudio task ID to be retrieved. Default is None.
            project_id (Optional[int]): LabelStudio project ID to be retrieved. Default is None.
            columns_to_drop (Optional[List[str]]): List of column names to drop from the dataset. Default is None.
        Returns:
            tuple: A tuple containing the CSV file name, columns data types, and the processed dataframe.
        """
        task_filename1 = 'task_{}_audio.csv'.format(task_id)
        task_filename2 = 'task_{}_text.csv'.format(task_id)

        project_filename1 = 'project_{}_audio.csv'.format(project_id)
        project_filename2 = 'project_{}_text.csv'.format(project_id)
        
        
        # Code to handle task_id or project_id accordingly
        if (project_id is None and task_id is None) or (project_id is not None and task_id is not None):
            raise ValueError("One and only one of project_id or task_id must be specified.")
        elif task_id:
            print('Extracting data...')
            # Extracting data using Task ID
            data, dtypes = labelstudio_functions.extract_data(json.loads(labelstudio_functions.get_task_data(task_id)))
            # Processing audio data into a pandas dataframe
            if data['data'][:5] == 'https':
                df = pd.DataFrame(data['annotation'])
                df['audio'] = [data['data']] * len(data['annotation'])
                filename = task_filename1
            else: # Processing text data into a pandas dataframe
                df = pd.DataFrame([data])
                filename = task_filename2
            id = task_id
            labelstudio_tasks = None
        elif project_id:
            print('Extracting data...')
            # Extracting data using Project ID
            data, dtypes = labelstudio_functions.extract_project_data(project_id)
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
            id = project_id
            labelstudio_tasks = labelstudio_functions.get_all_tasks_per_project(project_id)

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


        # Save the dataframe to a CSV file
        df.to_csv(filename, index = False)
        print('Data extracted successfully, and saved to a CSV file with the name: {}.'.format(filename))
        
        description = 'This is {} data retrieved from LabelStudio.'.format(filename.replace('_', ' '))

        labelstudio_data = LabelStudioData(
            id = str(id),
            name = filename,
            description = description,
            dtypes = dtypes,
            labelstudio_tasks = labelstudio_tasks
        )
        return labelstudio_data