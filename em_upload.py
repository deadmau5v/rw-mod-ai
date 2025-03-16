from pymilvus import connections, Collection, DataType, FieldSchema, CollectionSchema
import json
from sentence_transformers import SentenceTransformer

import config
from db import get_mods_info
from module import ModsInfo

# Connect to Zilliz
connections.connect(
    uri=config.zilliz_endpoint,
    token=config.zilliz_token
)

collection_name = "rw"
collection = Collection(collection_name)

# Vectorize Module
model = SentenceTransformer('all-MiniLM-L6-v2')


markdown_dir = "./data/markdown"
entities = []

mods: list[ModsInfo] = get_mods_info()
for mod in mods:

    metadata = mod.to_meta_data()

    english_content = mod.content or ""
    chinese_content = mod.content_cn or ""

    vector = model.encode(english_content + chinese_content).tolist()

    if len(vector) < 1536:
        vector.extend([0] * (1536 - len(vector)))
    elif len(vector) > 1536:
        vector = vector[:1536]

    entity = {
        "id": None,
        "vector": vector,
        "content": english_content + chinese_content,
        "metadata": json.dumps(metadata)
    }
    entities.append(entity)

# insert
collection.insert(entities)
collection.flush()
