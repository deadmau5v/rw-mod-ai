import json

new_datas = []

with open("data/train.jsonl", "r", encoding="utf-8") as f:
    for line in f.readlines():
        try:
            data = json.loads(line)
            new_data = {
                "messages": [
                    {
                        "role": "system",
                        "content": data["messages"][0]["content"]
                    },
                    {
                        "role": "user",
                        "content": data["messages"][2]["content"]
                    },
                    {
                        "role": "assistant",
                        "content": data["messages"][1]["content"]
                    }
                ]
            }
            new_datas.append(new_data)
        except Exception as e:
            print(e)

with open("data/train_new.jsonl", "w", encoding="utf-8") as f:
    for new_data in new_datas:
        f.write(json.dumps(new_data, ensure_ascii=False) + "\n")
