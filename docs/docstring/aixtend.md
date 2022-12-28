# aixtend package

## Subpackages


* [aixtend.factories package](aixtend.factories.md)


    * [Submodules](aixtend.factories.md#submodules)


    * [aixtend.factories.asset_factory module](aixtend.factories.md#module-aixtend.factories.asset_factory)


        * [`AssetFactory`](aixtend.factories.md#aixtend.factories.asset_factory.AssetFactory)


            * [`AssetFactory.api_key`](aixtend.factories.md#aixtend.factories.asset_factory.AssetFactory.api_key)


            * [`AssetFactory.backend_url`](aixtend.factories.md#aixtend.factories.asset_factory.AssetFactory.backend_url)


            * [`AssetFactory.get()`](aixtend.factories.md#aixtend.factories.asset_factory.AssetFactory.get)


    * [aixtend.factories.benchmark_factory module](aixtend.factories.md#module-aixtend.factories.benchmark_factory)


        * [`BenchmarkFactory`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory)


            * [`BenchmarkFactory.api_key`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.api_key)


            * [`BenchmarkFactory.backend_url`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.backend_url)


            * [`BenchmarkFactory.create_benchmark()`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.create_benchmark)


            * [`BenchmarkFactory.create_benchmark_from_id()`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.create_benchmark_from_id)


            * [`BenchmarkFactory.create_benchmark_job_from_id()`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.create_benchmark_job_from_id)


            * [`BenchmarkFactory.download_results_as_csv()`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.download_results_as_csv)


            * [`BenchmarkFactory.start_benchmark_job()`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.start_benchmark_job)


            * [`BenchmarkFactory.update_benchmark_info()`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.update_benchmark_info)


            * [`BenchmarkFactory.update_benchmark_job_info()`](aixtend.factories.md#aixtend.factories.benchmark_factory.BenchmarkFactory.update_benchmark_job_info)


    * [aixtend.factories.dataset_factory module](aixtend.factories.md#module-aixtend.factories.dataset_factory)


        * [`DatasetFactory`](aixtend.factories.md#aixtend.factories.dataset_factory.DatasetFactory)


            * [`DatasetFactory.api_key`](aixtend.factories.md#aixtend.factories.dataset_factory.DatasetFactory.api_key)


            * [`DatasetFactory.backend_url`](aixtend.factories.md#aixtend.factories.dataset_factory.DatasetFactory.backend_url)


            * [`DatasetFactory.create()`](aixtend.factories.md#aixtend.factories.dataset_factory.DatasetFactory.create)


            * [`DatasetFactory.get()`](aixtend.factories.md#aixtend.factories.dataset_factory.DatasetFactory.get)


            * [`DatasetFactory.get_assets_from_page()`](aixtend.factories.md#aixtend.factories.dataset_factory.DatasetFactory.get_assets_from_page)


            * [`DatasetFactory.get_first_k_assets()`](aixtend.factories.md#aixtend.factories.dataset_factory.DatasetFactory.get_first_k_assets)


    * [aixtend.factories.metric_factory module](aixtend.factories.md#module-aixtend.factories.metric_factory)


        * [`MetricFactory`](aixtend.factories.md#aixtend.factories.metric_factory.MetricFactory)


            * [`MetricFactory.api_key`](aixtend.factories.md#aixtend.factories.metric_factory.MetricFactory.api_key)


            * [`MetricFactory.backend_url`](aixtend.factories.md#aixtend.factories.metric_factory.MetricFactory.backend_url)


            * [`MetricFactory.create_asset_from_id()`](aixtend.factories.md#aixtend.factories.metric_factory.MetricFactory.create_asset_from_id)


            * [`MetricFactory.list_assets()`](aixtend.factories.md#aixtend.factories.metric_factory.MetricFactory.list_assets)


    * [aixtend.factories.model_factory module](aixtend.factories.md#module-aixtend.factories.model_factory)


        * [`ModelFactory`](aixtend.factories.md#aixtend.factories.model_factory.ModelFactory)


            * [`ModelFactory.api_key`](aixtend.factories.md#aixtend.factories.model_factory.ModelFactory.api_key)


            * [`ModelFactory.backend_url`](aixtend.factories.md#aixtend.factories.model_factory.ModelFactory.backend_url)


            * [`ModelFactory.create_asset_from_id()`](aixtend.factories.md#aixtend.factories.model_factory.ModelFactory.create_asset_from_id)


            * [`ModelFactory.get_assets_from_page()`](aixtend.factories.md#aixtend.factories.model_factory.ModelFactory.get_assets_from_page)


            * [`ModelFactory.get_first_k_assets()`](aixtend.factories.md#aixtend.factories.model_factory.ModelFactory.get_first_k_assets)


            * [`ModelFactory.subscribe_to_asset()`](aixtend.factories.md#aixtend.factories.model_factory.ModelFactory.subscribe_to_asset)


            * [`ModelFactory.unsubscribe_to_asset()`](aixtend.factories.md#aixtend.factories.model_factory.ModelFactory.unsubscribe_to_asset)


    * [aixtend.factories.pipeline_factory module](aixtend.factories.md#module-aixtend.factories.pipeline_factory)


        * [`PipelineFactory`](aixtend.factories.md#aixtend.factories.pipeline_factory.PipelineFactory)


            * [`PipelineFactory.create_from_api_key()`](aixtend.factories.md#aixtend.factories.pipeline_factory.PipelineFactory.create_from_api_key)


    * [Module contents](aixtend.factories.md#module-aixtend.factories)


* [aixtend.modules package](aixtend.modules.md)


    * [Submodules](aixtend.modules.md#submodules)


    * [aixtend.modules.asset module](aixtend.modules.md#module-aixtend.modules.asset)


        * [`Asset`](aixtend.modules.md#aixtend.modules.asset.Asset)


            * [`Asset.to_dict()`](aixtend.modules.md#aixtend.modules.asset.Asset.to_dict)


    * [aixtend.modules.benchmark module](aixtend.modules.md#module-aixtend.modules.benchmark)


        * [`Benchmark`](aixtend.modules.md#aixtend.modules.benchmark.Benchmark)


    * [aixtend.modules.benchmark_job module](aixtend.modules.md#module-aixtend.modules.benchmark_job)


        * [`BenchmarkJob`](aixtend.modules.md#aixtend.modules.benchmark_job.BenchmarkJob)


            * [`BenchmarkJob.get_asset_info()`](aixtend.modules.md#aixtend.modules.benchmark_job.BenchmarkJob.get_asset_info)


    * [aixtend.modules.dataset module](aixtend.modules.md#module-aixtend.modules.dataset)


        * [`DataFormat`](aixtend.modules.md#aixtend.modules.dataset.DataFormat)


            * [`DataFormat.DICT`](aixtend.modules.md#aixtend.modules.dataset.DataFormat.DICT)


            * [`DataFormat.HUGGINGFACE_DATASETS`](aixtend.modules.md#aixtend.modules.dataset.DataFormat.HUGGINGFACE_DATASETS)


            * [`DataFormat.PANDAS`](aixtend.modules.md#aixtend.modules.dataset.DataFormat.PANDAS)


        * [`Dataset`](aixtend.modules.md#aixtend.modules.dataset.Dataset)


            * [`Dataset.get_data()`](aixtend.modules.md#aixtend.modules.dataset.Dataset.get_data)


        * [`FieldType`](aixtend.modules.md#aixtend.modules.dataset.FieldType)


            * [`FieldType.AUDIO`](aixtend.modules.md#aixtend.modules.dataset.FieldType.AUDIO)


            * [`FieldType.IMAGE`](aixtend.modules.md#aixtend.modules.dataset.FieldType.IMAGE)


            * [`FieldType.LABEL`](aixtend.modules.md#aixtend.modules.dataset.FieldType.LABEL)


            * [`FieldType.TEXT`](aixtend.modules.md#aixtend.modules.dataset.FieldType.TEXT)


            * [`FieldType.VIDEO`](aixtend.modules.md#aixtend.modules.dataset.FieldType.VIDEO)


        * [`FileFormat`](aixtend.modules.md#aixtend.modules.dataset.FileFormat)


            * [`FileFormat.CSV`](aixtend.modules.md#aixtend.modules.dataset.FileFormat.CSV)


            * [`FileFormat.JSON`](aixtend.modules.md#aixtend.modules.dataset.FileFormat.JSON)


            * [`FileFormat.PARQUET`](aixtend.modules.md#aixtend.modules.dataset.FileFormat.PARQUET)


            * [`FileFormat.XML`](aixtend.modules.md#aixtend.modules.dataset.FileFormat.XML)


    * [aixtend.modules.metric module](aixtend.modules.md#module-aixtend.modules.metric)


        * [`Metric`](aixtend.modules.md#aixtend.modules.metric.Metric)


    * [aixtend.modules.model module](aixtend.modules.md#module-aixtend.modules.model)


        * [`Model`](aixtend.modules.md#aixtend.modules.model.Model)


            * [`Model.poll()`](aixtend.modules.md#aixtend.modules.model.Model.poll)


            * [`Model.run()`](aixtend.modules.md#aixtend.modules.model.Model.run)


            * [`Model.run_async()`](aixtend.modules.md#aixtend.modules.model.Model.run_async)


            * [`Model.to_dict()`](aixtend.modules.md#aixtend.modules.model.Model.to_dict)


    * [aixtend.modules.pipeline module](aixtend.modules.md#module-aixtend.modules.pipeline)


        * [`Pipeline`](aixtend.modules.md#aixtend.modules.pipeline.Pipeline)


            * [`Pipeline.poll()`](aixtend.modules.md#aixtend.modules.pipeline.Pipeline.poll)


            * [`Pipeline.run()`](aixtend.modules.md#aixtend.modules.pipeline.Pipeline.run)


            * [`Pipeline.run_async()`](aixtend.modules.md#aixtend.modules.pipeline.Pipeline.run_async)


    * [Module contents](aixtend.modules.md#module-aixtend.modules)


* [aixtend.utils package](aixtend.utils.md)


    * [Submodules](aixtend.utils.md#submodules)


    * [aixtend.utils.config module](aixtend.utils.md#module-aixtend.utils.config)


    * [aixtend.utils.file_utils module](aixtend.utils.md#module-aixtend.utils.file_utils)


        * [`save_file()`](aixtend.utils.md#aixtend.utils.file_utils.save_file)


    * [Module contents](aixtend.utils.md#module-aixtend.utils)


## Module contents

aiXplain SDK Library.
—

aiXplain SDK enables python programmers to add AI functions
to their software.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the “License”);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

> [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an “AS IS” BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
