from aixplain.enums.license import License
from aixplain.enums.privacy import Privacy
from aixplain.modules.asset import Asset
from aixplain.enums import DataType, Language, License, StorageType
from aixplain.factories import CorpusFactory
from aixplain.modules import MetaData
import pandas as pd
import warnings
from typing import List, Optional, Text, Dict


class LabelStudioData(Asset):
    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        dtypes: Dict,
        labelstudio_tasks: Optional[List[Text]] = None,
        license: Optional[License] = None,
        privacy: Privacy = Privacy.PRIVATE,
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        **kwargs,
    ) -> None:
        """Label Studio Class.

        Description:
            Label Studio is an annotation service that includes data of various types, i.e., audio and text.

        Args:
            id (Text): Label Studio task/project ID.
            name (Text): CSV file name.
            description (Text): Description of the Label Studio object.
            dtypes (Dict): List of data types of each field in the Label Studio object.
            labelstudio_tasks (Optional[List[Text]]): List of task IDs if the object is a project. Default is None.
            license (Optional[License], optional): Object license. Defaults to None.
            privacy (Privacy, optional): Object privacy info. Defaults to Privacy.PRIVATE.
            supplier (Text, optional): Object supplier. Defaults to "aiXplain".
            version (Text, optional): Object version. Defaults to "1.0".
        """
        super().__init__(
            id=id, name=name, description=description, supplier=supplier, version=version, license=license, privacy=privacy
        )
        self.labelstudio_tasks = labelstudio_tasks
        self.dtypes = dtypes
        self.kwargs = kwargs

    def onboard_as_corpus(
        self,
        corpus_name: str,
        language: Optional[List[str]] = None,
        corpus_description: Optional[str] = None
    ) -> Dict:
        """
        Automatically onboard a Label Studio object onto aiXplain platform as a corpus.

        Args:
            corpus_name (str): The data name of the corpus to be onboarded on the platform.
            task_id (Optional[int]): LabelStudio task ID to be retrieved. Default is None.
            project_id (Optional[int]): LabelStudio project ID to be retrieved. User must specify
                                    either task_id or project_id, not both, nor None. Default is None.
            columns_to_drop (Optional[List[str]]): List of column names to drop from the dataset
                                                before onboarding. Default is None.
            language Optional[List[str]]: List of languages codes to add to metadata. Default is None.
            corpus_description (Optional[str]): Data description of the corpus to be onboarded.
                                            Default is None.

        Returns:
            None
        """

        filename = self.name
        dtypes = self.dtypes
        df = pd.read_csv(filename)
        
        langs = None
        if language is not None:
            langs = []
            for k in range(len(language)):
                for lang in list(Language):
                    if lang.value['language'] == language[k] and lang.value['dialect'] == '':
                        langs.append(lang)
            if len(langs) == 0:
                langs = None
                warnings.warn("Languages given are not supported. Proceeding without adding language to the metadata.", UserWarning)
            elif len(langs) < len(language):
                warnings.warn("One or more languages are not supported. Proceeding without adding them to the metadata.", UserWarning)

        print("Proceeding to onboard the corpus to aiXplain platform...")
        schema = []
        if 'text' in filename:
            for col in df.columns:
                print('Creating MetaData for column: {}.'.format(col))
                if col not in dtypes.keys():
                    if langs is None:
                        schema.append(MetaData(
                            name = col, 
                            dtype = DataType.TEXT, 
                            data_column = col,
                            storage_type = StorageType.TEXT
                        ))
                    else:
                        schema.append(MetaData(
                            name = col, 
                            dtype = DataType.TEXT, 
                            data_column = col,
                            languages = langs,
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
                    if langs is None:
                        schema.append(MetaData(
                            name=col, 
                            dtype=DataType.TEXT, 
                            data_column=col,
                            storage_type=StorageType.TEXT
                        ))
                    else:
                        schema.append(MetaData(
                            name=col, 
                            dtype=DataType.TEXT, 
                            data_column=col,
                            languages = langs,
                            storage_type=StorageType.TEXT
                        ))
        else:
            for col in df.columns:
                if col in ['start', 'end']:
                    continue
                elif col == 'audio':
                    print('Creating MetaData for column: {}.'.format(col))
                    if ('start' in df.columns) and ('end' in df.columns):
                        if langs is None:
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
                                start_column='start',
                                end_column='end',
                                data_column=col,
                                languages = langs,
                                storage_type=StorageType.URL
                            ))
                    else:
                        if langs is None:
                            schema.append(MetaData(
                                name=col, 
                                dtype=DataType.AUDIO,
                                data_column=col,
                                storage_type=StorageType.URL
                            ))
                        else:
                            schema.append(MetaData(
                                name=col, 
                                dtype=DataType.AUDIO,
                                data_column=col,
                                languages = langs,
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
                    if langs is None:
                        schema.append(MetaData(
                            name=col, 
                            dtype=DataType.TEXT, 
                            data_column=col,
                            storage_type=StorageType.TEXT
                        ))
                    else:
                        schema.append(MetaData(
                            name=col, 
                            dtype=DataType.TEXT, 
                            data_column=col,
                            languages = langs,
                            storage_type=StorageType.TEXT
                        ))
                        
        if corpus_description:
            payload = CorpusFactory.create(
                name=corpus_name,
                description=corpus_description,
                license=License.MIT,
                content_path=filename,
                schema=schema
            )
        else:
            payload = CorpusFactory.create(
                name=corpus_name,
                license=License.MIT,
                content_path=filename,
                schema=schema
            )
            
        return payload