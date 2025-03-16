import json

from pymilvus import connections, Collection, DataType, FieldSchema, CollectionSchema
from sentence_transformers import SentenceTransformer

import config

# Connect to Zilliz
connections.connect(
    uri=config.zilliz_endpoint,
    token=config.zilliz_token
)

collection_name = "rw"
collection = Collection(collection_name)

# Vectorize Module
model = SentenceTransformer('all-MiniLM-L6-v2')


def search_with_natural_language(query, top_k=5):
    query_vector = model.encode(query).tolist()
    # all-minilm-l6-v2 的向量维度为 1536
    if len(query_vector) < 1536:
        query_vector.extend([0] * (1536 - len(query_vector))) 
    elif len(query_vector) > 1536:
        query_vector = query_vector[:1536] 

    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }

    results = collection.search(
        data=[query_vector],
        anns_field="vector",
        param=search_params,
        limit=top_k,
        output_fields=["content", "metadata"]
    )

    hits = results[0]
    search_results = []
    for hit in hits:
        item = {
            "distance": hit.distance,
            "content": hit.entity.get("content"),
            "metadata": json.loads(hit.entity.get("metadata"))
        }
        search_results.append(item)

    return search_results


if __name__ == '__main__':
    query = "我要玩僵尸mod"
    results = search_with_natural_language(query)

    for result in results:
        print(f"Distance: {result['distance']}")
        print(f"Content: {result['content']}")
        print(f"Metadata: {result['metadata']}")
        print("---")
