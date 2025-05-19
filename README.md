THIS PROJECT STILL NEEDS SOME FINAL TOTCH , BUT IT S WORKING 

-------------------------------------------------------------
FIRST: you need to download my Fakenewsclassifier model from kaggle : https://www.kaggle.com/models/lambarkiaymane/fakenewsclassifier

--->Then put the folder 'final_model' in airflow/scripts/

--->Then just build and run the docker-compose
(localHost port 8081:8080 to check the airflow web services)
--------------------------------------------------------------

WARNNING : you need to create your own dashboard in grafana at port "3000:3000"
and install the plugging for Cassandra
