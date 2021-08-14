import json 
import os
from airflow import DAG
from datetime import datetime, timedelta
import pandas as pd
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.hooks.base_hook import BaseHook
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.email_operator import EmailOperator
from airflow.providers.http.operators.http import SimpleHttpOperator

default_args = {
    "owner": "amey",
    "start_date": datetime(2021, 8, 8),
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "ameysonje242000@gmail.com",
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

csv_data_path = f'{json.loads(BaseHook.get_connection("csv_data").get_extra()).get("path")}/csv_data.csv'

transformed_csv_path = f'{os.path.splitext(csv_data_path)[0]}_transformed.csv'

def transform_data(*args, **kwargs):
    print(csv_data_path)
    print(transformed_csv_path)
    csv_data = pd.read_csv(filepath_or_buffer=csv_data_path,
                            sep=',',
                            header=0,
                            usecols=['Year','Industry_name_NZSIOC','Variable_code','Value']
                            )
    csv_data.dropna(axis=0, how='any', inplace=True)
    csv_data.to_csv(path_or_buf=transformed_csv_path)

def is_today(*args, **context):
    exec_date=context['execution_date']
    today=exec_date.in_timezone("Europe/London").weekday()
    print('today is ' + str(today))
    return 'friday_Task' if today==4 else 'none'

def friday_Task():
    print('From friday_Task, so its Friday today')
    

with DAG(dag_id="pipeline_try",
         schedule_interval="@daily",
         default_args=default_args,
         #template_searchpath=[f"{os.environ['AIRFLOW_PATH']}"],
         catchup=False) as dag:

    transform_data = PythonOperator(
        task_id = "transform_data",
        python_callable = transform_data
    )
    is_today = BranchPythonOperator(
        task_id = 'is_today',
        python_callable= is_today,
        provide_context = True
    )
    friday_Task = PythonOperator(
        task_id = 'friday_Task',
        python_callable= friday_Task,
        
    )
    none = DummyOperator(
        task_id = 'none'
    )
    httpgettry = SimpleHttpOperator(
        task_id='httpgettry',
        method='GET',
        http_conn_id='http_post',
        endpoint='Users/',
        #endpoint='post',
        data={
            'user_id':'amey_sonje'
        },
        headers={"Content-Type":"application/json"},
        log_response=True,
        #xcom_push=True,
        #response_check=lambda response: response.json()['json']['blocks_id'] == 'amey_sonje;inv_try_2',
        dag=dag
    )
    htttposttry = SimpleHttpOperator(
        task_id='httpposttry',
        method='POST',
        http_conn_id='http_post',
        endpoint='Users/',
        #endpoint='post',
        data=json.dumps( {
    "user_id": "amey6",
    "password": "amey3",
    "name": "amey2",
    "email_id": "amey2420000@gmail.com"
        }),
        headers={"Content-Type":"application/json"},
        log_response=True,
        #xcom_push=True,
        #response_check=lambda response: response.json()['json']['blocks_id'] == 'amey_sonje;inv_try_2',
        dag=dag
    )

transform_data >> is_today
is_today >> [friday_Task, none]
friday_Task >> [httpgettry, htttposttry]

