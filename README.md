# API

ATTENTION :

DO NOT USE THIS CODE AS ANY TYPE OF PRODUCTION CODE. THIS CODE STORES THE USER'S IP ADDRESS AND TIMESTAMPS, IF TOO MUCH REQUESTS COME,
THE BACKEND SYSTEM MAY CRASH BECAUSE OF THE BUFFER FLOW.
AND ALSO, WHEN YOU WANT TO DEPLOY IT OUTSIDE OF THE LOCALHOST, HIGHLY RECOMMEND USE WSGI.
USING REDIS MAY CAN BE A SOLUTION TO STORE IP ADDRESS AND TIMESTAMPS.

REQUEST TO API:

-by using api_request.py script, you can send the requests to API.


In this code,

Simple API created using python-flask.


API-Endpoints:
/register
/kline_1m
/kline_5m
/force_order


Each user must be registered our database by requesting the /register API endpoint. 
when the users are registered our database, API-key and API-secret-key will automatically generate. Then these API-KEY and API-SECRET-KEYs
will send to users e-mail automatically.

Restrictions:

-Each user must have its own API-KEY and API-SECRET KEY.
-Each user only make one request per minute to get data from API.
-Each user only send registration request two times in a day.
-Maximum value of 1000 for the data_size parameter. Users will be able to fetch data up to a maximum of 1000 records from the respective tables.
-The default data_size parametre 30. it means API will respond with last 30 value from the Postgres.The reuests that having 1000+ datasize
automatically API respond 1000 again. 
