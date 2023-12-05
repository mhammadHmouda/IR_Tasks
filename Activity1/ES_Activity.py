import gzip
import sys
from elasticsearch import Elasticsearch, helpers
from dateutil import parser
import csv, configparser, warnings

warnings.filterwarnings("ignore")

def init_es_conn():
    config = configparser.ConfigParser()
    config.read('config.ini')

    es_host = config['elasticsearch']['host']
    es_username = config['elasticsearch']['username']
    es_password = config['elasticsearch']['password']

    return Elasticsearch(
        [es_host],
        basic_auth=(es_username, es_password),
        verify_certs=False
    )


def create_index(es, index_name):
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
    
    configurations = {
        "settings": {
            "analysis": {
                "filter": {
                    "ngram_filter": {
                        "type": "ngram",
                        "min_gram": 3,
                        "max_gram": 4
                    }
                },
                "analyzer": {
                    "text_processing": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "ngram_filter"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "date": {
                    "type": "date",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "flag": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "id": {
                    "type": "keyword",
                    "ignore_above": 256
                },
                "target": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "text": {
                    "type": "text",
                    "analyzer": "text_processing" 
                },
                "user": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                }
            }
        }
    }
    
    es.indices.create(index=index_name, ignore=400, body=configurations)
    print("Index created!\n")


def create_actions_batch(index_name, file_path, batch_size=10000):
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        actions = []
        
        for i, row in enumerate(csv_reader, start=1):
            try:
                action = {
                    "_op_type": "index",
                    "_index": index_name,
                    "_id": row["id"],
                    "_source": {
                        "target": row["target"],
                        "id": row["id"],
                        "date": parser.parse(row["date"]),
                        "flag": row["flag"],
                        "user": row["user"],
                        "text": row["text"]
                    }
                }
                
                actions.append(action)

                if i % batch_size == 0:
                    yield actions
                    actions = []

            except Exception as e:
                print(f"Error processing row {i}: {e}")

        if actions:
            yield actions

def load_tweets_to_index(es, index_name, file_path):
    x = 0
    for batch in create_actions_batch(index_name, file_path):
        try:
            helpers.bulk(es, batch)
            print(f"Successfully loaded ({len(batch)}) tweets to index!")

            x += len(batch)
            if(x >= 240000):
                print("\nExceed the maximium size\n")
                break
            
        except Exception as e:
            print(f"Error while indexing batch: {e}")


# Create query to get users between (15:00:00 and 16:00:00 time In 2009-04-18 date) and with (text match sad word) and limit the size to 5 elements
def create_query(es, index_name):

    query = {
    "query": {
        "bool": {
            "must": [
                {
                "range": {
                    "date": {
                    "gte": "2009-04-18T15:00:00",
                    "lte": "2009-04-18T16:00:00"
                    }}
                },
                {
                "match": {
                    "text": "sad"
                }}
            ] }
        },
        "size": 5
    }

    results = es.search(index=index_name, body=query)

    for hit in results["hits"]["hits"]:
        print(hit["_source"]["user"])

def main():

    index_name = "tweets"

    # Initialize elastic search connection
    es = init_es_conn()
    
    # (Program accept csv file path from system argument)
    file_path = sys.argv[1] # "d:\\docs-tfidf\\tweets_ds.csv"

    # # Create index with the some configuration
    # create_index(es, index_name)

    # # Load the tweets csv file to the index created
    # load_tweets_to_index(es, index_name, file_path)

    # Create query to filter tweets between (15:00:00 and 16:00:00 time In 2009-04-18 date) and with (text match sad word)
    create_query(es, index_name)


if __name__ == "__main__":
    main()